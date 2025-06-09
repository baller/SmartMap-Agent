# 智能旅行助手 (Travel Assistant Agent)

基于 Model Context Protocol (MCP) 和 AI 大模型的智能旅行规划助手。为用户提供个性化的旅行计划，包括景点推荐、路线规划、预算估算等功能。

## 🌟 特性

- **🤖 AI 智能规划**: 基于 OpenAI GPT 模型的智能旅行规划
- **🔧 MCP 工具集成**: 使用 Model Context Protocol 集成外部工具
- **🗺️ 百度地图集成**: 国内首家兼容 MCP 协议的地图服务，获取真实的地点和路线信息
- **🌤️ 天气数据支持**: 集成 OpenWeatherMap API，提供天气预报和建议
- **💬 实时交互**: WebSocket 支持的实时对话和状态更新
- **📱 现代化 UI**: 基于 React + Next.js + Tailwind CSS 的美观界面
- **⚡ 流式响应**: 实时显示 AI 思考过程和工具调用状态

## 🏗️ 系统架构

### 后端架构
```
backend/
├── src/
│   ├── core/           # 核心模块
│   │   ├── travel_agent.py      # 主要 Agent 实现
│   │   ├── mcp_client.py        # MCP 客户端
│   │   ├── chat_openai.py       # OpenAI 客户端
│   │   ├── session_manager.py   # 会话管理
│   │   └── mcp_tools.py         # MCP 工具配置
│   ├── tools/          # MCP 工具服务器
│   │   ├── weather_mcp_server.py    # 天气工具
│   │   └── itinerary_mcp_server.py  # 行程规划工具
│   ├── api/            # FastAPI 应用
│   │   └── main.py              # API 主程序
│   └── utils/          # 工具模块
│       ├── info.py              # 配置管理
│       └── pretty.py            # 日志系统
```

### 前端架构
```
frontend/
├── app/                # Next.js App Router
│   ├── page.tsx                 # 主页面
│   ├── layout.tsx               # 应用布局
│   └── globals.css              # 全局样式
└── components/         # React 组件
    ├── TravelAssistant.tsx      # 主要聊天界面
    ├── Header.tsx               # 应用头部
    └── Welcome.tsx              # 欢迎页面
```

## 🚀 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- 百度地图 API Key（推荐）
- OpenAI API Key 或兼容的 API 服务

### 1. 克隆项目

```bash
git clone https://github.com/your-username/travel-assistant-agent.git
cd travel-assistant-agent
```

### 2. 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -e .

# 配置环境变量
cp env.example .env
# 编辑 .env 文件，填入你的 API Keys
```

环境变量配置 (`.env`):
```env
# OpenAI/LLM Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
DEFAULT_MODEL_NAME=gpt-4o-mini

# 百度地图 API 配置
# 在 https://lbsyun.baidu.com/ 申请 AK
BAIDU_MAP_API_KEY=your_baidu_map_api_key_here

# 天气 API 配置 (可选)
# 在 https://openweathermap.org/api 申请 API Key
WEATHER_API_KEY=your_weather_api_key_here
```

### 3. 前端设置

```bash
cd frontend

# 安装依赖
npm install
```

### 4. 启动服务

**启动后端服务:**
```bash
cd backend
python src/api/main.py
```
后端将在 http://localhost:8000 启动

**启动前端服务:**
```bash
cd frontend
npm run dev
```
前端将在 http://localhost:3000 启动

### 5. 开始使用

访问 http://localhost:3000，开始与智能旅行助手对话！

## 🔧 API 文档

### REST API 端点

- `POST /api/sessions` - 创建新会话
- `GET /api/sessions` - 获取所有会话
- `GET /api/sessions/{session_id}` - 获取特定会话
- `DELETE /api/sessions/{session_id}` - 删除会话
- `POST /api/plan` - 旅行规划（同步）
- `GET /api/health` - 健康检查

### WebSocket 接口

- `ws://localhost:8000/ws/{session_id}` - 实时对话接口

消息格式:
```json
{
  "type": "travel_request",
  "content": "我想在杭州玩3天"
}
```

## 🛠️ MCP 工具

### 百度地图工具 (百度地图 MCP Server)
- `map_geocode` - 地址解析为坐标
- `map_reverse_geocode` - 坐标解析为地址  
- `map_search_places` - 搜索地点信息
- `map_search_nearby` - 周边地点搜索
- `map_place_detail` - 获取地点详情
- `map_direction` - 路线规划
- `map_distance` - 距离计算
- `map_ip_location` - IP定位
- `map_coordinate_convert` - 坐标转换
- `map_static_image` - 静态地图

### 天气工具 (weather_mcp_server.py)
- `get_current_weather` - 当前天气
- `get_weather_forecast` - 天气预报
- `get_weather_alerts` - 天气提醒

### 行程规划工具 (itinerary_mcp_server.py)
- `plan_itinerary` - 多日行程规划
- `optimize_route` - 路线优化
- `suggest_activities` - 活动推荐
- `calculate_budget` - 预算估算

## 💡 使用示例

### 基本旅行规划
```
用户: "我想在杭州玩3天，预算5000元，喜欢文化古迹和美食"

助手: 我来为您规划杭州3天的文化美食之旅！

[调用百度地图工具获取杭州景点信息...]
[调用天气工具获取天气预报...]
[调用行程规划工具生成行程安排...]

为您推荐以下行程：

第一天：西湖文化之旅
- 上午：西湖十景游览（断桥残雪、苏堤春晓）
- 下午：岳王庙、灵隐寺
- 晚上：河坊街品尝杭州小吃

第二天：历史文化深度游
...
```

### 亲子旅游规划
```
用户: "帮我规划一个北京周末两日游，重点是亲子活动"

助手: 为您推荐适合亲子的北京两日游行程：

第一天：科技与自然
- 上午：中国科技馆（互动展览）
- 下午：北京动物园（熊猫馆）
- 晚上：王府井步行街

第二天：历史与文化
...
```

## 🔄 开发流程

### 添加新的 MCP 工具

1. 在 `backend/src/tools/` 创建新的工具服务器
2. 在 `TravelMcpTools` 类中添加工具配置
3. 更新 Agent 的系统提示词
4. 测试工具功能

### 自定义 Agent 行为

修改 `backend/src/core/travel_agent.py` 中的系统提示词和处理逻辑。

### 前端组件开发

在 `frontend/components/` 中添加新组件，使用 Tailwind CSS 进行样式设计。

## 🐛 故障排除

### 常见问题

1. **MCP 工具连接失败**
   - 检查 Python 路径和依赖安装
   - 确认 API Keys 配置正确

2. **WebSocket 连接断开**
   - 检查网络连接
   - 重启后端服务

3. **API 调用限制**
   - 检查 API Key 额度
   - 考虑使用备用 API 服务

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系

如有问题，请提交 GitHub Issue 或联系开发团队。

---

**注意**: 
- 本项目使用百度地图 MCP Server，这是国内首家兼容 MCP 协议的地图服务商
- 百度地图 API 需要在 [百度地图开放平台](https://lbsyun.baidu.com/) 申请 AK
- 在生产环境中使用前，请确保进行充分的测试和安全评估

## 🔗 相关链接

- [百度地图 MCP Server](https://github.com/baidu-maps/mcp)
- [百度地图开放平台](https://lbsyun.baidu.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
