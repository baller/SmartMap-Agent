"""
MCP Tools Configuration for Travel Assistant
旅行助手的 MCP 工具配置
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from pathlib import Path
import sys

@dataclass
class McpToolInfo:
    """MCP 工具信息"""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str]
    description: str = ""

    def to_common_params(self) -> Dict[str, Any]:
        """转换为通用参数格式"""
        return {
            "name": self.name,
            "command": self.command,
            "args": self.args,
            "env": self.env
        }


class TravelMcpTools:
    """旅行相关的 MCP 工具配置"""
    
    @classmethod
    def get_baidu_maps_tool(cls) -> McpToolInfo:
        """百度地图工具配置"""
        return McpToolInfo(
            name="baidu-maps",
            command="npx",
            args=["-y", "@baidumap/mcp-server-baidu-map"],
            env={"BAIDU_MAP_API_KEY": "${BAIDU_MAP_API_KEY}"},
            description="百度地图 MCP Server，提供地理编码、地点检索、路线规划等功能"
        )
    
    @classmethod  
    def get_weather_tool(cls) -> McpToolInfo:
        """天气工具配置"""
        project_root = Path(__file__).parent.parent.parent
        weather_server_path = project_root / "src" / "tools" / "weather_mcp_server.py"
        
        return McpToolInfo(
            name="weather",
            command=sys.executable,
            args=[str(weather_server_path)],
            env={"WEATHER_API_KEY": "${WEATHER_API_KEY}"},
            description="天气查询工具，提供当前天气、天气预报和天气提醒"
        )
    
    @classmethod
    def get_itinerary_tool(cls) -> McpToolInfo:
        """行程规划工具配置"""
        project_root = Path(__file__).parent.parent.parent
        itinerary_server_path = project_root / "src" / "tools" / "itinerary_mcp_server.py"
        
        return McpToolInfo(
            name="itinerary",
            command=sys.executable,
            args=[str(itinerary_server_path)],
            env={},
            description="行程规划工具，提供多日行程规划、路线优化、活动推荐和预算估算"
        )

    # 兼容性属性（保持向后兼容）
    @property
    def maps(self) -> McpToolInfo:
        """地图工具 - 现在使用百度地图"""
        return self.get_baidu_maps_tool()
    
    @property
    def weather(self) -> McpToolInfo:
        """天气工具"""
        return self.get_weather_tool()
    
    @property
    def itinerary(self) -> McpToolInfo:
        """行程规划工具"""
        return self.get_itinerary_tool()

# 创建实例供外部使用
TravelMcpTools = TravelMcpTools() 