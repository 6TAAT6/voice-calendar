# ===== 讯飞语音识别模块（v1 REST API）=====
# 使用讯飞语音听写接口，支持 ≤60 秒短音频
# 文档：https://www.xfyun.cn/doc/asr/voicedictation/API.html
#
# 认证方式：
#   X-Appid: APPID
#   X-CurTime: 当前UTC时间戳（秒）
#   X-Param: Base64(JSON参数)
#   X-CheckSum: MD5(APIKey + X-CurTime + X-Param)
#
# 请求体：audio=<Base64编码的音频>

import hashlib
import base64
import json
import time
import httpx
from config import XUNFEI, XUNFEI_ASR_URL


async def recognize_audio(audio_data: bytes) -> str:
    """发送音频到讯飞，返回识别文字

    参数：
        audio_data: 音频文件的二进制数据（WAV/PCM格式，16kHz, 16bit, 单声道）

    返回：
        识别出的中文文字字符串
    """
    app_id = XUNFEI["app_id"]
    api_key = XUNFEI["api_key"]

    # 检查是否已配置
    if app_id == "你的APPID":
        return "[未配置讯飞API，请在 backend/config.py 中填入你的 AppID/APIKey/APISecret]"

    # ---- Step 1: 构造 X-Param ----
    # 告诉讯飞：音频格式是 16kHz 原始 PCM，引擎用 sms16k
    param = {
        "engine_type": "sms16k",  # 16kHz 通用引擎
        "aue": "raw",              # 音频编码：raw = 未压缩 PCM
    }
    x_param = base64.b64encode(
        json.dumps(param, separators=(",", ":")).encode()
    ).decode()

    # ---- Step 2: 计算签名 ----
    # X-CheckSum = MD5(APIKey + 当前UTC秒 + X-Param)
    x_time = str(int(time.time()))
    raw_sign = f"{api_key}{x_time}{x_param}"
    x_checksum = hashlib.md5(raw_sign.encode()).hexdigest()

    # ---- Step 3: 发送请求 ----
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "X-Appid": app_id,
        "X-CurTime": x_time,
        "X-Param": x_param,
        "X-CheckSum": x_checksum,
    }

    # 音频 Base64 编码
    audio_base64 = base64.b64encode(audio_data).decode()
    body = {"audio": audio_base64}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            XUNFEI_ASR_URL,
            headers=headers,
            data=body,
        )

    # ---- Step 4: 解析结果 ----
    result = response.json()
    # 调试时可取消注释：
    # print("讯飞返回:", json.dumps(result, ensure_ascii=False, indent=2))

    # code=0 表示成功
    if result.get("code") == "0":
        data = result.get("data", {})
        text = data.get("text", "")
        # 去掉末尾的句号（讯飞习惯）
        return text.rstrip("。").strip()
    else:
        err_msg = result.get("desc", result.get("message", "未知错误"))
        raise Exception(f"讯飞识别失败 (code={result.get('code')}): {err_msg}")
