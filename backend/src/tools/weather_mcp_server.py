#!/usr/bin/env python3
"""
Weather MCP Server
提供天气查询功能
"""

import asyncio
import json
import os
import requests
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource
)
import mcp.types as types
from pydantic import AnyUrl
import mcp.server.stdio

from dotenv import load_dotenv

load_dotenv()

# Weather API configuration
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5"

server = Server("weather-server")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """列出可用的天气工具"""
    return [
        types.Tool(
            name="get_current_weather",
            description="获取指定城市的当前天气信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'杭州'或'Hangzhou,CN'"
                    },
                    "units": {
                        "type": "string",
                        "description": "温度单位：metric(摄氏度), imperial(华氏度), kelvin",
                        "default": "metric"
                    },
                    "lang": {
                        "type": "string", 
                        "description": "语言：zh_cn(中文), en(英文)",
                        "default": "zh_cn"
                    }
                },
                "required": ["city"]
            }
        ),
        types.Tool(
            name="get_weather_forecast",
            description="获取指定城市的5天天气预报",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'杭州'或'Hangzhou,CN'"
                    },
                    "days": {
                        "type": "integer",
                        "description": "预报天数（1-5天）",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 5
                    },
                    "units": {
                        "type": "string",
                        "description": "温度单位：metric(摄氏度), imperial(华氏度), kelvin",
                        "default": "metric"
                    },
                    "lang": {
                        "type": "string",
                        "description": "语言：zh_cn(中文), en(英文)",
                        "default": "zh_cn"
                    }
                },
                "required": ["city"]
            }
        ),
        types.Tool(
            name="get_weather_alerts",
            description="获取指定城市的天气预警信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'杭州'或'Hangzhou,CN'"
                    },
                    "lang": {
                        "type": "string",
                        "description": "语言：zh_cn(中文), en(英文)",
                        "default": "zh_cn"
                    }
                },
                "required": ["city"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """处理工具调用"""
    if not WEATHER_API_KEY:
        return [types.TextContent(
            type="text",
            text="错误：未配置天气 API Key。请设置 WEATHER_API_KEY 环境变量。\n" +
                 "您可以在 https://openweathermap.org/api 免费获取 API Key。"
        )]
    
    try:
        if name == "get_current_weather":
            return await get_current_weather(arguments)
        elif name == "get_weather_forecast":
            return await get_weather_forecast(arguments)
        elif name == "get_weather_alerts":
            return await get_weather_alerts(arguments)
        else:
            return [types.TextContent(
                type="text",
                text=f"未知工具: {name}"
            )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"天气工具调用出错: {str(e)}"
        )]


async def get_current_weather(args: dict) -> list[types.TextContent]:
    """获取当前天气"""
    city = args["city"]
    units = args.get("units", "metric")
    lang = args.get("lang", "zh_cn")
    
    url = f"{WEATHER_API_URL}/weather"
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": units,
        "lang": lang
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 解析天气数据
        weather_info = {
            "city": data["name"],
            "country": data["sys"]["country"],
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "weather": {
                "main": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"]
            },
            "temperature": {
                "current": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "min": data["main"]["temp_min"],
                "max": data["main"]["temp_max"],
                "unit": "°C" if units == "metric" else "°F" if units == "imperial" else "K"
            },
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "visibility": data.get("visibility", 0) / 1000,  # 转换为公里
            "wind": {
                "speed": data["wind"]["speed"],
                "direction": data["wind"].get("deg", 0)
            },
            "clouds": data["clouds"]["all"],
            "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%H:%M:%S"),
            "sunset": datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%H:%M:%S")
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(weather_info, ensure_ascii=False, indent=2)
        )]
        
    except requests.exceptions.RequestException as e:
        return [types.TextContent(
            type="text",
            text=f"获取天气数据失败: {str(e)}"
        )]
    except KeyError as e:
        return [types.TextContent(
            type="text",
            text=f"解析天气数据失败，缺少字段: {str(e)}"
        )]


