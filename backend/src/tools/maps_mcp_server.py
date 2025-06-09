#!/usr/bin/env python3
"""
Google Maps MCP Server
提供地图搜索、地点详情、路线规划等功能
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
import googlemaps
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

# Google Maps client
gmaps = None
if os.environ.get("GOOGLE_MAPS_API_KEY"):
    gmaps = googlemaps.Client(key=os.environ["GOOGLE_MAPS_API_KEY"])

server = Server("maps-server")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """列出可用的地图工具"""
    return [
        types.Tool(
            name="search_places",
            description="搜索指定地区的地点（景点、餐厅、酒店等）",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词，如'杭州西湖附近的餐厅'"
                    },
                    "location": {
                        "type": "string", 
                        "description": "搜索中心位置，如'杭州市'"
                    },
                    "radius": {
                        "type": "integer",
                        "description": "搜索半径（米），默认5000",
                        "default": 5000
                    },
                    "place_type": {
                        "type": "string",
                        "description": "地点类型：tourist_attraction, restaurant, lodging, etc.",
                        "default": ""
                    }
                },
                "required": ["query", "location"]
            }
        ),
        types.Tool(
            name="get_place_details",
            description="获取特定地点的详细信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "place_id": {
                        "type": "string",
                        "description": "Google Places API 的地点ID"
                    },
                    "place_name": {
                        "type": "string", 
                        "description": "地点名称（如果没有place_id）"
                    },
                    "location": {
                        "type": "string",
                        "description": "地点所在城市（配合place_name使用）"
                    }
                },
                "anyOf": [
                    {"required": ["place_id"]},
                    {"required": ["place_name", "location"]}
                ]
            }
        ),
        types.Tool(
            name="get_directions",
            description="获取两点间的路线规划",
            inputSchema={
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "起点地址或地点名称"
                    },
                    "destination": {
                        "type": "string",
                        "description": "终点地址或地点名称"  
                    },
                    "mode": {
                        "type": "string",
                        "description": "交通方式：driving, walking, transit, bicycling",
                        "default": "driving"
                    },
                    "waypoints": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "途经点列表",
                        "default": []
                    }
                },
                "required": ["origin", "destination"]
            }
        ),
        types.Tool(
            name="get_distance_matrix",
            description="计算多个起点到多个终点的距离和时间",
            inputSchema={
                "type": "object", 
                "properties": {
                    "origins": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "起点列表"
                    },
                    "destinations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "终点列表"
                    },
                    "mode": {
                        "type": "string",
                        "description": "交通方式：driving, walking, transit, bicycling",
                        "default": "driving"
                    }
                },
                "required": ["origins", "destinations"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """处理工具调用"""
    if not gmaps:
        return [types.TextContent(
            type="text",
            text="错误：未配置 Google Maps API Key。请设置 GOOGLE_MAPS_API_KEY 环境变量。"
        )]
    
    try:
        if name == "search_places":
            return await search_places(arguments)
        elif name == "get_place_details":
            return await get_place_details(arguments)
        elif name == "get_directions":
            return await get_directions(arguments)
        elif name == "get_distance_matrix":
            return await get_distance_matrix(arguments)
        else:
            return [types.TextContent(
                type="text",
                text=f"未知工具: {name}"
            )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"工具调用出错: {str(e)}"
        )]


async def search_places(args: dict) -> list[types.TextContent]:
    """搜索地点"""
    query = args["query"]
    location = args["location"]
    radius = args.get("radius", 5000)
    place_type = args.get("place_type", "")
    
    # 首先搜索地点
    places_result = gmaps.places(
        query=query,
        location=location,
        radius=radius,
        type=place_type if place_type else None
    )
    
    results = []
    if places_result["status"] == "OK":
        for place in places_result["results"][:10]:  # 限制返回10个结果
            place_info = {
                "name": place.get("name", ""),
                "address": place.get("formatted_address", ""),
                "rating": place.get("rating", 0),
                "price_level": place.get("price_level", "未知"),
                "types": place.get("types", []),
                "place_id": place.get("place_id", ""),
                "location": place.get("geometry", {}).get("location", {}),
                "business_status": place.get("business_status", "")
            }
            results.append(place_info)
    
    return [types.TextContent(
        type="text",
        text=json.dumps({
            "query": query,
            "location": location,
            "results_count": len(results),
            "places": results
        }, ensure_ascii=False, indent=2)
    )]


async def get_place_details(args: dict) -> list[types.TextContent]:
    """获取地点详情"""
    place_id = args.get("place_id")
    place_name = args.get("place_name")
    location = args.get("location")
    
    if place_id:
        # 使用 place_id 获取详情
        place_details = gmaps.place(place_id=place_id)
    elif place_name and location:
        # 先搜索地点获取 place_id
        search_result = gmaps.places(query=f"{place_name} {location}")
        if search_result["status"] == "OK" and search_result["results"]:
            place_id = search_result["results"][0]["place_id"]
            place_details = gmaps.place(place_id=place_id)
        else:
            return [types.TextContent(
                type="text",
                text=f"未找到地点: {place_name} 在 {location}"
            )]
    else:
        return [types.TextContent(
            type="text",
            text="需要提供 place_id 或者 place_name + location"
        )]
    
    if place_details["status"] == "OK":
        result = place_details["result"]
        details = {
            "name": result.get("name", ""),
            "address": result.get("formatted_address", ""),
            "phone": result.get("formatted_phone_number", ""),
            "website": result.get("website", ""),
            "rating": result.get("rating", 0),
            "user_ratings_total": result.get("user_ratings_total", 0),
            "price_level": result.get("price_level", "未知"),
            "opening_hours": result.get("opening_hours", {}).get("weekday_text", []),
            "types": result.get("types", []),
            "reviews": [
                {
                    "author_name": review.get("author_name", ""),
                    "rating": review.get("rating", 0),
                    "text": review.get("text", ""),
                    "time": review.get("time", 0)
                }
                for review in result.get("reviews", [])[:3]  # 只取前3个评论
            ],
            "location": result.get("geometry", {}).get("location", {}),
            "photos": len(result.get("photos", []))
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(details, ensure_ascii=False, indent=2)
        )]
    else:
        return [types.TextContent(
            type="text",
            text=f"获取地点详情失败: {place_details['status']}"
        )]


async def get_directions(args: dict) -> list[types.TextContent]:
    """获取路线规划"""
    origin = args["origin"]
    destination = args["destination"]
    mode = args.get("mode", "driving")
    waypoints = args.get("waypoints", [])
    
    directions = gmaps.directions(
        origin=origin,
        destination=destination,
        mode=mode,
        waypoints=waypoints if waypoints else None
    )
    
    if directions:
        route = directions[0]  # 取第一条路线
        leg = route["legs"][0]  # 取第一段
        
        result = {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "distance": leg["distance"]["text"],
            "duration": leg["duration"]["text"],
            "start_address": leg["start_address"],
            "end_address": leg["end_address"],
            "steps": [
                {
                    "distance": step["distance"]["text"],
                    "duration": step["duration"]["text"],
                    "instructions": step["html_instructions"],
                    "travel_mode": step["travel_mode"]
                }
                for step in leg["steps"][:10]  # 限制步骤数量
            ]
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
    else:
        return [types.TextContent(
            type="text",
            text="未找到路线"
        )]


async def get_distance_matrix(args: dict) -> list[types.TextContent]:
    """获取距离矩阵"""
    origins = args["origins"]
    destinations = args["destinations"]
    mode = args.get("mode", "driving")
    
    matrix = gmaps.distance_matrix(
        origins=origins,
        destinations=destinations,
        mode=mode
    )
    
    if matrix["status"] == "OK":
        results = []
        for i, origin in enumerate(origins):
            for j, destination in enumerate(destinations):
                element = matrix["rows"][i]["elements"][j]
                if element["status"] == "OK":
                    results.append({
                        "origin": origin,
                        "destination": destination,
                        "distance": element["distance"]["text"],
                        "duration": element["duration"]["text"]
                    })
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "mode": mode,
                "results": results
            }, ensure_ascii=False, indent=2)
        )]
    else:
        return [types.TextContent(
            type="text",
            text=f"获取距离矩阵失败: {matrix['status']}"
        )]


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