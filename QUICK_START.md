# 🚀 快速启动指南

## 前置条件

- Python 3.8+
- Node.js 16+
- OpenAI API Key (或兼容 API)
- 百度地图 API Key (推荐，在 https://lbsyun.baidu.com/ 申请)

## 启动方法

### 方法一：使用脚本自动启动（推荐）

1. **启动后端服务**（新建终端窗口）
```bash
chmod +x run_backend.sh
./run_backend.sh
```

2. **启动前端应用**（新建终端窗口）
```bash
chmod +x run_frontend.sh
./run_frontend.sh
```

### 方法二：手动启动

#### 后端服务启动

1. 进入后端目录
```bash
cd backend
```

2. 创建并激活虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -e .
```

4. 配置环境变量
```bash
cp env.example .env
# 编辑 .env 文件，填入 API Keys
```

5. 启动服务
```bash
python src/api/main.py
```

#### 前端应用启动

1. 进入前端目录（新终端窗口）
```bash
cd frontend
```

2. 安装依赖
```bash
npm install
```

3. 启动开发服务器
```bash
npm run dev
```

## 访问应用

- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

## API 配置

编辑 `backend/.env` 文件：

```env
# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
DEFAULT_MODEL_NAME=gpt-4o-mini

# 百度地图 API 配置
# 在 https://lbsyun.baidu.com/ 申请 AK
BAIDU_MAP_API_KEY=your_baidu_map_api_key_here

# 天气 API 配置（可选）
# 在 https://openweathermap.org/api 申请 API Key
WEATHER_API_KEY=your_weather_api_key_here
```

## 百度地图 MCP Server 功能

✨ **核心功能**：
- 🗺️ 地理编码：地址 ↔ 坐标转换
- 🔍 地点搜索：智能搜索景点、餐厅、酒店
- 📍 周边搜索：基于位置的附近地点发现
- 🛣️ 路线规划：多种交通方式的路径计算
- 📊 距离计算：精确的距离和时间估算
- 🏢 地点详情：详细的商家信息查询

## 使用示例

启动应用后，您可以尝试以下问题：

- "我想在杭州玩3天，预算5000元，喜欢文化古迹和美食"
- "帮我规划一个北京周末两日游，重点是亲子活动"
- "我要去上海出差，顺便旅游一天，推荐路线"
- "从北京到上海的最佳路线是什么？"
- "帮我找一下西湖附近的特色餐厅"

## 故障排除

### 后端启动失败
- 检查 Python 版本：`python --version`
- 检查 API Keys 配置
- 确认百度地图 API Key 有效且已开通相关服务
- 查看终端错误信息

### 前端启动失败
- 检查 Node.js 版本：`node --version`
- 清除缓存：`rm -rf node_modules package-lock.json && npm install`

### API 调用失败
- 验证 OpenAI API Key 是否有效
- 检查百度地图 API Key 配置和额度
- 确认网络连接正常
- 检查 API 调用权限

### 百度地图相关问题
- 确认在百度地图开放平台启用了所需服务
- 检查 API 调用次数是否超限
- 验证 AK 的域名和 IP 白名单设置

## 开发模式

- 后端会在文件更改时自动重启
- 前端支持热重载
- 查看 `http://localhost:8000/docs` 获取 API 文档
- 百度地图 MCP Server 支持所有标准 MCP 协议功能

## 相关文档

- [百度地图 MCP Server 文档](https://github.com/baidu-maps/mcp)
- [百度地图开放平台](https://lbsyun.baidu.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)

现在您可以开始使用基于百度地图的智能旅行助手了！🎉 