"""
Travel Assistant OpenAI Chat Client
基于参考项目的 OpenAI 客户端实现
"""

import asyncio
import os
from mcp import Tool
from openai import NOT_GIVEN, AsyncOpenAI
from dataclasses import dataclass, field

from openai.types import FunctionDefinition
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
import dotenv
from pydantic import BaseModel
from rich import print as rprint

from src.utils import pretty
from src.utils.info import DEFAULT_MODEL_NAME, OPENAI_API_KEY, OPENAI_BASE_URL

LOGGER = pretty.ALogger("[ChatOpenAI]")

dotenv.load_dotenv()


class ToolCallFunction(BaseModel):
    name: str = ""
    arguments: str = ""


class ToolCall(BaseModel):
    id: str = ""
    function: ToolCallFunction = ToolCallFunction()


class ChatOpenAIChatResponse(BaseModel):
    content: str = ""
    tool_calls: list[ToolCall] = []


@dataclass
class AsyncChatOpenAI:
    model: str
    messages: list[ChatCompletionMessageParam] = field(default_factory=list)
    tools: list[Tool] = field(default_factory=list)

    system_prompt: str = ""
    context: str = ""

    llm: AsyncOpenAI = field(init=False)

    def __post_init__(self) -> None:
        # API 配置
        api_key = os.environ.get("SILICONFLOW_API_KEY") or os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("SILICONFLOW_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        
        if not api_key:
            raise ValueError("请设置 SILICONFLOW_API_KEY 或 OPENAI_API_KEY 环境变量")
        
        self.llm = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        
        # 初始化消息
        if self.system_prompt:
            self.messages.insert(0, {"role": "system", "content": self.system_prompt})
        if self.context:
            self.messages.append({"role": "user", "content": self.context})

    async def chat(
        self, prompt: str = "", print_llm_output: bool = True
    ) -> ChatOpenAIChatResponse:
        """发起聊天对话"""
        try:
            return await self._chat(prompt, print_llm_output)
        except Exception as e:
            LOGGER.error(f"Error during chat: {e}")
            raise

    async def _chat(
        self, prompt: str = "", print_llm_output: bool = True
    ) -> ChatOpenAIChatResponse:
        LOGGER.title("CHAT")
        if prompt:
            self.messages.append({"role": "user", "content": prompt})

        content = ""
        tool_calls: list[ToolCall] = []
        printed_llm_output = False
        param_tools = self.get_tools_definition() or NOT_GIVEN
        
        async with await self.llm.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=param_tools,
            stream=True,
        ) as stream:
            LOGGER.title("RESPONSE")
            async for chunk in stream:
                delta = chunk.choices[0].delta
                # 处理 content
                if delta.content:
                    content += delta.content or ""
                    if print_llm_output:
                        print(delta.content, end="")
                        printed_llm_output = True
                # 处理 tool_calls
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        if len(tool_calls) <= tool_call.index:
                            tool_calls.append(ToolCall())
                        this_tool_call = tool_calls[tool_call.index]
                        if tool_call.id:
                            this_tool_call.id += tool_call.id or ""
                        if tool_call.function:
                            if tool_call.function.name:
                                this_tool_call.function.name += (
                                    tool_call.function.name or ""
                                )
                            if tool_call.function.arguments:
                                this_tool_call.function.arguments += (
                                    tool_call.function.arguments or ""
                                )
        
        if printed_llm_output:
            print()
            
        # 添加助手回复到消息历史
        self.messages.append(
            {
                "role": "assistant",
                "content": content,
                "tool_calls": [
                    {
                        "type": "function",
                        "id": tc.id,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ],
            }
        )
        return ChatOpenAIChatResponse(
            content=content,
            tool_calls=tool_calls,
        )

    def get_tools_definition(self) -> list[ChatCompletionToolParam]:
        """获取工具定义"""
        return [
            ChatCompletionToolParam(
                type="function",
                function=FunctionDefinition(
                    name=t.name,
                    description=t.description,
                    parameters=t.inputSchema,
                ),
            )
            for t in self.tools
        ]

    def append_tool_result(self, tool_call_id: str, tool_output: str) -> None:
        """添加工具调用结果到消息历史"""
        self.messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": tool_output,
            }
        )

    def get_message_history(self) -> list[ChatCompletionMessageParam]:
        """获取消息历史"""
        return self.messages.copy()

    def clear_messages(self) -> None:
        """清空消息历史（保留系统提示）"""
        system_messages = [msg for msg in self.messages if msg.get("role") == "system"]
        self.messages = system_messages 