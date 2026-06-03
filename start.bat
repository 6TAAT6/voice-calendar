@echo off
chcp 65001 >nul
title 语音日历 — 一键启动

echo.
echo   ╔══════════════════════════════╗
echo   ║   🎙️  语音日历  一键启动      ║
echo   ╚══════════════════════════════╝
echo.

:: 检查 Python 环境
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo   ❌ 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

:: 检查 Node 环境
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo   ❌ 未找到 Node.js，请先安装 Node.js 18+
    pause
    exit /b 1
)

echo   📦 检查后端依赖...
cd /d "%~dp0backend"
pip list >nul 2>&1

echo   📦 检查前端依赖...
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo   📦 正在安装前端依赖...
    npm install
)

echo.
echo   🚀 启动服务...

:: 启动后端
start "语音日历-后端" cmd /c "cd /d "%~dp0backend" && echo [后端] 启动中... && uvicorn main:app --reload --host 127.0.0.1 --port 8000"

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: 启动前端
start "语音日历-前端" cmd /c "cd /d "%~dp0frontend" && echo [前端] 启动中... && npm run dev"

:: 等待前端启动
timeout /t 5 /nobreak >nul

echo.
echo   ✅ 启动完成！
echo   📱 浏览器打开: http://localhost:5173
echo   📚 API 文档:   http://localhost:8000/docs
echo.
echo   按任意键停止所有服务...
pause >nul

:: 清理
taskkill /FI "WINDOWTITLE eq 语音日历-*" /T /F >nul 2>&1
echo   已停止所有服务。
