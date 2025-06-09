"""
Travel Assistant MCP Client
基于参考项目的 MCP 客户端实现，用于与外部工具交互
"""

import asyncio
from typing import Any, Optional
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
        version: str = "0.0.1",
    ) -> None:
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.name = name
        self.version = version
        self.command = command
        self.args = args
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
        server_params = StdioServerParameters(
            command=self.command,
            args=self.args,
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