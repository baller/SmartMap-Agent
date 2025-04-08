import asyncio
from dataclasses import dataclass
import json
import os
import shlex

from rich import print as rprint

from augmented.chat_openai import AsyncChatOpenAI
from augmented.mcp_client import MCPClient
from augmented.utils import pretty
from augmented.utils.info import PROJECT_ROOT_DIR


class McpCmdOptions:
    uvx_use_cn_mirror = (
        ("--extra-index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple")
        if os.environ.get("USE_CN_MIRROR")
        else ""
    )
    npx_use_cn_mirror = (
        ("--registry https://registry.npmmirror.com")
        if os.environ.get("USE_CN_MIRROR")
        else ""
    )
    fetch_server_mcp_use_proxy = (
        f"--proxy-url {os.environ.get('PROXY_URL')}"
        if os.environ.get("PROXY_URL")
        else ""
    )


@dataclass
class Agent:
    mcp_clients: list[MCPClient]
    model: str
    llm: AsyncChatOpenAI | None = None
    system_prompt: str = ""
    context: str = ""

    async def init(self):
        pretty.log_title("[Agent] INIT LLM&TOOLS")
        tools = []
        for mcp_client in self.mcp_clients:
            await mcp_client.init()
            tools.extend(mcp_client.get_tools())
        self.llm = AsyncChatOpenAI(
            self.model,
            tools=tools,
            system_prompt=self.system_prompt,
            context=self.context,
        )

    async def close(self) -> None:
        pretty.log_title("[Agent] CLOSE LLM&TOOLS")
        for mcp_client in self.mcp_clients:
            await mcp_client.close()

    async def invoke(self, prompt: str) -> str | None:
        try:
            return await self._invoke(prompt)
        finally:
            await self.close()

    async def _invoke(self, prompt: str) -> str | None:
        if self.llm is None:
            raise ValueError("llm not call .init()")
        chat_resp = await self.llm.chat(prompt)
        i = 0
        while True:
            pretty.log_title(f"INVOKE CYCLE {i}")
            i += 1
            # 处理工具调用
            rprint(chat_resp)
            if chat_resp.tool_calls:
                for tool_call in chat_resp.tool_calls:
                    target_mcp_client: MCPClient | None = None
                    for mcp_client in self.mcp_clients:
                        if tool_call.function.name in [
                            t.name for t in mcp_client.get_tools()
                        ]:
                            target_mcp_client = mcp_client
                            break
                    if target_mcp_client:
                        pretty.log_title(f"TOOL USE `{tool_call.function.name}`")
                        rprint("with args:", tool_call.function.arguments)
                        mcp_result = await target_mcp_client.call_tool(
                            tool_call.function.name,
                            json.loads(tool_call.function.arguments),
                        )
                        rprint("call result:", mcp_result)
                        self.llm.append_tool_result(
                            tool_call.id, mcp_result.model_dump_json()
                        )
                    else:
                        self.llm.append_tool_result(tool_call.id, "tool not found")
                chat_resp = await self.llm.chat()
            else:
                return chat_resp.content


async def example():
    enabled_mcp_clients = []
    for mcp_name, cmd in [
        (
            "filesystem",
            f"npx {McpCmdOptions.npx_use_cn_mirror} -y @modelcontextprotocol/server-filesystem {PROJECT_ROOT_DIR!s}",
        ),
        (
            "fetch",
            f"uvx {McpCmdOptions.uvx_use_cn_mirror} mcp-server-fetch {McpCmdOptions.fetch_server_mcp_use_proxy}".strip(),
        ),
    ]:
        rprint(cmd)
        command, *args = shlex.split(cmd)
        mcp_client = MCPClient(
            name=mcp_name,
            command=command,
            args=args,
        )
        enabled_mcp_clients.append(mcp_client)

    agent = Agent(
        model="gpt-4o-mini",
        mcp_clients=enabled_mcp_clients,
    )
    await agent.init()
    resp = await agent.invoke(
        f"爬取 https://news.ycombinator.com 的内容, 并且总结后保存在 {PROJECT_ROOT_DIR / 'output' / 'step3-agent-with-mcp'!s} 目录下的news.md文件中"
    )
    rprint(resp)


if __name__ == "__main__":
    asyncio.run(example())
