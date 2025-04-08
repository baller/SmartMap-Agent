import asyncio
import os
from mcp import Tool
from openai import AsyncOpenAI
from dataclasses import dataclass, field

from openai.types import FunctionDefinition
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
import dotenv
from pydantic import BaseModel
from rich import print as rprint

from augmented.utils import pretty

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

    def __post_init__(self):
        self.llm = AsyncOpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.environ.get("OPENAI_BASE_URL"),
        )
        if self.system_prompt:
            self.messages.insert(0, {"role": "system", "content": self.system_prompt})
        if self.context:
            self.messages.append({"role": "user", "content": self.context})

    async def chat(self, prompt: str = "", print_llm_output: bool = True):
        pretty.log_title("CHAT")
        if prompt:
            self.messages.append({"role": "user", "content": prompt})

        streaming = await self.llm.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=self.getToolsDefinition(),
            stream=True
        )
        pretty.log_title("RESPONSE")
        content = ""
        tool_calls: list[ToolCall] = []
        printed_llm_output = False
        async for chunk in streaming:
            delta = chunk.choices[0].delta
            # 处理 content
            if delta.content:
                content += delta.content or ""
                if print_llm_output:
                    print(delta.content, end="")
                    printed_llm_output = True
            # 处理 tool_calls
            if delta.tool_calls:
                for tool_call_chunk in delta.tool_calls:
                    # 第一次收到一个tool_call, 因为流式传输所以我们先设置一个占位值
                    if len(tool_call_chunk) <= tool_call_chunk.index:
                        tool_calls.append(ToolCall())
                    current_call = tool_calls[tool_call_chunk.index]
                    if tool_call_chunk.id:
                        current_call.id = tool_call_chunk.id or ""
                    if tool_call_chunk.function:
                        current_call.function.name = tool_call_chunk.function.name or ""
                        current_call.function.arguments = (
                            tool_call_chunk.function.arguments or ""
                        )
        if printed_llm_output:
            print()
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

    def getToolsDefinition(self) -> list[ChatCompletionToolParam]:
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


async def example():
    llm = AsyncChatOpenAI(
        model="gpt-4o-mini",
    )
    chat_resp = await llm.chat(prompt="Hello")
    rprint(chat_resp)


if __name__ == "__main__":
    asyncio.run(example())
