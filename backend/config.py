# ===== 语音日历 — 配置文件 =====
# 密钥通过 .env 文件管理（.env 不会被提交到 git）
# 如果 .env 不存在，从这里读取默认值（方便开发调试）
#
# 使用方式：
#   cp .env.example .env
#   编辑 .env 填入真实密钥
import os
from pathlib import Path

from dotenv import load_dotenv

# 自动加载 backend/.env（如果存在）
_env_path = Path(__file__).parent / ".env"
load_dotenv(_env_path)


# ===== 讯飞语音听写配置 =====
# 获取步骤：https://console.xfyun.cn/ → 我的应用 → 语音听写
XUNFEI = {
    "app_id": os.getenv("XUNFEI_APP_ID", "你的APPID"),
    "api_key": os.getenv("XUNFEI_API_KEY", ""),
    "api_secret": os.getenv("XUNFEI_API_SECRET", ""),
}

# 讯飞语音听写 v2 WebSocket 地址
# 文档：https://www.xfyun.cn/doc/asr/voicedictation/API.html
XUNFEI_ASR_URL = "wss://ws-api.xfyun.cn/v2/iat"

# 讯飞语音合成 TTS v2 WebSocket 地址
# 文档：https://www.xfyun.cn/doc/tts/online_tts/API.html
XUNFEI_TTS_URL = "wss://tts-api.xfyun.cn/v2/tts"


# ===== DeepSeek 大模型配置（语义解析）=====
# 获取步骤：https://platform.deepseek.com/ → API Keys
DEEPSEEK = {
    "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
    "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
}

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
