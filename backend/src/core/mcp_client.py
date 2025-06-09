"""
Travel Assistant MCP Client
基于参考项目的 MCP 客户端实现，用于与外部工具交互
"""

import asyncio
import os
from typing import Any, Optional, Dict
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters, Tool
from mcp.client.stdio import stdio_client

from rich import print as rprint

from dotenv import load_dotenv

from src.utils.pretty import RICH_CONSOLE, ALogger

load_dotenv()

LOGGER = ALogger("[MCPClient]")


class MCPClient:
    def __init__(
        self,
        name: str,
        command: str,
        args: list[str],
        env: Dict[str, str] = None,
        version: str = "0.0.1",
    ) -> None:
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.name = name
        self.version = version
        self.command = command
        self.args = args
        self.env = env or {}
        self.tools: list[Tool] = []

    async def init(self) -> None:
        """初始化 MCP 客户端"""
        LOGGER.title(f"INIT MCP CLIENT: {self.name}")
        await self._connect_to_server()

    async def cleanup(self) -> None:
        """清理 MCP 客户端资源"""
        try:
            LOGGER.title(f"CLEANUP MCP CLIENT: {self.name}")
            await self.exit_stack.aclose()
        except Exception as e:
            LOGGER.error(f"Error during MCP client cleanup: {e}")
            RICH_CONSOLE.print_exception()

    def get_tools(self) -> list[Tool]:
        """获取可用工具列表"""
        return self.tools

    async def _connect_to_server(self) -> None:
        """连接到 MCP 服务器"""
        # 准备环境变量
        server_env = os.environ.copy()
        
        # 解析并添加工具特定的环境变量
        for key, value in self.env.items():
            if value.startswith("${") and value.endswith("}"):
                # 从系统环境变量中获取值，如 ${BAIDU_MAP_API_KEY}
                env_var_name = value[2:-1]  # 移除 ${ 和 }
                env_value = os.getenv(env_var_name)
                if env_value:
                    server_env[key] = env_value
                    LOGGER.success(f"Set environment variable {key} from {env_var_name}")
                else:
                    LOGGER.warning(f"{env_var_name} environment variable is not set")
            else:
                server_env[key] = value
        
        server_params = StdioServerParameters(
            command=self.command,
            args=self.args,
            env=server_env
        )

        try:
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params),
            )
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )

            await self.session.initialize()

            # 列出可用工具
            response = await self.session.list_tools()
            self.tools = response.tools
            LOGGER.success(f"Connected to {self.name} with tools: {[tool.name for tool in self.tools]}")
        
        except Exception as e:
            LOGGER.error(f"Failed to connect to MCP server {self.name}: {e}")
            raise

    async def call_tool(self, name: str, params: dict[str, Any]):
        """调用指定的工具"""
        if not self.session:
            raise ValueError("MCP session not initialized")
        
        try:
            LOGGER.tool_call(name, str(params))
            result = await self.session.call_tool(name, params)
            LOGGER.success(f"Tool {name} executed successfully")
            return result
        except Exception as e:
            LOGGER.error(f"Error calling tool {name}: {e}")
            raise 