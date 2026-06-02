# ===== 程序入口 =====
# FastAPI 应用的主文件，就像 C++ 的 main() 函数
# 运行方式：uvicorn main:app --reload
# 然后打开 http://localhost:8000/docs 可以看到交互式 API 文档

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from models import Event

# ---- 创建数据库表 ----
# 如果表不存在就自动创建（首次运行时）
# 类比 C++：if (!file_exists) create_file();
Base.metadata.create_all(bind=engine)

# ---- 创建 FastAPI 应用 ----
app = FastAPI(
    title="语音日历 API",
    description="语音日程管理助手的后端服务",
    version="0.1.0",
)

# ---- CORS 跨域配置 ----
# 重要！前端(Vue, 端口5173) 和 后端(FastAPI, 端口8000) 在不同端口
# 浏览器默认禁止跨端口访问，CORS 告诉浏览器"允许前端的请求"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 允许前端地址
    allow_credentials=True,
    allow_methods=["*"],                       # 允许所有 HTTP 方法（GET/POST/DELETE...）
    allow_headers=["*"],                       # 允许所有请求头
)


# ============================================
# API 端点（接口/路由）
# ============================================

@app.get("/")
def root():
    """根路径 — 健康检查

    访问 http://localhost:8000/ 返回这个
    用来确认"后端服务器还活着"
    """
    return {
        "status": "ok",
        "message": "语音日历 API 运行中 🎙️",
        "version": "0.1.0",
    }


@app.get("/events")
def list_events():
    """列出所有事件 — 占位接口

    当前版本返回空列表 + 使用说明
    完整实现在 PR3 中完成
    """
    return {
        "count": 0,
        "events": [],
        "hint": "这是占位接口，完整 CRUD 将在 PR3 实现。"
                "届时支持：GET/POST/PUT/DELETE /events",
    }


@app.get("/health")
def health_check():
    """健康检查端点 — 给前端判断后端是否在线"""
    return {"status": "healthy"}
