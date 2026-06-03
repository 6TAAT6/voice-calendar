# ===== 讯飞语音合成 TTS v2 WebSocket =====
# 把文字转成语音，用于：
#   - 创建事件后的语音反馈（"已为您创建明天下午三点的产品评审会"）
#   - 每日日程播报
# 文档：https://www.xfyun.cn/doc/tts/online_tts/API.html
#
# 鉴权方式和语音听写 IAT 完全一致：HMAC-SHA256 → Base64 → URL 参数

import base64
import hashlib
import hmac
import json
import ssl
import time
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

import websocket
import _thread

from config import XUNFEI, XUNFEI_TTS_URL

# 发音人：aisxping = 小萍（女声，亲切自然）
DEFAULT_VOICE = "aisxping"


def _build_url() -> str:
    """构建 TTS WebSocket 鉴权 URL（和 IAT 一样的签名流程）"""
    api_key = XUNFEI["api_key"]
    api_secret = XUNFEI["api_secret"]

    host = "tts-api.xfyun.cn"
    path = "/v2/tts"

    now = datetime.now()
    date_rfc = format_date_time(mktime(now.timetuple()))

    signature_origin = f"host: {host}\ndate: {date_rfc}\nGET {path} HTTP/1.1"

    signature_sha = hmac.new(
        api_secret.encode("utf-8"),
        signature_origin.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    signature_b64 = base64.b64encode(signature_sha).decode("utf-8")

    authorization_origin = (
        f'api_key="{api_key}", '
        f'algorithm="hmac-sha256", '
        f'headers="host date request-line", '
        f'signature="{signature_b64}"'
    )
    authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")

    params = {
        "authorization": authorization,
        "date": date_rfc,
        "host": host,
    }
    return f"{XUNFEI_TTS_URL}?{urlencode(params)}"


def _synthesize_sync(text: str, voice: str = DEFAULT_VOICE) -> bytes:
    """同步：发送文字到讯飞 TTS，返回 MP3 音频字节

    参数：
        text: 要合成的文字（≤2000 汉字）
        voice: 发音人，默认 aisxping（小萍）

    返回：
        MP3 音频数据
    """
    audio_chunks = []      # 收集音频片段
    error = [None]         # 错误信息
    finished = [False]     # 完成标记

    def on_open(ws):
        """连接成功 → 发送合成请求"""
        # 语音合成是一次性发送文本，status=2 表示最后一帧
        text_b64 = base64.b64encode(text.encode("utf-8")).decode("utf-8")

        frame = {
            "common": {"app_id": XUNFEI["app_id"]},
            "business": {
                "aue": "lame",             # MP3 格式（体积小，浏览器直接播放）
                "sfl": 1,                   # 流式返回
                "auf": "audio/L16;rate=16000",
                "vcn": voice,               # 发音人
                "tte": "utf8",
            },
            "data": {
                "status": 2,                # 2 = 最后一帧（文本一次性发完）
                "text": text_b64,
            },
        }
        ws.send(json.dumps(frame))

    def on_message(ws, message):
        """接收音频数据"""
        try:
            msg = json.loads(message)
        except json.JSONDecodeError:
            return

        code = msg.get("code", -1)

        if code == 0:
            data = msg.get("data", {})
            audio_b64 = data.get("audio", "")
            if audio_b64:
                audio_chunks.append(base64.b64decode(audio_b64))
            # status=2 表示传输完成
            if data.get("status") == 2:
                finished[0] = True
                ws.close()
        else:
            err_msg = msg.get("message", f"TTS 错误 code={code}")
            error[0] = Exception(f"讯飞语音合成失败: {err_msg}")
            ws.close()

    def on_error(ws, err):
        if not error[0]:
            error[0] = Exception(f"TTS WebSocket 错误: {err}")

    def on_close(ws, close_code, close_msg):
        finished[0] = True

    ws_url = _build_url()
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    if error[0]:
        raise error[0]

    return b"".join(audio_chunks)


async def synthesize(text: str, voice: str = DEFAULT_VOICE) -> bytes:
    """异步包装：把文字转为 MP3 音频

    参数：
        text: 要合成的文字
        voice: 发音人，默认 aisxping

    返回：
        MP3 音频字节
    """
    import asyncio
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _synthesize_sync, text, voice)


# ===== 常用语音模板 =====

def build_feedback_text(title: str, event_time: str) -> str:
    """生成创建成功的语音反馈文本"""
    try:
        dt = datetime.fromisoformat(event_time)
        time_str = dt.strftime("%m月%d日 %H点%M分")
    except (ValueError, TypeError):
        time_str = event_time
    return f"已为您创建{time_str}的{title}"


def build_daily_brief_text(events: list) -> str:
    """生成每日日程播报文本"""
    today = datetime.now().strftime("%m月%d日")
    if not events:
        return f"今天是{today}，您今天没有日程安排。"

    count = len(events)
    if count == 1:
        e = events[0]
        return f"今天是{today}，您有{count}个日程：{e['title']}。"
    elif count <= 3:
        parts = "、".join(e["title"] for e in events)
        return f"今天是{today}，您有{count}个日程：{parts}。"
    else:
        return f"今天是{today}，您有{count}个日程，比较忙哦。"
