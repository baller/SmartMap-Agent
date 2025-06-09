#!/bin/bash

echo "🎨 启动智能旅行助手前端应用"

# 检查是否在正确目录
if [ ! -d "frontend" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 进入前端目录
cd frontend

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 启动开发服务器
echo "🌐 启动 Next.js 开发服务器..."
npm run dev 