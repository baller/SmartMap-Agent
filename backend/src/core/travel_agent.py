"""
Travel Assistant Agent
基于参考项目的 Agent 实现，专门用于旅行规划
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable

from rich import print as rprint

from src.core.chat_openai import AsyncChatOpenAI
from src.core.mcp_client import MCPClient
from src.core.mcp_tools import TravelMcpTools
from src.utils import pretty
from src.utils.info import DEFAULT_MODEL_NAME, PROJECT_ROOT_DIR

LOGGER = pretty.ALogger("[TravelAgent]")


@dataclass
class UserProfile:
    """用户配置文件"""
    name: str = "用户"
    home_location: str = "北京"
    preferences: List[str] = None
    budget_range: str = "中等"
    travel_style: str = "休闲"

    def __post_init__(self):
        if self.preferences is None:
            self.preferences = ["文化古迹", "美食", "自然风光"]


@dataclass
class SessionContext:
    """会话上下文"""
    session_id: str
    user_profile: UserProfile
    chat_history: List[Dict[str, Any]]
    current_request: str = ""
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.chat_history is None:
            self.chat_history = []


class MCPContextManager:
    """MCP 上下文管理器"""
    
    def __init__(self):
        self.user_profile: Optional[UserProfile] = None
        self.session_context: Optional[SessionContext] = None
        self.environment_context: Dict[str, Any] = {}
        self.tool_context: Dict[str, Any] = {}
        
    def set_user_profile(self, profile: UserProfile):
        """设置用户配置文件"""
        self.user_profile = profile
        
    def set_session_context(self, context: SessionContext):
        """设置会话上下文"""
        self.session_context = context
        
    def update_environment_context(self):
        """更新环境上下文"""
        self.environment_context = {
            "current_time": datetime.now().isoformat(),
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "day_of_week": datetime.now().strftime("%A"),
            "timezone": "Asia/Shanghai"
        }
        
    def update_tool_context(self, tools: List[Any], tool_results: Dict[str, Any] = None):
        """更新工具上下文"""
        self.tool_context = {
            "available_tools": [{"name": tool.name, "description": tool.description} for tool in tools],
            "tool_results": tool_results or {}
        }
        
    def get_structured_context(self) -> str:
        """获取结构化的上下文信息"""
        context_parts = []
        
        # 用户配置文件上下文
        if self.user_profile:
            context_parts.append(f"""
## 用户配置文件
- 姓名: {self.user_profile.name}
- 居住地: {self.user_profile.home_location}
- 偏好: {', '.join(self.user_profile.preferences)}
- 预算: {self.user_profile.budget_range}
- 旅行风格: {self.user_profile.travel_style}
""")
        
        # 环境上下文
        if self.environment_context:
            context_parts.append(f"""
## 环境信息
- 当前时间: {self.environment_context.get('current_time')}
- 当前日期: {self.environment_context.get('current_date')}
- 星期: {self.environment_context.get('day_of_week')}
""")
        
        # 会话上下文
        if self.session_context:
            context_parts.append(f"""
