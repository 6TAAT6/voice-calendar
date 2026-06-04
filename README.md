# 语音日历 — Voice Calendar

> 以语音交互为核心的智能日程管理。**说一句话，轻松管理日程。**

[![Vue](https://img.shields.io/badge/Vue-3-4fc08d?logo=vue.js)](https://vuejs.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)


## Demo 视频

> 演示视频链接（待添加）



## 核心功能

### 语音交互
| 功能 | 说明 |
|------|------|
| 语音创建 | 说一句话自动创建日程 |
| AI 对话修正 | 识别不准？说"改成xxx"直接修正 |
| 语音播报 | 创建成功自动播报"已为您创建xxx" |

### 三视图日历
- 月视图：彩色事件块，10种类型独立配色
- 周视图：7列时间轴，每小时一格
- 日视图：当天事件时间轴，左侧色条

### 智能能力
- 冲突检测：创建时自动检测重复和时间冲突
- 重复事件：NLP 识别"每天早上跑步"并标记循环
- 统计面板：本月/本周/近3天/完成率
- 搜索筛选：关键词实时过滤 + 类型下拉
- ics 导出：一键导出，导入 Apple/Google Calendar


## 技术栈

| 层 | 技术 | 为什么 |
|------|------|------|
| 前端 | Vue 3 + Vite | 上手快，中文资料多 |
| 后端 | Python FastAPI | AI 处理天然优势 |
| 数据库 | SQLite + SQLAlchemy | 零配置 |
| 语音识别 | 讯飞 IAT v2 | 中文识别最好 |
| 语音合成 | 讯飞 TTS v2 | 语音反馈自然 |
| 语义解析 | DeepSeek Chat | 性价比高 |


## 项目结构

```
voice-calendar/
├── frontend/                 # Vue 3 + Vite（5173）
│   └── src/
│       ├── api/index.js
│       ├── composables/
│       │   ├── useAudioRecorder.js
│       │   └── useReminder.js
│       └── views/
│           ├── Home.vue      # 主页：录音 + AI解析
│           ├── Calendar.vue  # 三视图日历
│           └── Settings.vue
├── backend/                  # FastAPI（8000）
│   ├── main.py               # 15+ API 端点
│   ├── speech.py             # 讯飞语音识别
│   ├── tts.py                # 讯飞语音合成
│   ├── nlp_parser.py         # DeepSeek 解析+修正
│   ├── config.py
│   └── .env.example
├── start.bat                 # Windows 一键启动
├── start.sh                  # Mac/Linux 一键启动
└── DEMO_SCRIPT.md            # 演示演讲稿
```


## 快速启动

### 一键启动
- Windows：双击 `start.bat`
- Mac/Linux：`bash start.sh`

### 手动启动
```bash
# 终端1 — 后端
cd backend && pip install -r requirements.txt
uvicorn main:app --reload

# 终端2 — 前端
cd frontend && npm install && npm run dev
```
浏览器打开 http://localhost:5173


## API 密钥

| 服务 | 获取地址 | 免费额度 |
|------|------|------|
| 讯飞语音听写 | console.xfyun.cn | 500次/天 |
| 讯飞语音合成 | console.xfyun.cn | 500次/天 |
| DeepSeek | platform.deepseek.com | 500万tokens |

配置方式：`cp backend/.env.example backend/.env` → 填入密钥


## Git 分支

| 分支 | 功能 |
|------|------|
| pr1-frontend-scaffold | Vue 前端骨架 |
| pr2-backend-scaffold | FastAPI 后端骨架 |
| pr3-event-crud-api | 事件增删改查 |
| pr4-voice-input | 前端录音 + 讯飞接口 |
| pr5-nlp-parser | DeepSeek 语义解析 |
| pr6-calendar-reminder | 月视图日历 + 浏览器提醒 |
| pr7-optimization | 工程规范化 + 安全加固 |
| pr8-tts-smart | TTS + AI修正 + 冲突检测 + 一键启动 |
| pr9-all-features | 三视图 + 搜索 + 统计 + 导出 + 重复事件 |


## 注意事项

- 录音需 Chrome/Edge + localhost
- `.env` 已加入 `.gitignore`，不会被提交
- 首次启动需配置密钥，参考 `.env.example`


## 作者

6TAAT6

## 许可

MIT
