# ===== 语音日历 API — 完整功能 =====
# PR8: 加入语音合成 + 冲突检测 + AI 对话修正
# 运行：uvicorn main:app --reload    或    ../start.bat
# 文档：http://localhost:8000/docs

from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import engine, Base, get_db
from models import Event
from speech import recognize_audio
from nlp_parser import parse_schedule, nlp_correct
from tts import synthesize, build_feedback_text, build_daily_brief_text


# ---- 请求/响应模型 ----
class ParseRequest(BaseModel):
    text: str = Field(..., min_length=1, description="用户说的话")


class CorrectRequest(BaseModel):
    """AI 对话修正：用户对上一次识别结果说"不对，改成xxx" """
    original_text: str = Field(..., min_length=1, description="上一次识别/解析的文字")
    correction_text: str = Field(..., min_length=1, description="用户说的修正指令")


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500, description="要合成的文字")
    voice: str = Field(default="aisxping", description="发音人")


class EventCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    event_time: str = Field(..., description="ISO 格式: yyyy-MM-ddTHH:mm:ss")
    event_type: str = Field(default="其他")
    description: str = Field(default="")
    remind: bool = Field(default=True)
    force_create: bool = Field(default=False, description="忽略冲突警告，强制创建")


# ---- 启动时创建数据库表 ----
Base.metadata.create_all(bind=engine)

# ---- FastAPI 应用 ----
app = FastAPI(
    title="语音日历 API",
    description="语音日程管理 — 语音识别 + 语义解析 + 事件管理",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# 全局异常处理 — 统一错误格式
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc)},
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
# 语音识别（PR4）
# ============================================

