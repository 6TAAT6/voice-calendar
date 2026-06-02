# ===== 数据库配置 =====
# 创建数据库连接，类似于 C++ 里打开文件：
#   ofstream file("data.db");
# 但 SQLAlchemy 功能更强，之后能用 Python 对象操作数据库

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# 数据库文件位置：backend/voice_calendar.db
# SQLite 有 3 个好处：
# 1. 零安装 — 不需要装 MySQL/PostgreSQL
# 2. 就是文件 — 复制 .db 文件就等于备份了整个数据库
# 3. 够用 — 单机应用完全没问题
DATABASE_URL = "sqlite:///./voice_calendar.db"

# engine = 数据库引擎，"发动机"负责实际读写文件
# check_same_thread=False 让 FastAPI 的多线程能同时访问
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Session = 会话工厂，"每次打开数据库的一把钥匙"
# 每次请求拿一把，用完还回去
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = 所有数据模型的"父类"
# 之后定义 Event 类时继承它，SQLAlchemy 自动建表
class Base(DeclarativeBase):
    pass


# get_db() = 一个"发钥匙"的函数
# FastAPI 每次收到请求，调用它拿数据库连接，处理完自动关闭
# 类比 C++ 的 RAII：
#   {
#       FileHandle f = open("data.db");  // get_db() 做的
#       ... 读写操作 ...
#   }  // 离开作用域自动关闭
def get_db():
    db = SessionLocal()
    try:
        yield db      # yield = 交出数据库连接，用完后回到这里
    finally:
        db.close()    # 无论如何都会执行（即使中间出错），确保关闭连接
