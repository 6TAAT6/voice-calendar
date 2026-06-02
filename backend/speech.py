# ===== 讯飞语音识别模块 =====
# 流程：
#   1. 接收前端发来的音频文件(.wav)
#   2. 计算签名 → 上传到讯飞 API
#   3. 返回识别出的文字

import hashlib
import hmac
import base64
import time
import httpx
from config import XUNFEI, XUNFEI_ASR_URL


def _build_signature(app_id: str, api_secret: str, timestamp: str) -> str:
    """计算讯飞 API 所需的签名

    签名算法：HMAC-SHA256(api_secret, app_id + timestamp)
    然后 Base64 编码

    类比：就像密码盐加密，确保请求来自合法用户
    """
    raw = f"{app_id}{timestamp}"
    h = hmac.new(
        api_secret.encode("utf-8"),
        raw.encode("utf-8"),
        hashlib.sha256,
    )
    return base64.b64encode(h.digest()).decode("utf-8")


async def recognize_audio(audio_data: bytes) -> str:
    """发送音频到讯飞，返回识别文字

    参数：
        audio_data: 音频文件的二进制数据

    返回：
        识别出的中文文字字符串
        如果识别失败，返回空字符串

    异常：
        各种网络/API 错误都会抛出，由调用方处理
    """
    app_id = XUNFEI["app_id"]
    api_key = XUNFEI["api_key"]
    api_secret = XUNFEI["api_secret"]

    # 检查是否已配置
    if app_id == "你的APPID":
        return "[未配置讯飞API，请在 backend/config.py 中填入你的 AppID/APIKey/APISecret]"

    # 生成时间戳（秒）
    timestamp = str(int(time.time()))

    # 计算签名
    signature = _build_signature(app_id, api_secret, timestamp)

    # 构造 multipart/form-data 请求
    # files = { "file": ("audio.wav", audio_data, "audio/wav") }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            XUNFEI_ASR_URL,
            data={
                "app_id": app_id,
                "ts": timestamp,
                "signa": signature,
            },
            files={
                "file": ("audio.wav", audio_data, "audio/wav"),
            },
        )

    # 解析返回结果
    result = response.json()
    # print("讯飞返回:", result)  # 调试时可以取消注释

    # 提取识别文字
    # 讯飞返回格式: {"code": 0, "data": {"text": "明天下午三点开会"}, ...}
    if result.get("code") == 0 and "data" in result:
        return result["data"].get("text", "")
    else:
        # 识别失败，返回错误信息
        err_msg = result.get("desc", result.get("message", "未知错误"))
        raise Exception(f"讯飞识别失败: {err_msg}")
