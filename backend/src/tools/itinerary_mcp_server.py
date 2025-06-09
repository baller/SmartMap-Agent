#!/usr/bin/env python3
"""
Itinerary Planning MCP Server
提供行程规划和优化功能
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from mcp.server.models import InitializeResult
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource
)
import mcp.types as types
from pydantic import AnyUrl
import mcp.server.stdio

from dotenv import load_dotenv

load_dotenv()

server = Server("itinerary-server")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """列出可用的行程规划工具"""
    return [
        types.Tool(
            name="plan_itinerary",
            description="根据景点列表和约束条件规划最优行程",
            inputSchema={
                "type": "object",
                "properties": {
                    "destinations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "景点名称"},
                                "address": {"type": "string", "description": "景点地址"},
                                "type": {"type": "string", "description": "景点类型"},
                                "duration": {"type": "integer", "description": "建议游玩时长（分钟）"},
                                "opening_hours": {"type": "string", "description": "开放时间"},
                                "priority": {"type": "integer", "description": "优先级 1-5，5最高"},
                                "location": {
                                    "type": "object",
                                    "properties": {
                                        "lat": {"type": "number"},
                                        "lng": {"type": "number"}
                                    }
                                }
                            },
                            "required": ["name", "duration", "priority"]
                        },
                        "description": "目的地列表"
                    },
                    "travel_days": {
                        "type": "integer",
                        "description": "旅行天数",
                        "minimum": 1,
                        "maximum": 30
                    },
                    "start_date": {
                        "type": "string",
                        "description": "开始日期 YYYY-MM-DD 格式"
                    },
                    "daily_start_time": {
                        "type": "string", 
                        "description": "每日开始时间 HH:MM 格式",
                        "default": "09:00"
                    },
                    "daily_end_time": {
                        "type": "string",
                        "description": "每日结束时间 HH:MM 格式", 
                        "default": "18:00"
                    },
                    "transportation": {
                        "type": "string",
                        "description": "主要交通方式: walking, driving, transit",
                        "default": "driving"
                    },
                    "preferences": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "旅行偏好，如 ['文化古迹', '美食', '自然风光']",
                        "default": []
                    }
                },
                "required": ["destinations", "travel_days", "start_date"]
            }
        ),
        types.Tool(
            name="optimize_route",
            description="优化单日游览路线以减少旅行时间",
            inputSchema={
                "type": "object",
                "properties": {
                    "locations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "address": {"type": "string"},
                                "location": {
                                    "type": "object",
                                    "properties": {
                                        "lat": {"type": "number"},
                                        "lng": {"type": "number"}
                                    }
                                },
                                "visit_duration": {"type": "integer", "description": "游玩时长（分钟）"}
                            },
                            "required": ["name", "visit_duration"]
                        },
                        "description": "要访问的地点列表"
                    },
                    "start_location": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "address": {"type": "string"},
                            "location": {
                                "type": "object", 
                                "properties": {
                                    "lat": {"type": "number"},
                                    "lng": {"type": "number"}
                                }
                            }
                        },
                        "description": "起始位置（如酒店）"
                    },
                    "transportation": {
                        "type": "string",
                        "description": "交通方式: walking, driving, transit",
                        "default": "driving"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "开始时间 HH:MM",
                        "default": "09:00"
                    }
                },
                "required": ["locations"]
            }
        ),
        types.Tool(
            name="suggest_activities",
            description="根据时间、天气、位置推荐活动",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "位置或城市名称"
                    },
                    "date": {
                        "type": "string",
                        "description": "日期 YYYY-MM-DD"
                    },
                    "time_slot": {
                        "type": "string",
                        "description": "时间段: morning, afternoon, evening, night",
                        "default": "morning"
                    },
                    "weather": {
                        "type": "string",
                        "description": "天气状况"
                    },
                    "interests": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "兴趣爱好",
                        "default": []
                    },
                    "budget": {
                        "type": "string",
                        "description": "预算范围: low, medium, high",
                        "default": "medium"
                    }
                },
                "required": ["location", "date"]
            }
        ),
        types.Tool(
            name="calculate_budget",
            description="计算行程预算估算",
            inputSchema={
                "type": "object",
                "properties": {
                    "itinerary": {
                        "type": "object",
                        "description": "完整行程数据"
                    },
                    "travelers": {
                        "type": "integer",
                        "description": "旅行人数",
                        "default": 1
                    },
                    "accommodation_level": {
                        "type": "string",
                        "description": "住宿标准: budget, mid-range, luxury",
                        "default": "mid-range"
                    },
                    "dining_level": {
                        "type": "string",
                        "description": "餐饮标准: budget, mid-range, luxury", 
                        "default": "mid-range"
                    }
                },
                "required": ["itinerary"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """处理工具调用"""
    try:
        if name == "plan_itinerary":
            return await plan_itinerary(arguments)
        elif name == "optimize_route":
            return await optimize_route(arguments)
        elif name == "suggest_activities":
            return await suggest_activities(arguments)
        elif name == "calculate_budget":
            return await calculate_budget(arguments)
        else:
            return [types.TextContent(
                type="text",
                text=f"未知工具: {name}"
            )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"行程规划工具调用出错: {str(e)}"
        )]


async def plan_itinerary(args: dict) -> list[types.TextContent]:
    """规划多日行程"""
    destinations = args["destinations"]
    travel_days = args["travel_days"]
    start_date = datetime.strptime(args["start_date"], "%Y-%m-%d")
    daily_start_time = args.get("daily_start_time", "09:00")
    daily_end_time = args.get("daily_end_time", "18:00")
    transportation = args.get("transportation", "driving")
    preferences = args.get("preferences", [])
    
    # 按优先级和类型对景点分组
    sorted_destinations = sorted(destinations, key=lambda x: x.get("priority", 3), reverse=True)
    
    # 计算每天可用时间（分钟）
    start_hour, start_min = map(int, daily_start_time.split(':'))
    end_hour, end_min = map(int, daily_end_time.split(':'))
    daily_available_minutes = (end_hour * 60 + end_min) - (start_hour * 60 + start_min)
    
    # 为每天分配景点
    daily_plans = []
    remaining_destinations = sorted_destinations.copy()
    
    for day in range(travel_days):
        current_date = start_date + timedelta(days=day)
        day_plan = {
            "date": current_date.strftime("%Y-%m-%d"),
            "day_of_week": current_date.strftime("%A"),
            "day_number": day + 1,
            "activities": [],
            "total_duration": 0,
            "travel_time": 0,
            "start_time": daily_start_time,
            "end_time": daily_end_time
        }
        
        # 为当天选择景点
        daily_time_used = 0
        daily_activities = []
        
        # 优先选择高优先级且适合时间的景点
        for dest in remaining_destinations.copy():
            duration = dest.get("duration", 120)  # 默认2小时
            
            # 检查是否还有足够时间
            if daily_time_used + duration <= daily_available_minutes * 0.8:  # 留20%缓冲时间
                activity = {
                    "name": dest["name"],
                    "address": dest.get("address", ""),
                    "type": dest.get("type", "景点"),
                    "duration": duration,
                    "priority": dest.get("priority", 3),
                    "start_time": calculate_time_from_minutes(daily_start_time, daily_time_used),
                    "end_time": calculate_time_from_minutes(daily_start_time, daily_time_used + duration),
                    "location": dest.get("location", {}),
                    "opening_hours": dest.get("opening_hours", ""),
                    "notes": []
                }
                
                # 添加基于偏好的建议
                if preferences:
                    dest_type = dest.get("type", "").lower()
                    for pref in preferences:
                        if pref.lower() in dest_type or dest_type in pref.lower():
                            activity["notes"].append(f"符合您的 '{pref}' 偏好")
                
                daily_activities.append(activity)
                daily_time_used += duration + 30  # 加30分钟交通/休息时间
                remaining_destinations.remove(dest)
                
                # 如果一天安排得差不多了就停止
                if len(daily_activities) >= 4 or daily_time_used >= daily_available_minutes * 0.7:
                    break
        
        # 如果当天活动较少，添加推荐活动
        if len(daily_activities) < 2:
            if day == 0:
                daily_activities.append({
                    "name": "到达与入住",
                    "type": "交通",
                    "duration": 60,
                    "start_time": daily_start_time,
                    "end_time": calculate_time_from_minutes(daily_start_time, 60),
                    "notes": ["建议预留时间用于到达和办理入住"]
                })
            elif day == travel_days - 1:
                daily_activities.append({
                    "name": "返程准备",
                    "type": "交通",
                    "duration": 60,
                    "start_time": calculate_time_from_minutes(daily_end_time, -60),
                    "end_time": daily_end_time,
                    "notes": ["建议预留时间用于收拾行李和返程"]
                })
        
        # 添加餐饮建议
        if daily_time_used < daily_available_minutes * 0.6:
            lunch_time = calculate_time_from_minutes(daily_start_time, daily_available_minutes // 2)
            daily_activities.append({
                "name": "午餐时间",
                "type": "餐饮",
                "duration": 60,
                "start_time": lunch_time,
                "end_time": calculate_time_from_minutes(lunch_time, 60),
                "notes": ["建议寻找当地特色餐厅"]
            })
        
        day_plan["activities"] = sorted(daily_activities, key=lambda x: x.get("start_time", ""))
        day_plan["total_duration"] = sum(act.get("duration", 0) for act in daily_activities)
        daily_plans.append(day_plan)
    
    # 生成未安排的景点建议
    unscheduled_suggestions = []
    for dest in remaining_destinations:
        unscheduled_suggestions.append({
            "name": dest["name"],
            "reason": "时间限制或优先级较低",
            "suggestion": "可考虑延长行程或作为备选"
        })
    
    # 生成旅行建议
    travel_tips = generate_travel_tips(sorted_destinations, transportation, preferences)
    
    result = {
        "trip_summary": {
            "destination": "多地",
            "total_days": travel_days,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": (start_date + timedelta(days=travel_days-1)).strftime("%Y-%m-%d"),
            "transportation": transportation,
            "planned_activities": sum(len(day["activities"]) for day in daily_plans),
            "total_scheduled_time": sum(day["total_duration"] for day in daily_plans)
        },
        "daily_itinerary": daily_plans,
        "unscheduled_destinations": unscheduled_suggestions,
        "travel_tips": travel_tips,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return [types.TextContent(
        type="text",
        text=json.dumps(result, ensure_ascii=False, indent=2)
    )]


async def optimize_route(args: dict) -> list[types.TextContent]:
    """优化单日路线"""
    locations = args["locations"]
    start_location = args.get("start_location", {})
    transportation = args.get("transportation", "driving")
    start_time = args.get("start_time", "09:00")
    
    if len(locations) <= 1:
        return [types.TextContent(
            type="text",
            text="需要至少2个地点才能进行路线优化"
        )]
    
    # 简化的路线优化（实际项目中可以使用更复杂的算法）
    # 这里使用贪心算法：每次选择离当前位置最近的未访问地点
    
    optimized_route = []
    unvisited = locations.copy()
    current_time = start_time
    current_location = start_location or unvisited[0]
    
    if start_location:
        optimized_route.append({
            "order": 0,
            "name": start_location.get("name", "起始点"),
            "type": "起始点",
            "arrival_time": current_time,
            "departure_time": current_time,
            "duration": 0,
            "location": start_location.get("location", {})
        })
    
    # 如果没有起始位置，从第一个地点开始
    if not start_location and unvisited:
        first_location = unvisited.pop(0)
        optimized_route.append({
            "order": 1,
            "name": first_location["name"],
            "type": first_location.get("type", "景点"),
            "arrival_time": current_time,
            "departure_time": calculate_time_from_minutes(current_time, first_location["visit_duration"]),
            "duration": first_location["visit_duration"],
            "location": first_location.get("location", {}),
            "notes": ["优化路线起点"]
        })
        current_time = calculate_time_from_minutes(current_time, first_location["visit_duration"] + 15)
        current_location = first_location
    
    # 贪心选择最近的下一个地点
    order = len(optimized_route) + 1
    while unvisited:
        # 简单距离计算（实际应使用真实的路线API）
        next_location = min(unvisited, key=lambda loc: calculate_simple_distance(
            current_location.get("location", {}), 
            loc.get("location", {})
        ))
        
        # 估算旅行时间（分钟）
        travel_time = estimate_travel_time(
            current_location.get("location", {}),
            next_location.get("location", {}),
            transportation
        )
        
        arrival_time = calculate_time_from_minutes(current_time, travel_time)
        departure_time = calculate_time_from_minutes(arrival_time, next_location["visit_duration"])
        
        optimized_route.append({
            "order": order,
            "name": next_location["name"],
            "type": next_location.get("type", "景点"),
            "arrival_time": arrival_time,
            "departure_time": departure_time,
            "duration": next_location["visit_duration"],
            "travel_time_from_previous": travel_time,
            "location": next_location.get("location", {}),
            "notes": []
        })
        
        current_time = calculate_time_from_minutes(departure_time, 15)  # 15分钟缓冲
        current_location = next_location
        unvisited.remove(next_location)
        order += 1
    
    # 计算总时间和距离
    total_duration = sum(stop.get("duration", 0) for stop in optimized_route)
    total_travel_time = sum(stop.get("travel_time_from_previous", 0) for stop in optimized_route)
    
    result = {
        "optimization_summary": {
            "total_stops": len(optimized_route),
            "total_visit_time": total_duration,
            "total_travel_time": total_travel_time,
            "total_time": total_duration + total_travel_time,
            "start_time": start_time,
            "estimated_end_time": optimized_route[-1]["departure_time"] if optimized_route else start_time,
            "transportation": transportation
        },
        "optimized_route": optimized_route,
        "route_tips": [
            "路线已按距离优化，减少不必要的往返",
            "建议预留额外时间应对交通状况",
            "可根据实际情况调整各景点的停留时间"
        ],
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return [types.TextContent(
        type="text",
        text=json.dumps(result, ensure_ascii=False, indent=2)
    )]


async def suggest_activities(args: dict) -> list[types.TextContent]:
    """推荐活动"""
    location = args["location"]
    date = args["date"]
    time_slot = args.get("time_slot", "morning")
    weather = args.get("weather", "")
    interests = args.get("interests", [])
    budget = args.get("budget", "medium")
    
    # 基于时间段的活动建议
    time_based_activities = {
        "morning": ["参观博物馆", "登山健行", "市场逛街", "公园散步", "文化古迹游览"],
        "afternoon": ["购物", "咖啡厅休憩", "艺术馆参观", "湖边漫步", "当地美食体验"],
        "evening": ["观景台看夕阳", "夜市逛街", "演出观赏", "酒吧体验", "夜游"],
        "night": ["夜景摄影", "夜市美食", "酒吧", "夜间演出", "温泉"]
    }
    
    # 基于天气的活动建议
    weather_activities = {
        "sunny": ["户外景点", "公园", "海滩", "登山", "骑行"],
        "rainy": ["博物馆", "购物中心", "咖啡厅", "室内娱乐", "温泉"],
        "cloudy": ["城市漫步", "摄影", "文化街区", "古迹参观", "咖啡厅"],
        "cold": ["温泉", "室内景点", "购物", "美食", "温暖咖啡厅"],
        "hot": ["室内景点", "水上活动", "阴凉公园", "空调购物中心", "冷饮店"]
    }
    
    # 基于兴趣的活动建议
    interest_activities = {
        "文化古迹": ["古建筑群", "历史博物馆", "文化街区", "传统工艺体验", "古迹导览"],
        "美食": ["当地特色餐厅", "美食街", "cooking class", "酒庄品酒", "传统市场"],
        "自然风光": ["国家公园", "山景", "湖泊", "海滩", "植物园"],
        "艺术": ["美术馆", "艺术区", "画廊", "艺术工作坊", "创意市集"],
        "购物": ["购物中心", "特色商店", "古玩市场", "设计师店铺", "免税店"],
        "娱乐": ["主题公园", "游乐场", "KTV", "游戏厅", "体验馆"]
    }
    
    # 基于预算的活动分类
    budget_categories = {
        "low": {"max_cost": 100, "activities": ["免费景点", "公园", "海滩", "徒步", "免费博物馆"]},
        "medium": {"max_cost": 300, "activities": ["付费景点", "餐厅", "咖啡厅", "购物", "娱乐"]},
        "high": {"max_cost": 1000, "activities": ["高端餐厅", "奢华体验", "私人导览", "豪华购物", "高端娱乐"]}
    }
    
    # 生成推荐活动
    recommended_activities = []
    
    # 基于时间段推荐
    time_activities = time_based_activities.get(time_slot, [])
    for activity in time_activities[:3]:
        recommended_activities.append({
            "name": f"{location}{activity}",
            "category": "时间推荐",
            "reason": f"适合{time_slot}时段",
            "estimated_duration": "1-3小时",
            "budget_level": budget
        })
    
    # 基于天气推荐
    if weather:
        weather_key = "sunny"  # 默认
        if "雨" in weather or "rain" in weather.lower():
            weather_key = "rainy"
        elif "云" in weather or "cloud" in weather.lower():
            weather_key = "cloudy"
        elif "冷" in weather or "cold" in weather.lower():
            weather_key = "cold"
        elif "热" in weather or "hot" in weather.lower():
            weather_key = "hot"
        
        weather_activities_list = weather_activities.get(weather_key, [])
        for activity in weather_activities_list[:2]:
            recommended_activities.append({
                "name": f"{location}{activity}",
                "category": "天气推荐",
                "reason": f"适合{weather}天气",
                "estimated_duration": "1-4小时",
                "budget_level": budget
            })
    
    # 基于兴趣推荐
    for interest in interests:
        if interest in interest_activities:
            interest_activity_list = interest_activities[interest]
            for activity in interest_activity_list[:2]:
                recommended_activities.append({
                    "name": f"{location}{activity}",
                    "category": "兴趣推荐",
                    "reason": f"符合您的{interest}兴趣",
                    "estimated_duration": "2-4小时",
                    "budget_level": budget
                })
    
    # 去重和限制数量
    unique_activities = []
    seen_names = set()
    for activity in recommended_activities:
        if activity["name"] not in seen_names:
            unique_activities.append(activity)
            seen_names.add(activity["name"])
        if len(unique_activities) >= 8:
            break
    
    result = {
        "location": location,
        "date": date,
        "time_slot": time_slot,
        "weather_condition": weather,
        "interests": interests,
        "budget_level": budget,
        "recommended_activities": unique_activities,
        "general_tips": [
            "建议提前查询各景点的开放时间",
            "根据天气状况携带合适的装备",
            "可以提前预订热门景点的门票",
            "留意当地的文化习俗和礼仪"
        ],
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return [types.TextContent(
        type="text",
        text=json.dumps(result, ensure_ascii=False, indent=2)
    )]


async def calculate_budget(args: dict) -> list[types.TextContent]:
    """计算预算估算"""
    itinerary = args["itinerary"]
    travelers = args.get("travelers", 1)
    accommodation_level = args.get("accommodation_level", "mid-range")
    dining_level = args.get("dining_level", "mid-range")
    
    # 预算标准（人民币/天）
    accommodation_costs = {
        "budget": 150,
        "mid-range": 400,
        "luxury": 1000
    }
    
    dining_costs = {
        "budget": 100,
        "mid-range": 250,
        "luxury": 600
    }
    
    # 景点门票估算
    activity_costs = {
        "景点": 50,
        "博物馆": 30,
        "公园": 20,
        "餐饮": 0,  # 已在dining中计算
        "交通": 0,  # 单独计算
        "娱乐": 100,
        "购物": 200,
        "温泉": 150
    }
    
    # 交通费用估算
    transportation_daily_costs = {
        "walking": 20,  # 偶尔的公交费用
        "driving": 200,  # 租车+油费+停车
        "transit": 50   # 公交/地铁
    }
    
    daily_plans = itinerary.get("daily_itinerary", [])
    trip_summary = itinerary.get("trip_summary", {})
    
    total_days = len(daily_plans)
    if total_days == 0:
        return [types.TextContent(
            type="text",
            text="无效的行程数据"
        )]
    
    # 计算各项费用
    accommodation_total = accommodation_costs[accommodation_level] * total_days * travelers
    dining_total = dining_costs[dining_level] * total_days * travelers
    
    # 计算活动费用
    activity_total = 0
    for day in daily_plans:
        for activity in day.get("activities", []):
            activity_type = activity.get("type", "景点")
            cost = activity_costs.get(activity_type, 50)
            activity_total += cost * travelers
    
    # 计算交通费用
    transportation_mode = trip_summary.get("transportation", "driving")
    transportation_total = transportation_daily_costs[transportation_mode] * total_days
    
    # 其他费用（购物、紧急等）
    miscellaneous = (accommodation_total + dining_total + activity_total) * 0.2
    
    # 总预算
    subtotal = accommodation_total + dining_total + activity_total + transportation_total
    total_budget = subtotal + miscellaneous
    
    # 生成预算明细
    budget_breakdown = {
        "trip_overview": {
            "destination": trip_summary.get("destination", ""),
            "total_days": total_days,
            "travelers": travelers,
            "accommodation_level": accommodation_level,
            "dining_level": dining_level
        },
        "cost_breakdown": {
            "accommodation": {
                "total": accommodation_total,
                "per_day": accommodation_costs[accommodation_level],
                "description": f"{accommodation_level}级住宿 × {total_days}天 × {travelers}人"
            },
            "dining": {
                "total": dining_total,
                "per_day": dining_costs[dining_level] * travelers,
                "description": f"{dining_level}级餐饮 × {total_days}天 × {travelers}人"
            },
            "activities": {
                "total": activity_total,
                "per_person": activity_total / travelers if travelers > 0 else 0,
                "description": f"景点门票和活动费用"
            },
            "transportation": {
                "total": transportation_total,
                "per_day": transportation_daily_costs[transportation_mode],
                "description": f"{transportation_mode}方式的交通费用"
            },
            "miscellaneous": {
                "total": miscellaneous,
                "percentage": 20,
                "description": "购物、紧急费用等（约20%）"
            }
        },
        "budget_summary": {
            "subtotal": subtotal,
            "total_budget": total_budget,
            "per_person": total_budget / travelers if travelers > 0 else 0,
            "per_day": total_budget / total_days if total_days > 0 else 0,
            "currency": "CNY"
        },
        "budget_tips": [
            "预算为估算值，实际费用可能有差异",
            "建议预留10-20%的额外预算应对突发情况",
            "淡旺季价格差异较大，请根据实际情况调整",
            "可以通过调整住宿和餐饮标准来控制预算",
            "提前预订通常可以获得更好的价格"
        ],
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return [types.TextContent(
        type="text",
        text=json.dumps(budget_breakdown, ensure_ascii=False, indent=2)
    )]


# 辅助函数
def calculate_time_from_minutes(start_time: str, minutes: int) -> str:
    """从开始时间计算经过指定分钟后的时间"""
    try:
        if isinstance(start_time, str):
            start_hour, start_min = map(int, start_time.split(':'))
        else:
            return start_time
        
        total_minutes = start_hour * 60 + start_min + minutes
        new_hour = (total_minutes // 60) % 24
        new_min = total_minutes % 60
        return f"{new_hour:02d}:{new_min:02d}"
    except:
        return start_time


def calculate_simple_distance(loc1: dict, loc2: dict) -> float:
    """计算两点间的简单距离（欧几里得距离）"""
    if not loc1 or not loc2:
        return 1.0  # 默认距离
    
    lat1 = loc1.get("lat", 0)
    lng1 = loc1.get("lng", 0)
    lat2 = loc2.get("lat", 0)
    lng2 = loc2.get("lng", 0)
    
    return ((lat1 - lat2) ** 2 + (lng1 - lng2) ** 2) ** 0.5


def estimate_travel_time(loc1: dict, loc2: dict, transportation: str) -> int:
    """估算两点间的旅行时间（分钟）"""
    distance = calculate_simple_distance(loc1, loc2)
    
    # 简化的时间估算（实际应使用真实路线API）
    speed_factors = {
        "walking": 300,  # 很慢
        "driving": 30,   # 中等
        "transit": 60    # 较慢
    }
    
    factor = speed_factors.get(transportation, 60)
    estimated_time = max(int(distance * factor), 15)  # 最少15分钟
    return min(estimated_time, 120)  # 最多2小时


def generate_travel_tips(destinations: list, transportation: str, preferences: list) -> list:
    """生成旅行建议"""
    tips = []
    
    # 基于目的地数量的建议
    if len(destinations) > 10:
        tips.append("行程安排较为紧凑，建议合理安排休息时间")
    
    # 基于交通方式的建议
    transport_tips = {
        "walking": "建议穿着舒适的步行鞋，携带充足的水",
        "driving": "建议提前了解停车情况和交通规则",
        "transit": "建议办理当地交通卡，了解公交时刻表"
    }
    if transportation in transport_tips:
        tips.append(transport_tips[transportation])
    
    # 基于偏好的建议
    preference_tips = {
        "文化古迹": "建议了解景点历史背景，可考虑聘请导游",
        "美食": "建议提前了解当地特色菜品，预留充足的用餐时间",
        "自然风光": "建议关注天气状况，携带相应的户外装备"
    }
    for pref in preferences:
        if pref in preference_tips:
            tips.append(preference_tips[pref])
    
    # 通用建议
    tips.extend([
        "建议购买旅行保险，确保行程安全",
        "保持手机电量充足，下载离线地图",
        "尊重当地文化和习俗"
    ])
    
    return tips


async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializeResult(
                protocolVersion="2024-11-05",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main()) 