## 会话信息
- 会话ID: {self.session_context.session_id}
- 创建时间: {self.session_context.created_at.isoformat()}
- 当前请求: {self.session_context.current_request}
""")
        
        return "\n".join(context_parts)


@dataclass
class TravelAgent:
    """旅行助手 Agent"""
    
    mcp_clients: list[MCPClient]
    model: str
    llm: AsyncChatOpenAI | None = None
    system_prompt: str = ""
    mcp_context_manager: MCPContextManager = None
    status_callback: Optional[Callable[[str, str], None]] = None
    stream_callback: Optional[Callable[[str, Any], None]] = None

    def __post_init__(self):
        if self.mcp_context_manager is None:
            self.mcp_context_manager = MCPContextManager()

    async def init(self) -> None:
        """初始化 Agent"""
        LOGGER.title("INIT TRAVEL AGENT")
        tools = []
        for mcp_client in self.mcp_clients:
            await mcp_client.init()
            tools.extend(mcp_client.get_tools())
        
        # 更新工具上下文
        self.mcp_context_manager.update_tool_context(tools)
        self.mcp_context_manager.update_environment_context()
        
        # 获取结构化上下文
        context = self.mcp_context_manager.get_structured_context()
        
        self.llm = AsyncChatOpenAI(
            self.model,
            tools=tools,
            system_prompt=self.system_prompt,
            context=context,
        )

    async def cleanup(self) -> None:
        """清理资源"""
        LOGGER.title("CLEANUP TRAVEL AGENT")
        while self.mcp_clients:
            mcp_client = self.mcp_clients.pop()
            await mcp_client.cleanup()

    def set_status_callback(self, callback: Callable[[str, str], None]):
        """设置状态回调函数"""
        self.status_callback = callback

    def set_stream_callback(self, callback: Callable[[str, Any], None]):
        """设置流式回调函数"""
        self.stream_callback = callback

    def _emit_status(self, status: str, details: str = ""):
        """发送状态更新"""
        if self.status_callback:
            self.status_callback(status, details)

    async def plan_travel(self, request: str, user_profile: UserProfile = None, session_id: str = "default") -> str:
        """规划旅行行程"""
        try:
            # 设置用户配置文件
            if user_profile is None:
                user_profile = UserProfile()
            self.mcp_context_manager.set_user_profile(user_profile)
            
            # 设置会话上下文
            session_context = SessionContext(
                session_id=session_id,
                user_profile=user_profile,
                chat_history=[],
                current_request=request
            )
            self.mcp_context_manager.set_session_context(session_context)
            
            # 更新上下文
            self.mcp_context_manager.update_environment_context()
            
            return await self._invoke(request)
        except Exception as e:
            LOGGER.error(f"Error during travel planning: {e}")
            raise

    async def _invoke(self, prompt: str) -> str | None:
        """执行 Agent 推理循环"""
        if self.llm is None:
            raise ValueError("Agent not initialized, call .init() first")
        
        # 创建流式回调函数
        async def handle_stream(stream_type: str, data: Any):
            if self.stream_callback:
                await self.stream_callback(stream_type, data)
        
        async def handle_tool_call(call_type: str, data: Any):
            if self.stream_callback:
                await self.stream_callback(call_type, data)
        
        # 发送思考过程模拟
        self._emit_status("thinking", "正在分析您的旅行需求...")
        if self.stream_callback:
            # 分析用户请求
            await self.stream_callback("reasoning", f"用户请求：{prompt}\n\n")
            await asyncio.sleep(0.3)
            
            await self.stream_callback("reasoning", "分析步骤：\n")
            await asyncio.sleep(0.2)
            
            await self.stream_callback("reasoning", "1. 识别关键信息：\n")
            await asyncio.sleep(0.3)
            
            # 简单的关键词分析
            key_info = []
            if "天" in prompt or "日" in prompt:
                await self.stream_callback("reasoning", "   - 发现时间信息\n")
                key_info.append("时间")
            if "预算" in prompt or "元" in prompt or "钱" in prompt:
                await self.stream_callback("reasoning", "   - 发现预算信息\n")
                key_info.append("预算")
            if any(city in prompt for city in ["北京", "上海", "杭州", "广州", "深圳", "成都", "西安"]):
                await self.stream_callback("reasoning", "   - 发现目的地信息\n")
                key_info.append("目的地")
            if any(keyword in prompt for keyword in ["亲子", "家庭", "孩子", "儿童"]):
                await self.stream_callback("reasoning", "   - 发现旅行类型：亲子游\n")
                key_info.append("亲子游")
            
            await asyncio.sleep(0.4)
            await self.stream_callback("reasoning", "\n2. 确定需要的工具：\n")
            await self.stream_callback("reasoning", "   - 地图搜索工具：查找景点和路线\n")
            await self.stream_callback("reasoning", "   - 天气工具：获取天气预报\n")
            await self.stream_callback("reasoning", "   - 行程规划工具：制定详细计划\n")
            
            await asyncio.sleep(0.3)
            await self.stream_callback("reasoning", "\n3. 开始调用工具获取信息...\n\n")
        
        chat_resp = await self.llm.chat(
            prompt, 
            print_llm_output=False,
            stream_callback=handle_stream,
            tool_call_callback=handle_tool_call
        )
        
        i = 0
        while True:
            LOGGER.title(f"INVOKE CYCLE {i}")
            i += 1
            
            # 处理工具调用
            if chat_resp.tool_calls:
                self._emit_status("calling_tools", f"正在调用 {len(chat_resp.tool_calls)} 个工具获取信息...")
                
                # 发送工具调用开始信息
                if self.stream_callback:
                    await self.stream_callback("tool_calls_start", {
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "function_name": tc.function.name,
                                "arguments": tc.function.arguments
                            } for tc in chat_resp.tool_calls
                        ]
                    })
                    # 暂停reasoning，开始工具调用
                    await self.stream_callback("reasoning", "\n🔧 开始调用工具...\n")
                
                for tool_call in chat_resp.tool_calls:
                    target_mcp_client: MCPClient | None = None
                    for mcp_client in self.mcp_clients:
                        if tool_call.function.name in [t.name for t in mcp_client.get_tools()]:
                            target_mcp_client = mcp_client
                            break
                    
                    if target_mcp_client:
                        self._emit_status("tool_calling", f"正在调用 {tool_call.function.name}")
                        LOGGER.title(f"TOOL USE `{tool_call.function.name}`")
                        LOGGER.info(f"with args: {tool_call.function.arguments}")
                        
                        # 发送工具调用详情
                        if self.stream_callback:
                            await self.stream_callback("tool_call_detail", {
                                "tool_call_id": tool_call.id,
                                "function_name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                                "status": "calling"
                            })
                        
                        try:
                            mcp_result = await target_mcp_client.call_tool(
                                tool_call.function.name,
                                json.loads(tool_call.function.arguments),
                            )
                            LOGGER.success(f"Tool result: {str(mcp_result)[:200]}...")
                            self.llm.append_tool_result(
                                tool_call.id, mcp_result.model_dump_json()
                            )
                            
                            # 发送工具调用结果
                            if self.stream_callback:
                                await self.stream_callback("tool_call_result", {
                                    "tool_call_id": tool_call.id,
                                    "function_name": tool_call.function.name,
                                    "result": str(mcp_result)[:500] + "..." if len(str(mcp_result)) > 500 else str(mcp_result),
                                    "status": "success"
                                })
                                # 添加reasoning反馈
                                await self.stream_callback("reasoning", f"✓ {tool_call.function.name} 调用成功，获得了相关信息\n")
                        except Exception as e:
                            LOGGER.error(f"Tool call failed: {e}")
                            self.llm.append_tool_result(tool_call.id, f"工具调用失败: {str(e)}")
                            
                            # 发送工具调用错误
                            if self.stream_callback:
                                await self.stream_callback("tool_call_result", {
                                    "tool_call_id": tool_call.id,
                                    "function_name": tool_call.function.name,
                                    "error": str(e),
                                    "status": "error"
                                })
                    else:
                        LOGGER.warning(f"Tool {tool_call.function.name} not found")
                        self.llm.append_tool_result(tool_call.id, "工具未找到")
                        
                        # 发送工具未找到错误
                        if self.stream_callback:
                            await self.stream_callback("tool_call_result", {
                                "tool_call_id": tool_call.id,
                                "function_name": tool_call.function.name,
                                "error": "工具未找到",
                                "status": "not_found"
                            })
                
                self._emit_status("processing", "正在处理工具返回的信息...")
                # 添加reasoning反馈
                if self.stream_callback:
                    await self.stream_callback("reasoning", "\n📝 处理工具返回的信息：\n")
                    await asyncio.sleep(0.3)
                    await self.stream_callback("reasoning", "   - 分析获取的景点数据\n")
                    await self.stream_callback("reasoning", "   - 整合天气信息\n")
                    await self.stream_callback("reasoning", "   - 考虑用户偏好和预算\n")
                    await self.stream_callback("reasoning", "   - 优化行程安排\n")
                    await asyncio.sleep(0.5)
                    await self.stream_callback("reasoning", "\n🎯 开始生成最终的旅行方案...\n")
                
                chat_resp = await self.llm.chat(
                    print_llm_output=False,
                    stream_callback=handle_stream,
                    tool_call_callback=handle_tool_call
                )
            else:
                self._emit_status("completed", "旅行规划完成")
                # 最终reasoning总结
                if self.stream_callback:
                    await self.stream_callback("reasoning", "✅ 分析完成，开始生成最终的旅行计划\n")
                return chat_resp.content

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的旅行规划助手，擅长为用户制定详细的旅行计划。

你的主要任务：
1. 理解用户的旅行需求（目的地、时间、预算、偏好等）
2. 使用可用的工具搜索相关信息：
   - 使用 search_places 工具搜索景点、餐厅、交通信息
   - 使用 get_current_weather/get_weather_forecast 工具获取天气预报
   - 使用 plan_itinerary 工具生成结构化的行程安排
3. 综合所有信息，为用户提供详细、实用的旅行计划

规划原则：
- 根据用户偏好和预算合理安排
- 考虑交通便利性和时间安排
- 提供多样化的活动选择
- 包含实用的旅行提示

回答格式：
- 使用清晰的结构化格式
- 包含详细的时间安排
- 提供具体的地点信息和交通方式
- 给出预算估算和实用建议

请始终保持友好、专业的态度，并根据用户的具体需求调整建议。""" 