# ===== 语音日历 API =====
# 运行方式：uvicorn main:app --reload
# API 文档：http://localhost:8000/docs

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from models import Event
from speech import recognize_audio

# ---- 启动时自动创建数据库表 ----
Base.metadata.create_all(bind=engine)

# ---- FastAPI 应用 ----
app = FastAPI(
    title="语音日历 API",
    description="语音日程管理助手的后端服务",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# 健康检查
# ============================================

@app.get("/")
def root():
    return {"status": "ok", "message": "语音日历 API 运行中 🎙️"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ============================================
# 语音识别接口（PR4 核心）
# ============================================

@app.post("/speech/recognize")
async def speech_recognize(audio: UploadFile = File(...)):
    """接收音频文件，调用讯飞 API 识别，返回文字

    前端调用方式：
    const formData = new FormData()
    formData.append("audio", audioBlob, "recording.wav")
    fetch("http://localhost:8000/speech/recognize", { method: "POST", body: formData })

    返回格式：
    { "text": "明天下午三点开会", "success": true }
    """
    # 1. 读取前端上传的音频文件
    audio_bytes = await audio.read()

    # 2. 检查文件大小（讯飞限制 60 秒内的音频，预计不超过 10MB）
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="音频文件为空")

    if len(audio_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="音频文件过大（最大10MB）")

    # 3. 调用讯飞识别
    try:
        text = await recognize_audio(audio_bytes)
        return {"text": text, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 事件接口（占位，完整实现在 PR3 之后）
# ============================================

@app.get("/events")
def list_events():
    return {"count": 0, "events": [], "hint": "完整 CRUD 将在 PR3 中实现"}
