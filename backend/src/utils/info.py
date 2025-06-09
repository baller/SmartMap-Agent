"""
Configuration and Information for Travel Assistant
旅行助手的配置信息
"""

import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
DEFAULT_MODEL_NAME = os.environ.get("DEFAULT_MODEL_NAME", "gpt-4o-mini")

# 百度地图 API 配置
BAIDU_MAP_API_KEY = os.environ.get("BAIDU_MAP_API_KEY", "")

# Weather API Configuration
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "")

# FastAPI Configuration
HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", 8000))

# CORS Configuration
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
]

# Session Management Configuration
MAX_SESSIONS = int(os.environ.get("MAX_SESSIONS", 100))
SESSION_TIMEOUT = int(os.environ.get("SESSION_TIMEOUT", 3600))  # 1 hour

# Project Paths
PROJECT_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# API URLs and Endpoints
API_DOCS_URL = "/docs"
API_HEALTH_URL = "/api/health" 