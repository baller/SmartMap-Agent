import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 项目根目录
PROJECT_ROOT_DIR = Path(__file__).parent.parent.parent

# LLM 配置
DEFAULT_MODEL_NAME = os.environ.get("DEFAULT_MODEL_NAME", "gpt-4o-mini")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("SILICONFLOW_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL") or os.environ.get("SILICONFLOW_BASE_URL", "https://api.openai.com/v1")

# Google Maps 配置
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

# 天气 API 配置
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")

# FastAPI 配置
PORT = int(os.environ.get("PORT", 8000))
HOST = os.environ.get("HOST", "0.0.0.0")

# CORS 配置
CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

# 会话配置
MAX_SESSIONS = int(os.environ.get("MAX_SESSIONS", 100))
SESSION_TIMEOUT = int(os.environ.get("SESSION_TIMEOUT", 3600))

# 代理配置
USE_CN_MIRROR = bool(os.environ.get("USE_CN_MIRROR"))
PROXY_URL = os.environ.get("PROXY_URL") 