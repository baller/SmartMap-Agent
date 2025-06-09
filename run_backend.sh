#!/bin/bash

echo "🚀 启动智能旅行助手后端服务"

# 检查是否在正确目录
if [ ! -d "backend" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 进入后端目录
cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📦 安装依赖..."
pip install -e .

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "⚠️  创建环境变量文件..."
    cp env.example .env
    echo "请编辑 .env 文件，填入你的 API Keys："
    echo "- OPENAI_API_KEY (必需)"
    echo "- BAIDU_MAP_API_KEY (推荐，在 https://lbsyun.baidu.com/ 申请)"
    echo "- WEATHER_API_KEY (可选，在 https://openweathermap.org/api 申请)"
    echo ""
    echo "✨ 百度地图 MCP Server 功能："
    echo "  - 地理编码和逆地理编码"
    echo "  - 地点检索和详情查询"
    echo "  - 路线规划和距离计算"
    echo "  - 周边搜索和坐标转换"
    echo ""
    read -p "配置完成后按 Enter 继续..."
fi

# 启动服务
echo "🌟 启动 FastAPI 服务..."
echo "🗺️  使用百度地图 MCP Server 提供地图服务"
python src/api/main.py 