async def get_weather_forecast(args: dict) -> list[types.TextContent]:
    """获取天气预报"""
    city = args["city"]
    days = args.get("days", 5)
    units = args.get("units", "metric")
    lang = args.get("lang", "zh_cn")
    
    url = f"{WEATHER_API_URL}/forecast"
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": units,
        "lang": lang,
        "cnt": days * 8  # 每天8个时间点（3小时间隔）
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 按天分组预报数据
        daily_forecasts = {}
        unit_symbol = "°C" if units == "metric" else "°F" if units == "imperial" else "K"
        
        for item in data["list"]:
            date = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")
            time = datetime.fromtimestamp(item["dt"]).strftime("%H:%M")
            
            if date not in daily_forecasts:
                daily_forecasts[date] = {
                    "date": date,
                    "forecasts": [],
                    "temp_min": float('inf'),
                    "temp_max": float('-inf'),
                    "weather_summary": {}
                }
            
            forecast = {
                "time": time,
                "temperature": item["main"]["temp"],
                "feels_like": item["main"]["feels_like"],
                "weather": item["weather"][0]["description"],
                "humidity": item["main"]["humidity"],
                "wind_speed": item["wind"]["speed"],
                "precipitation": item.get("rain", {}).get("3h", 0) + item.get("snow", {}).get("3h", 0)
            }
            
            daily_forecasts[date]["forecasts"].append(forecast)
            daily_forecasts[date]["temp_min"] = min(daily_forecasts[date]["temp_min"], item["main"]["temp_min"])
            daily_forecasts[date]["temp_max"] = max(daily_forecasts[date]["temp_max"], item["main"]["temp_max"])
            
            # 统计主要天气
            weather_desc = item["weather"][0]["description"]
            daily_forecasts[date]["weather_summary"][weather_desc] = daily_forecasts[date]["weather_summary"].get(weather_desc, 0) + 1
        
        # 整理每日摘要
        forecast_summary = {
            "city": data["city"]["name"],
            "country": data["city"]["country"],
            "forecast_days": len(daily_forecasts),
            "unit": unit_symbol,
            "daily_forecasts": []
        }
        
        for date, day_data in list(daily_forecasts.items())[:days]:
            # 获取主要天气
            main_weather = max(day_data["weather_summary"].items(), key=lambda x: x[1])[0]
            
            daily_summary = {
                "date": date,
                "day_of_week": datetime.strptime(date, "%Y-%m-%d").strftime("%A"),
                "temperature": {
                    "min": day_data["temp_min"],
                    "max": day_data["temp_max"],
                    "unit": unit_symbol
                },
                "main_weather": main_weather,
                "forecasts": day_data["forecasts"][:4]  # 只显示前4个时间点
            }
            forecast_summary["daily_forecasts"].append(daily_summary)
        
        return [types.TextContent(
            type="text",
            text=json.dumps(forecast_summary, ensure_ascii=False, indent=2)
        )]
        
    except requests.exceptions.RequestException as e:
        return [types.TextContent(
            type="text",
            text=f"获取天气预报失败: {str(e)}"
        )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"处理天气预报数据失败: {str(e)}"
        )]


async def get_weather_alerts(args: dict) -> list[types.TextContent]:
    """获取天气预警（简化版本，实际需要更高级的API）"""
    city = args["city"]
    lang = args.get("lang", "zh_cn")
    
    # 由于免费版 OpenWeatherMap API 不包含预警信息，我们提供一个简化的实现
    # 实际项目中可以使用更高级的天气服务
    
    # 先获取当前天气，根据条件给出建议
    try:
        current_weather = await get_current_weather({"city": city, "lang": lang})
        weather_data = json.loads(current_weather[0].text)
        
        alerts = []
        
        # 基于天气条件生成简单的提醒
        humidity = weather_data["humidity"]
        wind_speed = weather_data["wind"]["speed"]
        description = weather_data["weather"]["description"].lower()
        
        if humidity > 80:
            alerts.append({
                "type": "高湿度提醒",
                "level": "注意",
                "message": f"当前湿度{humidity}%，较为潮湿，注意防潮"
            })
        
        if wind_speed > 10:
            alerts.append({
                "type": "大风提醒", 
                "level": "注意",
                "message": f"当前风速{wind_speed}m/s，外出注意安全"
            })
        
        if any(keyword in description for keyword in ["rain", "雨", "snow", "雪"]):
            alerts.append({
                "type": "降水提醒",
                "level": "提醒",
                "message": "预计有降水，出行请携带雨具"
            })
        
        if not alerts:
            alerts.append({
                "type": "天气正常",
                "level": "信息",
                "message": "当前天气状况良好，适合出行"
            })
        
        alert_info = {
            "city": weather_data["city"],
            "check_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "alerts_count": len(alerts),
            "alerts": alerts,
            "note": "此为基础天气提醒，如需专业天气预警请参考当地气象部门"
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(alert_info, ensure_ascii=False, indent=2)
        )]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"获取天气提醒失败: {str(e)}"
        )]


async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main()) 