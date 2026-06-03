# CLAUDE.md — 语音日历项目

## 👤 关于我
- 有 C++ 基础的新手开发者，JavaScript / Python / Vue 边做边学
- 偏好：每个新概念先解释是什么、为什么，再写代码
- 代码注释用中文，文件名/函数名用英文
- 做决策时先给选项 + 优缺点对比，再推荐

## 📁 项目结构
```
voice-calendar/
├── frontend/        # Vue 3 + Vite（端口 5173）
│   └── src/
│       ├── api/           # 后端 API 调用
│       ├── composables/   # 可复用逻辑模块
│       ├── router/        # 页面路由
│       └── views/         # 页面组件
├── backend/         # Python FastAPI（端口 8000）
│   ├── main.py      # API 入口
│   ├── models.py    # 数据库模型
│   ├── database.py  # 数据库连接
│   ├── schemas.py   # 数据校验
│   ├── speech.py    # 讯飞语音识别
│   ├── nlp_parser.py # DeepSeek 语义解析
│   └── config.py    # 第三方 API 密钥
└── .claude/         # Claude Code 配置
```

## 🔧 技术栈
| 层 | 技术 | 为什么选它 |
|-----|------|-----------|
| 前端框架 | Vue 3 + Vite | 上手快，中文资料多，适合新手 |
| 后端框架 | Python FastAPI | 做 NLP 语音处理天然优势 |
| 数据库 | SQLite + SQLAlchemy | 零配置，单文件，够用 |
| 语音识别 | 讯飞语音听写 API | 中文识别最好，有免费额度 |
| 语义解析 | DeepSeek Chat API | 性价比高，解析中文自然语言准确 |

## 🚀 启动方式

**一键启动（推荐）**：
- Windows: 双击 `start.bat`
- Mac/Linux: `bash start.sh`

**手动启动**：
```bash
# 终端1 — 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# 终端2 — 前端
cd frontend
npm install
npm run dev
```
浏览器打开 http://localhost:5173

## 🌿 Git 分支策略
- master: 仅初始化 + README
- pr1-frontend-scaffold: Vue 前端骨架
- pr2-backend-scaffold: FastAPI 后端骨架
- pr3-event-crud-api: 事件增删改查 API
- pr4-voice-input: 前端录音 + 讯飞接口
- pr5-nlp-parser: DeepSeek 语义解析
- pr6-calendar-reminder: 日历月视图 + 浏览器提醒
- 每个 PR 一个分支，从 master 分出，独立开发

## ⚠️ 注意事项
- Windows 终端跨盘符要用 `cd /d` 而不是 `cd`
- 讯飞 API 审核中（2026-06-03 提交，两个工作日内）
- 后端密钥在 backend/config.py，不要提交到公开仓库
- 前端录音需要 Chrome/Edge 浏览器 + HTTPS 或 localhost
- 浏览器提醒需要用户手动授权通知权限
