"""
Session Manager for Travel Assistant
会话管理器，用于管理用户会话状态和历史记录
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import weakref

from src.core.travel_agent import TravelAgent, UserProfile, SessionContext
from src.utils.pretty import ALogger
from src.utils.info import MAX_SESSIONS, SESSION_TIMEOUT

LOGGER = ALogger("[SessionManager]")


@dataclass
class SessionData:
    """会话数据"""
    session_id: str
    user_profile: UserProfile
    chat_history: List[Dict[str, Any]]
    created_at: datetime
    last_activity: datetime
    status: str = "active"  # active, thinking, processing, completed, error
    current_request: str = ""
    agent_instance: Optional[TravelAgent] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        # 不序列化 agent_instance
        data.pop('agent_instance', None)
        return data

    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = datetime.now()

    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return (datetime.now() - self.last_activity).total_seconds() > SESSION_TIMEOUT


class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}
        self.status_callbacks: Dict[str, List[Callable]] = {}
        self.stream_callbacks: Dict[str, List[Callable]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._agent_factory: Optional[Callable[[], TravelAgent]] = None

    def set_agent_factory(self, factory: Callable[[], TravelAgent]):
        """设置 Agent 工厂函数"""
        self._agent_factory = factory

    async def start(self):
        """启动会话管理器"""
        LOGGER.title("START SESSION MANAGER")
        # 启动清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())

    async def stop(self):
        """停止会话管理器"""
        LOGGER.title("STOP SESSION MANAGER")
        # 取消清理任务
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # 清理所有会话
        await self._cleanup_all_sessions()

    def create_session(self, user_profile: UserProfile = None) -> str:
        """创建新会话"""
        if len(self.sessions) >= MAX_SESSIONS:
            # 清理最旧的会话
            oldest_session_id = min(
                self.sessions.keys(),
                key=lambda sid: self.sessions[sid].last_activity
            )
            asyncio.create_task(self.delete_session(oldest_session_id))

        session_id = str(uuid.uuid4())
        if user_profile is None:
            user_profile = UserProfile()

        session_data = SessionData(
            session_id=session_id,
            user_profile=user_profile,
            chat_history=[],
            created_at=datetime.now(),
            last_activity=datetime.now()
        )

        self.sessions[session_id] = session_data
        self.status_callbacks[session_id] = []
        self.stream_callbacks[session_id] = []

        LOGGER.success(f"Created session: {session_id}")
        return session_id

    async def delete_session(self, session_id: str):
        """删除会话"""
        if session_id in self.sessions:
            session_data = self.sessions[session_id]
            
            # 清理 Agent 实例
            if session_data.agent_instance:
                try:
                    await session_data.agent_instance.cleanup()
                except Exception as e:
                    LOGGER.error(f"Error cleaning up agent for session {session_id}: {e}")

            # 删除会话数据
            del self.sessions[session_id]
            
            # 清理状态回调
            if session_id in self.status_callbacks:
                del self.status_callbacks[session_id]
                
            # 清理流式回调
            if session_id in self.stream_callbacks:
                del self.stream_callbacks[session_id]

            LOGGER.info(f"Deleted session: {session_id}")

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """获取会话数据"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if not session.is_expired():
                session.update_activity()
                return session
            else:
                # 会话已过期，异步删除
                asyncio.create_task(self.delete_session(session_id))
        return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有活跃会话"""
        active_sessions = []
        for session_id, session_data in self.sessions.items():
            if not session_data.is_expired():
                active_sessions.append(session_data.to_dict())
        return active_sessions

    def add_status_callback(self, session_id: str, callback: Callable[[str, str], None]):
        """添加状态回调函数"""
        if session_id not in self.status_callbacks:
            self.status_callbacks[session_id] = []
        self.status_callbacks[session_id].append(callback)

    def remove_status_callback(self, session_id: str, callback: Callable[[str, str], None]):
        """移除状态回调函数"""
        if session_id in self.status_callbacks:
            try:
                self.status_callbacks[session_id].remove(callback)
            except ValueError:
                pass

    def add_stream_callback(self, session_id: str, callback: Callable[[str, Any], None]):
        """添加流式回调函数"""
        if session_id not in self.stream_callbacks:
            self.stream_callbacks[session_id] = []
        self.stream_callbacks[session_id].append(callback)

    def remove_stream_callback(self, session_id: str, callback: Callable[[str, Any], None]):
        """移除流式回调函数"""
        if session_id in self.stream_callbacks:
            try:
                self.stream_callbacks[session_id].remove(callback)
            except ValueError:
                pass

    def _emit_status(self, session_id: str, status: str, details: str = ""):
        """发送状态更新到所有回调"""
        if session_id in self.sessions:
            self.sessions[session_id].status = status
            self.sessions[session_id].update_activity()

        if session_id in self.status_callbacks:
            for callback in self.status_callbacks[session_id]:
                try:
                    callback(status, details)
                except Exception as e:
                    LOGGER.error(f"Error in status callback: {e}")

    async def _emit_stream(self, session_id: str, stream_type: str, data: Any):
        """发送流式数据到所有回调"""
        if session_id in self.stream_callbacks:
            for callback in self.stream_callbacks[session_id]:
                try:
                    await callback(stream_type, data)
                except Exception as e:
                    LOGGER.error(f"Error in stream callback: {e}")

    async def _get_or_create_agent(self, session_id: str) -> TravelAgent:
        """获取或创建 Agent 实例"""
        session_data = self.get_session(session_id)
        if not session_data:
            raise ValueError(f"Session {session_id} not found")

        if session_data.agent_instance is None:
            if not self._agent_factory:
                raise ValueError("Agent factory not set")
            
            # 创建新的 Agent 实例
            agent = self._agent_factory()
            
            # 设置状态回调
            agent.set_status_callback(lambda status, details: self._emit_status(session_id, status, details))
            
            # 设置流式回调
            agent.set_stream_callback(lambda stream_type, data: asyncio.create_task(self._emit_stream(session_id, stream_type, data)))
            
            # 初始化 Agent
            await agent.init()
            session_data.agent_instance = agent

        return session_data.agent_instance

    async def process_travel_request(self, session_id: str, request: str) -> str:
        """处理旅行规划请求"""
        session_data = self.get_session(session_id)
        if not session_data:
            raise ValueError(f"Session {session_id} not found")

        try:
            # 添加用户消息到历史
            user_message = {
                "role": "user",
                "content": request,
                "timestamp": datetime.now().isoformat()
            }
            session_data.chat_history.append(user_message)
            session_data.current_request = request

            # 获取 Agent 实例
            agent = await self._get_or_create_agent(session_id)

            # 执行旅行规划
            self._emit_status(session_id, "processing", "开始处理您的旅行规划请求...")
            
            result = await agent.plan_travel(
                request=request,
                user_profile=session_data.user_profile,
                session_id=session_id
            )

            # 添加助手回复到历史
            assistant_message = {
                "role": "assistant",
                "content": result,
                "timestamp": datetime.now().isoformat()
            }
            session_data.chat_history.append(assistant_message)

            self._emit_status(session_id, "completed", "旅行规划完成")
            return result

        except Exception as e:
            error_msg = f"处理请求时出错: {str(e)}"
            LOGGER.error(f"Error processing travel request for session {session_id}: {e}")
            
            # 添加错误消息到历史
            error_message = {
                "role": "system",
                "content": error_msg,
                "timestamp": datetime.now().isoformat()
            }
            session_data.chat_history.append(error_message)
            
            self._emit_status(session_id, "error", error_msg)
            raise

    def update_user_profile(self, session_id: str, profile_updates: Dict[str, Any]):
        """更新用户配置文件"""
        session_data = self.get_session(session_id)
        if not session_data:
            raise ValueError(f"Session {session_id} not found")

        # 更新用户配置文件
        for key, value in profile_updates.items():
            if hasattr(session_data.user_profile, key):
                setattr(session_data.user_profile, key, value)

        LOGGER.info(f"Updated user profile for session {session_id}")

    def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取聊天历史"""
        session_data = self.get_session(session_id)
        if not session_data:
            return []

        return session_data.chat_history[-limit:] if limit else session_data.chat_history

    async def _cleanup_expired_sessions(self):
        """定期清理过期会话"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                
                expired_sessions = []
                for session_id, session_data in self.sessions.items():
                    if session_data.is_expired():
                        expired_sessions.append(session_id)

                for session_id in expired_sessions:
                    await self.delete_session(session_id)
                    LOGGER.info(f"Cleaned up expired session: {session_id}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                LOGGER.error(f"Error in cleanup task: {e}")

    async def _cleanup_all_sessions(self):
        """清理所有会话"""
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self.delete_session(session_id)


# 全局会话管理器实例
session_manager = SessionManager() 