# 🎙️ 语音日历 — Voice Calendar

> 以语音交互为核心的智能日程管理助手。**说一句话，轻松管理你的日程。**

[![Vue](https://img.shields.io/badge/Vue-3-4fc08d?logo=vue.js)](https://vuejs.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)


## 🎥 Demo 视频

> 🎬 **演示视频**：[点击观看]()（链接待添加）



## ✨ 核心功能

### 🎤 语音交互（核心）
| 功能 | 说明 |
|------|------|
| 🎙️ **语音创建** | 说一句话自动创建日程，支持复杂时间表达 |
| ✏️ **AI 对话修正** | 识别不对？说"改成xxx"直接修正 |
| 🔊 **语音播报反馈** | 创建成功自动播报"已为您创建xxx" |

### 📅 三视图日历
| 视图 | 说明 |
|------|------|
| 📅 月视图 | 彩色事件块，类型一目了然 |
| 📊 周视图 | 7 列时间轴，满屏看本周 |
| 📋 日视图 | 当天事件时间轴，左侧色条 |

### 🧠 智能能力
| 功能 | 说明 |
|------|------|
| ⚠️ **冲突检测** | 创建时自动检测重复和时间冲突 |
| 🔄 **重复事件** | NLP 识别"每天早上跑步" |
| 📊 **统计面板** | 本月/本周/近3天/完成率 |
| 🔍 **搜索筛选** | 关键词实时过滤 + 类型筛选 |
| 📥 **ics 导出** | 一键导出，导入 Apple/Google Calendar |


## 🏗️ 技术栈

| 层 | 技术 | 为什么选它 |
|------|------|------|
| 前端框架 | Vue 3 + Vite | 上手快，中文资料多 |
| 后端框架 | Python FastAPI | AI/NLP 处理天然优势 |
| 数据库 | SQLite + SQLAlchemy | 零配置，够用 |
| 语音识别 | 讯飞语音听写 IAT v2 | 中文识别最好，免费额度 |
| 语音合成 | 讯飞语音合成 TTS v2 | 中文语音自然，免费额度 |
| 语义解析 | DeepSeek Chat API | 性价比高，中文理解准确 |


## 📁 项目结构

```
voice-calendar/
├── frontend/                   # Vue 3 + Vite（端口 5173）
│   └── src/
│       ├── api/index.js        # 后端 API 调用
│       ├── composables/        # 可复用逻辑
│       │   ├── useAudioRecorder.js   # PCM 实时采集
│       │   └── useReminder.js        # 浏览器提醒
│       ├── router/index.js     # 页面路由
│       └── views/
│           ├── Home.vue        # 主页（录音+AI解析）
│           ├── Calendar.vue    # 三视图日历
│           └── Settings.vue    # 设置
├── backend/                    # Python FastAPI（端口 8000）
│   ├── main.py                 # API 入口（15+ 端点）
│   ├── models.py               # 数据库模型
│   ├── database.py             # 数据库连接
│   ├── speech.py               # 讯飞语音识别 IAT v2
│   ├── tts.py                  # 讯飞语音合成 TTS v2
│   ├── nlp_parser.py           # DeepSeek 语义解析 + 对话修正
│   ├── config.py               # 环境变量配置
│   └── .env.example            # 配置模板
├── start.bat                   # Windows 一键启动
├── start.sh                    # Mac/Linux 一键启动
└── DEMO_SCRIPT.md              # 演示演讲稿
```


## 🚀 快速启动

### 一键启动（推荐）

- **Windows**：双击 `start.bat`
- **Mac/Linux**：`bash start.sh`

### 手动启动

```bash
# 1. 配置密钥
cp backend/.env.example backend/.env
# 编辑 backend/.env 填入你的讯飞和 DeepSeek 密钥

# 2. 终端1 — 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# 3. 终端2 — 前端
cd frontend
npm install
npm run dev
```

浏览器打开 **http://localhost:5173**


## 🔑 API 密钥获取

| 服务 | 用途 | 获取地址 | 免费额度 |
|------|------|------|------|
| 讯飞语音听写 | 语音→文字 | [console.xfyun.cn](https://console.xfyun.cn/) | 500次/天 |
| 讯飞语音合成 | 文字→语音 | [console.xfyun.cn](https://console.xfyun.cn/) | 500次/天 |
| DeepSeek | NLP语义解析 | [platform.deepseek.com](https://platform.deepseek.com/) | 500万tokens |


## 🌿 分支策略

| 分支 | 功能 |
|------|------|
| `master` | 主分支（可运行） |
| `pr1-frontend-scaffold` | Vue 前端骨架 |
| `pr2-backend-scaffold` | FastAPI 后端骨架 |
| `pr3-event-crud-api` | 事件增删改查 API |
| `pr4-voice-input` | 前端录音 + 讯飞接口 |
| `pr5-nlp-parser` | DeepSeek 语义解析 |
| `pr6-calendar-reminder` | 日历月视图 + 浏览器提醒 |
| `pr7-optimization` | .gitignore + .env 安全 + 错误处理统一 |
| `pr8-tts-smart` | 语音合成播报 + AI对话修正 + 冲突检测 + 一键启动 |
| `pr9-all-features` | 三视图 + 搜索筛选 + 统计面板 + ics导出 + 重复事件 |


## ⚠️ 注意事项

- 录音需要 **Chrome/Edge 浏览器** + localhost
- 浏览器提醒需用户手动授权通知权限
- `.env` 文件包含密钥，已加入 `.gitignore`，不会被提交到仓库
- 首次启动需配置 API 密钥，参考 `.env.example`


## 👤 作者

- 6TAAT6


## 📄 许可

MIT
