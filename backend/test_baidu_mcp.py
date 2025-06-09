#!/usr/bin/env python3
"""
测试百度地图 MCP Server 连接
"""

import asyncio
import os
from src.core.mcp_client import MCPClient
from src.core.mcp_tools import TravelMcpTools

async def test_baidu_maps():
    """测试百度地图 MCP Server"""
    
    # 检查环境变量
    api_key = os.getenv("BAIDU_MAP_API_KEY")
    print(f"BAIDU_MAP_API_KEY: {api_key[:10] + '...' if api_key else 'Not found'}")
    
    # 获取百度地图工具配置
    baidu_tool = TravelMcpTools.get_baidu_maps_tool()
    print(f"Tool config: {baidu_tool}")
    
    # 创建 MCP 客户端
    client = MCPClient(**baidu_tool.to_common_params())
    
    try:
        # 初始化客户端
        await client.init()
        
        # 获取工具列表
        tools = client.get_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")
        
        # 测试一个简单的工具调用
        if tools:
            print("\n测试地理编码功能...")
            result = await client.call_tool("map_geocode", {
                "address": "北京天安门"
            })
            print(f"Geocode result: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(test_baidu_maps()) 