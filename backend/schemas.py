# ===== 数据格式定义 =====
# Pydantic 模型 = JSON 的"类型检查器"
# 前端发来 {"title": "开会", "event_time": "2026-06-03T15:00"} 时
# FastAPI 自动用这个类验证：
#   title 是不是字符串？✓
#   event_time 是不是合法日期？✓
#   remind 没有传？那就用默认值 false ✓
# 任何一个检查不通过，自动返回友好的错误提示给前端

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ═══════════════════════════════════════
# 创建事件 — 前端发来的请求格式
# ═══════════════════════════════════════
class EventCreate(BaseModel):
    """创建事件时需要的字段

    JSON 示例：
    {
        "title": "产品评审会",
        "event_time": "2026-06-03T15:00:00",
        "description": "讨论新功能需求",
        "remind": true,
        "event_type": "会议"
    }
    """
    title: str = Field(..., min_length=1, max_length=200, description="事件标题")
    event_time: datetime = Field(..., description="事件发生时间，ISO格式")
    description: str = Field(default="", max_length=500, description="备注描述")
    remind: bool = Field(default=False, description="是否需要提醒")
    event_type: str = Field(default="其他", max_length=50, description="类型：会议/运动/生日/其他")


# ═══════════════════════════════════════
# 更新事件 — 前端发来的请求格式
# ═══════════════════════════════════════
class EventUpdate(BaseModel):
    """更新事件时需要的字段
    和创建的区别：所有字段都是可选的，传什么改什么
    不传的字段保持原值不变
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    event_time: Optional[datetime] = None
    description: Optional[str] = Field(None, max_length=500)
    remind: Optional[bool] = None
    event_type: Optional[str] = Field(None, max_length=50)
    completed: Optional[bool] = None


# ═══════════════════════════════════════
# 事件响应 — 后端返回的数据格式
# ═══════════════════════════════════════
class EventResponse(BaseModel):
    """返回给前端的事件格式
    比数据库多传了 id 和 created_at 等自动生成的字段
    """
    id: int
    title: str
    event_time: datetime
    description: str
    remind: bool
    completed: bool
    event_type: str
    created_at: datetime

    # model_config 告诉 Pydantic 可以从数据库对象自动转换
    model_config = {"from_attributes": True}
