# ===== 语音日历 API — 事件增删改查（CRUD）=====
# 运行方式：uvicorn main:app --reload
# API 文档：http://localhost:8000/docs（自动生成，可在页面上直接测试）
#
# 接口总览：
#   POST   /events        → 创建事件
#   GET    /events        → 获取事件列表（支持按类型/提醒筛选）
#   GET    /events/{id}   → 获取单个事件详情
#   PUT    /events/{id}   → 更新事件
#   DELETE /events/{id}   → 删除事件
#   GET    /              → 健康检查
#   GET    /health        → 健康检查

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import Event
from schemas import EventCreate, EventUpdate, EventResponse


# ---- 启动时自动创建数据库表 ----
Base.metadata.create_all(bind=engine)

# ---- FastAPI 应用 ----
app = FastAPI(
    title="语音日历 API",
    description="语音日程管理助手 — 事件增删改查服务",
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
# 健康检查（确认服务器活着）
# ============================================

@app.get("/")
def root():
    """根路径"""
    return {"status": "ok", "message": "语音日历 API 运行中 🎙️"}


@app.get("/health")
def health_check():
    """健康检查 — 前端用这个判断后端是否在线"""
    return {"status": "healthy"}


# ============================================
# 核心 CRUD 接口
# ============================================

@app.post("/events", response_model=EventResponse, status_code=201)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """创建事件

    请求示例：
    POST /events
    {
        "title": "产品评审会",
        "event_time": "2026-06-03T15:00:00",
        "description": "讨论新功能",
        "remind": true,
        "event_type": "会议"
    }
    """
    # Step 1: 把请求数据转成数据库模型对象
    db_event = Event(**event.model_dump())

    # Step 2: 添加到数据库
    db.add(db_event)

    # Step 3: 保存提交
    db.commit()

    # Step 4: 刷新，获取数据库自动生成的 id 和 created_at
    db.refresh(db_event)

    return db_event


@app.get("/events", response_model=list[EventResponse])
def list_events(
    event_type: str | None = None,
    remind_only: bool = False,
    db: Session = Depends(get_db),
):
    """获取所有事件列表

    支持筛选参数：
    - ?event_type=会议  → 只看会议类型
    - ?remind_only=true → 只看需要提醒的
    - 不加参数返回全部
    """
    query = db.query(Event)

    if event_type:
        query = query.filter(Event.event_type == event_type)
    if remind_only:
        query = query.filter(Event.remind == True)

    return query.order_by(Event.event_time.asc()).all()


@app.get("/events/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """获取单个事件详情

    GET /events/1  → 返回 id=1 的事件
    GET /events/99 → 返回 404 错误
    """
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail=f"事件 #{event_id} 不存在")
    return db_event


@app.put("/events/{event_id}", response_model=EventResponse)
def update_event(event_id: int, event: EventUpdate, db: Session = Depends(get_db)):
    """更新事件（支持部分更新）

    PUT /events/1
    { "title": "新标题", "completed": true }
    → 只改 title 和 completed，没传的字段保持原值
    """
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail=f"事件 #{event_id} 不存在")

    # exclude_unset=True → 只取前端实际传了的字段
    update_data = event.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)

    db.commit()
    db.refresh(db_event)
    return db_event


@app.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    """删除事件

    DELETE /events/1  → 删除成功（HTTP 204，无返回内容）
    DELETE /events/99 → 返回 404
    """
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail=f"事件 #{event_id} 不存在")

    db.delete(db_event)
    db.commit()
    return None
