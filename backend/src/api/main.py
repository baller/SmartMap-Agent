"""
Travel Assistant FastAPI Application
旅行助手 FastAPI 主应用程序
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from src.core.travel_agent import TravelAgent, UserProfile
from src.core.mcp_client import MCPClient
from src.core.mcp_tools import TravelMcpTools
from src.core.session_manager import session_manager
from src.utils.info import (
    HOST, PORT, CORS_ORIGINS, DEFAULT_MODEL_NAME
)
from src.utils.pretty import ALogger

LOGGER = ALogger("[FastAPI]")

# 创建 FastAPI 应用
app = FastAPI(
    title="Travel Assistant API",
    description="基于 MCP 的智能旅行规划助手",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket 连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
        # 添加状态回调
        def status_callback(status: str, details: str):
            asyncio.create_task(self.send_status(session_id, status, details))
        
        # 添加流式回调
        async def stream_callback(stream_type: str, data: Any):
            await self.send_stream_data(session_id, stream_type, data)
        
        session_manager.add_status_callback(session_id, status_callback)
        session_manager.add_stream_callback(session_id, stream_callback)
        LOGGER.info(f"WebSocket connected for session: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            LOGGER.info(f"WebSocket disconnected for session: {session_id}")

    async def send_status(self, session_id: str, status: str, details: str = ""):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps({
                    "type": "status",
                    "status": status,
                    "details": details,
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                LOGGER.error(f"Error sending status to {session_id}: {e}")

    async def send_message(self, session_id: str, message: str, message_type: str = "message"):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps({
                    "type": message_type,
                    "content": message,
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                LOGGER.error(f"Error sending message to {session_id}: {e}")

    async def send_stream_data(self, session_id: str, stream_type: str, data: Any):
        """发送流式数据"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps({
                    "type": "stream",
                    "stream_type": stream_type,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                LOGGER.error(f"Error sending stream data to {session_id}: {e}")

manager = ConnectionManager()


# Pydantic 模型
class CreateSessionRequest(BaseModel):
    user_profile: Optional[Dict[str, Any]] = None


class TravelPlanRequest(BaseModel):
    request: str
    session_id: str


class UpdateProfileRequest(BaseModel):
    session_id: str
    profile_updates: Dict[str, Any]


# Agent 工厂函数
def create_travel_agent() -> TravelAgent:
    """创建旅行助手 Agent 实例"""
    mcp_clients = []
    
    # 创建 MCP 客户端
    tools = [
        TravelMcpTools.get_baidu_maps_tool(),  # 使用百度地图
        TravelMcpTools.get_weather_tool(),     # 天气工具
        TravelMcpTools.get_itinerary_tool()    # 行程规划工具
    ]
    
    for tool_info in tools:
        mcp_client = MCPClient(**tool_info.to_common_params())
        mcp_clients.append(mcp_client)
    
    # 创建系统提示词
    system_prompt = """你是一个专业的旅行规划助手，擅长为用户制定详细的旅行计划。

你的主要任务：
1. 理解用户的旅行需求（目的地、时间、预算、偏好等）
2. 使用可用的工具搜索相关信息：
   - 使用百度地图工具搜索景点、餐厅、交通信息和路线规划
   - 使用天气工具获取天气预报和天气提醒
   - 使用行程规划工具生成结构化的行程安排
3. 综合所有信息，为用户提供详细、实用的旅行计划

可用工具说明：
- map_geocode: 地址解析为坐标
- map_reverse_geocode: 坐标解析为地址
- map_search_places: 搜索地点信息
- map_search_nearby: 周边地点搜索
- map_place_detail: 获取地点详情
- map_direction: 路线规划
- map_distance: 距离计算
- get_current_weather: 当前天气
- get_weather_forecast: 天气预报
- plan_itinerary: 行程规划
- optimize_route: 路线优化

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

    return TravelAgent(
        mcp_clients=mcp_clients,
        model=DEFAULT_MODEL_NAME,
        system_prompt=system_prompt
    )


# API 路由
@app.post("/api/sessions", response_model=Dict[str, str])
async def create_session(request: CreateSessionRequest = None):
    """创建新的会话"""
    try:
        user_profile = None
        if request and request.user_profile:
            user_profile = UserProfile(**request.user_profile)
        
        session_id = session_manager.create_session(user_profile)
        return {"session_id": session_id}
    except Exception as e:
        LOGGER.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions", response_model=List[Dict[str, Any]])
async def list_sessions():
    """列出所有活跃会话"""
    try:
        return session_manager.list_sessions()
    except Exception as e:
        LOGGER.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}", response_model=Dict[str, Any])
async def get_session(session_id: str):
    """获取会话信息"""
    try:
        session_data = session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session_data.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Error getting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, background_tasks: BackgroundTasks):
    """删除会话"""
    try:
        session_data = session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        background_tasks.add_task(session_manager.delete_session, session_id)
        return {"message": "Session deleted"}
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Error deleting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/plan", response_model=Dict[str, str])
async def plan_travel(request: TravelPlanRequest):
    """规划旅行（REST API 方式）"""
    try:
        result = await session_manager.process_travel_request(
            session_id=request.session_id,
            request=request.request
        )
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        LOGGER.error(f"Error planning travel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/sessions/{session_id}/profile")
async def update_profile(session_id: str, request: UpdateProfileRequest):
    """更新用户配置文件"""
    try:
        session_manager.update_user_profile(session_id, request.profile_updates)
        return {"message": "Profile updated"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        LOGGER.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/history", response_model=List[Dict[str, Any]])
async def get_chat_history(session_id: str, limit: int = 50):
    """获取聊天历史"""
    try:
        history = session_manager.get_chat_history(session_id, limit)
        return history
    except Exception as e:
        LOGGER.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(session_manager.sessions)
    }


# WebSocket 路由
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket 连接端点"""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "travel_request":
                # 处理旅行规划请求
                request = message_data.get("content", "")
                if request:
                    try:
                        # 发送开始状态
                        await manager.send_status(session_id, "processing", "开始处理您的旅行规划请求...")
                        
                        # 处理请求
                        result = await session_manager.process_travel_request(session_id, request)
                        
                        # 发送结果
                        await manager.send_message(session_id, result, "travel_plan")
                        
                    except Exception as e:
                        error_msg = f"处理请求时出错: {str(e)}"
                        LOGGER.error(f"Error in WebSocket request: {e}")
                        await manager.send_message(session_id, error_msg, "error")
                        await manager.send_status(session_id, "error", error_msg)
            
            elif message_data.get("type") == "ping":
                # 心跳检测
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        LOGGER.error(f"WebSocket error for session {session_id}: {e}")
        manager.disconnect(session_id)


# 启动和关闭事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    LOGGER.title("STARTING TRAVEL ASSISTANT API")
    
    # 设置 Agent 工厂
    session_manager.set_agent_factory(create_travel_agent)
    
    # 启动会话管理器
    await session_manager.start()
    
    LOGGER.success(f"Travel Assistant API started on {HOST}:{PORT}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    LOGGER.title("SHUTTING DOWN TRAVEL ASSISTANT API")
    
    # 停止会话管理器
    await session_manager.stop()
    
    LOGGER.success("Travel Assistant API shutdown complete")


# 主函数
def main():
    """启动应用"""
    uvicorn.run(
        "src.api.main:app",
        host=HOST,
        port=PORT,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main() 