# ===== 语音日历 API — 完整功能 =====
# PR5: 加入 DeepSeek 语义解析 + 事件创建
# 运行：uvicorn main:app --reload
# 文档：http://localhost:8000/docs

from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import engine, Base, get_db
from models import Event
from speech import recognize_audio
from nlp_parser import parse_schedule


# ---- 请求/响应模型 ----
class ParseRequest(BaseModel):
    text: str = Field(..., min_length=1, description="用户说的话")


class EventCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    event_time: str = Field(..., description="ISO 格式: yyyy-MM-ddTHH:mm:ss")
    event_type: str = Field(default="其他")
    description: str = Field(default="")
    remind: bool = Field(default=True)


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
async def speech_recognize(audio: UploadFile = File(...)):
    """接收音频 → 讯飞识别 → 返回文字"""
    audio_bytes = await audio.read()

    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="音频文件为空")
    if len(audio_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="音频文件过大")

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
# 事件 CRUD（PR3 核心功能）
# ============================================

@app.post("/events", status_code=201)
def create_event(req: EventCreateRequest, db: Session = Depends(get_db)):
    """创建事件（前端解析完直接调用）"""
    db_event = Event(
        title=req.title,
        event_time=datetime.fromisoformat(req.event_time),
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