@app.post("/speech/recognize")
async def speech_recognize(request: Request):
    """接收 PCM 音频（16kHz/16bit/单声道）→ 讯飞识别 → 返回文字

    前端发送格式：Content-Type: application/octet-stream, body = raw PCM bytes
    音频要求：16kHz 采样率, 16bit, 单声道（前端 Web Audio API 已转换好）
    """
    audio_bytes = await request.body()

    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="音频数据为空")
    if len(audio_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="音频文件过大（最大10MB）")

    try:
        text = await recognize_audio(audio_bytes)
        return {"text": text, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# NLP 语义解析（PR5 核心）
# ============================================

@app.post("/nlp/parse")
async def nlp_parse(req: ParseRequest):
    """将自然语言文字解析为结构化日程

    输入: { "text": "明天下午三点开产品评审会" }
    输出: { "title": "产品评审会", "event_time": "2026-06-04T15:00:00", ... }

    背后调用 DeepSeek 大模型理解自然语言
    """
    # 当前日期时间 → 帮助 DeepSeek 计算"明天""下周五"等
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    try:
        result = await parse_schedule(req.text, current_datetime=now)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 语音合成 TTS（PR8 新功能）
# ============================================

@app.post("/speech/synthesize")
async def speech_synthesize(req: SynthesizeRequest):
    """文字转语音 → 返回 MP3 音频流

    输入: { "text": "已为您创建明天下午三点的产品评审会" }
    返回: MP3 二进制数据（Content-Type: audio/mpeg）
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="合成文本为空")

    try:
        audio_bytes = await synthesize(req.text, req.voice)
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"X-Speech-Text": req.text[:100]},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# AI 对话修正（PR8 新功能 — 核心亮点）
# ============================================

@app.post("/nlp/correct")
async def nlp_correct_endpoint(req: CorrectRequest):
    """用户说"不对，改成xxx" → DeepSeek 理解修正语义 → 返回修正后的结构化日程

    工作流程：
      1. 用户第一次录音："明天下午开会" → 识别文字
      2. 用户觉得不对，点击修正按钮，说："改成后天上午十点开产品评审会"
      3. 后端把两段文字一起发给 DeepSeek，让它理解"修正"的意图
      4. 返回修正后的完整结构化日程

    输入:
      { "original_text": "明天下午开会",
        "correction_text": "改成后天上午十点开产品评审会" }

    输出:
      { "title": "产品评审会", "event_time": "2026-06-05T10:00:00", ... }
    """
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    try:
        result = await nlp_correct(
            original_text=req.original_text,
            correction_text=req.correction_text,
            current_datetime=now,
        )
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 事件 CRUD（PR3 核心功能）
#   PR8: 增加冲突检测 + 重复检测
# ============================================

@app.post("/events", status_code=201)
def create_event(req: EventCreateRequest, db: Session = Depends(get_db)):
    """创建事件（含智能冲突检测）

    如果检测到冲突或重复，返回 warnings 列表 + should_confirm=true
    前端可以显示警告，让用户确认后再调用 force_create=true 强制创建
    """
    event_time = datetime.fromisoformat(req.event_time)
    warnings = []

    # ---- 检测：完全重复（相同标题 + 相同日期）----
    same_date_start = event_time.replace(hour=0, minute=0, second=0)
    same_date_end = same_date_start + timedelta(days=1)
    existing_same_day = (
        db.query(Event)
        .filter(
            Event.title == req.title,
            Event.event_time >= same_date_start,
            Event.event_time < same_date_end,
        )
        .first()
    )
    if existing_same_day:
        warnings.append({
            "type": "duplicate",
            "message": f"当天已有「{req.title}」（{existing_same_day.event_time.strftime('%H:%M')}），建议修改标题或删除旧事件",
            "conflict_event_id": existing_same_day.id,
        })

    # ---- 检测：时间冲突（前后 30 分钟内已有事件）----
    conflict_window = timedelta(minutes=30)
    nearby_start = event_time - conflict_window
    nearby_end = event_time + conflict_window
    conflicting = (
        db.query(Event)
        .filter(
            Event.id != (existing_same_day.id if existing_same_day else 0),
            Event.event_time >= nearby_start,
            Event.event_time <= nearby_end,
        )
        .first()
    )
    if conflicting:
        warnings.append({
            "type": "conflict",
            "message": f"⚠️ {conflicting.event_time.strftime('%H:%M')} 已有「{conflicting.title}」，与此事件时间接近（{event_time.strftime('%H:%M')}）",
            "conflict_event_id": conflicting.id,
        })

    # 有冲突且未强制 → 只返回警告，不创建
    if warnings and not req.force_create:
        return {
            "success": False,
            "should_confirm": True,
            "warnings": warnings,
        }

    # 创建事件
    db_event = Event(
        title=req.title,
        event_time=event_time,
        description=req.description,
        remind=req.remind,
        event_type=req.event_type,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return {
        "id": db_event.id,
        "title": db_event.title,
        "event_time": db_event.event_time.isoformat(),
        "event_type": db_event.event_type,
        "description": db_event.description,
        "remind": db_event.remind,
        "completed": db_event.completed,
        "created_at": db_event.created_at.isoformat(),
        "warnings": warnings if warnings else None,
    }


class EventUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    event_time: str | None = None
    event_type: str | None = None
    description: str | None = None
    remind: bool | None = None
    completed: bool | None = None


@app.put("/events/{event_id}")
def update_event(event_id: int, req: EventUpdateRequest, db: Session = Depends(get_db)):
    """更新事件（部分更新，用于标记完成等）"""
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail=f"事件 #{event_id} 不存在")

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "event_time" and value:
            value = datetime.fromisoformat(value)
        setattr(db_event, key, value)

    db.commit()
    db.refresh(db_event)
    return {
        "id": db_event.id,
        "title": db_event.title,
        "event_time": db_event.event_time.isoformat(),
        "event_type": db_event.event_type,
        "description": db_event.description,
        "remind": db_event.remind,
        "completed": db_event.completed,
        "created_at": db_event.created_at.isoformat(),
    }


@app.get("/events")
def list_events(
    event_type: str | None = None,
    remind_only: bool = False,
    db: Session = Depends(get_db),
):
    """获取所有事件"""
    query = db.query(Event)
    if event_type:
        query = query.filter(Event.event_type == event_type)
    if remind_only:
        query = query.filter(Event.remind == True)

    events = query.order_by(Event.event_time.asc()).all()
    return [
        {
            "id": e.id,
            "title": e.title,
            "event_time": e.event_time.isoformat(),
            "event_type": e.event_type,
            "description": e.description,
            "remind": e.remind,
            "completed": e.completed,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


@app.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    """删除事件"""
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail=f"事件 #{event_id} 不存在")
    db.delete(db_event)
    db.commit()
    return None
