# ===== 数据模型 =====
# 定义"日程事件"长什么样
# 这个 Python 类会自动转成数据库表，不用手动写 CREATE TABLE

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from database import Base


class Event(Base):
    """日程事件模型

    一个 Event 对象 = 数据库里 events 表的一行

    表的列：
    ┌────┬──────────┬──────────┬─────────────────┬─────────┬──────────┬──────┐
    │ id │  title   │   time   │   description   │ remind  │ completed│ type │
    ├────┼──────────┼──────────┼─────────────────┼─────────┼──────────┼──────┤
    │ 1  │ 开会     │2026-06.. │ 产品评审会       │  True   │  False   │ 会议 │
    │ 2  │ 跑步     │2026-06.. │ 5公里           │  False  │  False   │ 运动 │
    └────┴──────────┴──────────┴─────────────────┴─────────┴──────────┴──────┘
    """

    # __tablename__ 指定数据库里的表名
    __tablename__ = "events"

    # 用 Column() 定义每一列
    id = Column(Integer, primary_key=True, index=True)  # 主键，自增ID，唯一标识
    title = Column(String(200), nullable=False)         # 事件标题（如"开会"），最长200字，必填
    event_time = Column(DateTime, nullable=False)       # 事件时间，必填
    description = Column(String(500), default="")        # 备注描述，最长500字，可选
    remind = Column(Boolean, default=False)              # 是否需要提醒，默认不需要
    completed = Column(Boolean, default=False)           # 是否已完成，默认未完成
    event_type = Column(String(50), default="其他")      # 事件类型：会议/运动/生日/其他
    created_at = Column(DateTime, default=datetime.now)  # 创建时间，自动填充

    # __repr__ = 打印对象时的显示格式（调试用）
    def __repr__(self):
        return f"<Event(id={self.id}, title='{self.title}', time={self.event_time})>"
