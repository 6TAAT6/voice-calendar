# ===== 讯飞语音听写 IAT v2 WebSocket =====
# 使用讯飞语音听写 v2 WebSocket API，支持 ≤60 秒短音频
# 文档：https://www.xfyun.cn/doc/asr/voicedictation/API.html
#
# 认证方式（HMAC-SHA256 签名）：
#   1. 构造签名原文: "host: {host}\ndate: {rfc1123_date}\nGET /v2/iat HTTP/1.1"
#   2. HMAC-SHA256 用 APISecret 签名 → Base64
#   3. 拼接 authorization_origin → 整体 Base64 → 放 URL 参数
#
# 发送格式：JSON 帧，status=0 首帧 / 1 中间帧 / 2 末帧

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

from config import XUNFEI

# 讯飞语音听写 v2 WebSocket 地址
IAT_WS_URL = "wss://ws-api.xfyun.cn/v2/iat"

# 分帧发送参数
FRAME_SIZE = 8000     # 每帧字节数
STATUS_FIRST = 0      # 首帧
STATUS_CONT = 1       # 中间帧
STATUS_LAST = 2       # 末帧


def _build_url() -> str:
    """构建带鉴权签名的 WebSocket URL

    签名流程：
    1. 构造签名原文 (host + date + request-line)
    2. HMAC-SHA256(APISecret, 签名原文) → Base64 得到 signature
    3. 拼接 authorization_origin → 整体 Base64 得到 authorization
    4. 参数拼接到 URL
    """
    app_id = XUNFEI["app_id"]
    api_key = XUNFEI["api_key"]
    api_secret = XUNFEI["api_secret"]

    # 检查配置
    if app_id == "你的APPID":
        raise ValueError("请先在 backend/config.py 配置讯飞 AppID/APIKey/APISecret")

    # RFC 1123 时间
    now = datetime.now()
    date_rfc = format_date_time(mktime(now.timetuple()))

    # 步骤 1: 构造签名原文
    host = "ws-api.xfyun.cn"
    path = "/v2/iat"
    signature_origin = f"host: {host}\ndate: {date_rfc}\nGET {path} HTTP/1.1"

    # 步骤 2: HMAC-SHA256 签名 → Base64
    signature_sha = hmac.new(
        api_secret.encode("utf-8"),
        signature_origin.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    signature_b64 = base64.b64encode(signature_sha).decode("utf-8")

    # 步骤 3: 拼接 authorization 原文 → Base64
    authorization_origin = (
        f'api_key="{api_key}", '
        f'algorithm="hmac-sha256", '
        f'headers="host date request-line", '
        f'signature="{signature_b64}"'
    )
    authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")

    # 步骤 4: 拼接 URL
    params = {
        "authorization": authorization,
        "date": date_rfc,
        "host": host,
    }
    return f"{IAT_WS_URL}?{urlencode(params)}"


def _send_audio_frames(ws, audio_data: bytes):
    """将音频分帧发送（在后台线程中调用，避免阻塞 WebSocket 事件循环）

    发送模式：status=0(首帧) → 1(中间帧) → 2(末帧)
    每帧间隔 40ms，给服务器留处理时间
    末帧发送后等待 2 秒让服务器返回结果，然后关闭连接
    """
    total = len(audio_data)
    offset = 0
    status = STATUS_FIRST

    while True:
        buf = audio_data[offset : offset + FRAME_SIZE]
        is_last = offset + FRAME_SIZE >= total
        offset += FRAME_SIZE

        if status == STATUS_FIRST:
            # 首帧：包含 common + business 参数
            frame = {
                "common": {"app_id": XUNFEI["app_id"]},
                "business": {
                    "domain": "iat",
                    "language": "zh_cn",
                    "accent": "mandarin",
                    "vad_eos": 10000,
                },
                "data": {
                    "status": STATUS_FIRST,
                    "format": "audio/L16;rate=16000",
                    "encoding": "raw",
                    "audio": base64.b64encode(buf).decode("utf-8"),
                },
            }
            ws.send(json.dumps(frame))
            status = STATUS_CONT

        elif status == STATUS_CONT and not is_last:
            # 中间帧
            frame = {
                "data": {
                    "status": STATUS_CONT,
                    "format": "audio/L16;rate=16000",
                    "encoding": "raw",
                    "audio": base64.b64encode(buf).decode("utf-8"),
                }
            }
            ws.send(json.dumps(frame))

        else:
            # 末帧（最后一个数据块）
            frame = {
                "data": {
                    "status": STATUS_LAST,
                    "format": "audio/L16;rate=16000",
                    "encoding": "raw",
                    "audio": base64.b64encode(buf).decode("utf-8"),
                }
            }
            ws.send(json.dumps(frame))
            break

        # 帧间隔，避免服务器来不及处理
        time.sleep(0.04)


def _collect_result(message: str, result_container: list) -> bool:
    """解析返回消息，提取识别文字。

    返回 True 表示应该关闭连接（code=2 服务器端通知关闭）
    """
    try:
        msg = json.loads(message)
    except json.JSONDecodeError:
        return False

    code = msg.get("code", -1)

    if code == 0:
        # 正常识别结果
        data = msg.get("data", {})
        result = data.get("result", {})
        ws_list = result.get("ws", [])
        for item in ws_list:
            for w in item.get("cw", []):
                result_container.append(w.get("w", ""))
        return False

    elif code == 2:
        # 服务端主动关闭——收集最终结果后关闭
        data = msg.get("data", {})
        if data:
            result = data.get("result", {})
            ws_list = result.get("ws", [])
            for item in ws_list:
                for w in item.get("cw", []):
                    result_container.append(w.get("w", ""))
        return True  # 通知调用方关闭连接

    else:
        # 错误
        err_msg = msg.get("message", f"未知错误 code={code}")
        raise Exception(f"讯飞识别失败: {err_msg}")


def recognize_sync(audio_data: bytes) -> str:
    """同步版本：发送音频到讯飞语音听写，返回识别文字

    参数：
        audio_data: 原始 PCM 音频字节（16kHz, 16bit, 单声道）

    返回：
        识别出的文字字符串
    """
    result_chunks = []    # 收集所有识别片段
    error = [None]        # 存放错误信息
    finished = [False]    # 标记是否完成
    ws_app = [None]       # 存放 WebSocketApp 实例

    def on_open(ws):
        """WebSocket 连接成功，在新线程中发送音频帧"""

        def send_audio():
            try:
                _send_audio_frames(ws, audio_data)
                # 等待服务器返回识别结果（通常 1-2 秒）
                time.sleep(2)
                ws.close()
            except Exception as e:
                error[0] = e
                ws.close()

        _thread.start_new_thread(send_audio, ())

    def on_message(ws, message):
        """接收识别结果"""
        try:
            # 忽略心跳等非 JSON 消息
            if not message.strip().startswith("{"):
                return
            if _collect_result(message, result_chunks):
                finished[0] = True
                ws.close()
        except Exception as e:
            error[0] = e
            ws.close()

    def on_error(ws, err):
        """WebSocket 错误"""
        if isinstance(err, ConnectionRefusedError):
            error[0] = Exception(f"无法连接到讯飞服务器，请检查网络")
        elif isinstance(err, Exception):
            error[0] = err
        else:
            error[0] = Exception(str(err))

    def on_close(ws, close_code, close_msg):
        """WebSocket 关闭"""
        finished[0] = True

    # 构建鉴权 URL
    ws_url = _build_url()

    # 创建 WebSocket 连接
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws_app[0] = ws

    # 启动 WebSocket（阻塞直到完成，忽略 SSL 证书验证）
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    # 检查是否出错
    if error[0]:
        raise error[0]

    # 拼接所有识别片段
    text = "".join(result_chunks).strip()

    # 去掉句末标点
    text = text.rstrip("。，！？；：、,.!?;:")

    return text


async def recognize_audio(audio_data: bytes) -> str:
    """异步包装——让同步 WebSocket 在后台线程运行，不阻塞 FastAPI 事件循环

    参数：
        audio_data: 音频文件的二进制数据（WAV/PCM格式，16kHz, 16bit, 单声道）

    返回：
        识别出的中文文字字符串
    """
    import asyncio

    # 在线程池中执行同步 WebSocket 调用
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, recognize_sync, audio_data)
