#!/bin/bash
# 语音日历 — 一键启动（Mac / Linux）

set -e

echo ""
echo "  ╔══════════════════════════════╗"
echo "  ║   🎙️  语音日历  一键启动      ║"
echo "  ╚══════════════════════════════╝"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "  ❌ 未找到 Python，请先安装 Python 3.10+"
    exit 1
fi

# 检查 Node
if ! command -v node &> /dev/null; then
    echo "  ❌ 未找到 Node.js，请先安装 Node.js 18+"
    exit 1
fi

PYTHON=$(command -v python3 || command -v python)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$SCRIPT_DIR/backend"

# 检查 .env
if [ ! -f ".env" ]; then
    echo "  ⚠️  未找到 backend/.env，从 .env.example 复制模板..."
    cp .env.example .env
    echo "  ✏️  请编辑 backend/.env 填入真实密钥后重新运行"
    exit 1
fi

echo "  📦 检查依赖..."
$PYTHON -c "import fastapi" 2>/dev/null || {
    echo "  📦 安装后端依赖..."
    pip install -r requirements.txt
}

cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    echo "  📦 安装前端依赖..."
    npm install
fi

echo ""
echo "  🚀 启动服务..."

# 启动后端（后台）
cd "$SCRIPT_DIR/backend"
$PYTHON -m uvicorn main:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# 启动前端（后台）
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

sleep 4

echo ""
echo "  ✅ 启动完成！"
echo "  📱 浏览器打开: http://localhost:5173"
echo "  📚 API 文档:   http://localhost:8000/docs"
echo ""
echo "  按 Ctrl+C 停止所有服务..."

# 捕获退出信号，清理后台进程
cleanup() {
    echo ""
    echo "  正在停止服务..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "  已停止所有服务。"
    exit 0
}
trap cleanup SIGINT SIGTERM

# 等待子进程
wait
