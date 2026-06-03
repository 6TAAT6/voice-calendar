@echo off
title Voice Calendar Start

echo ============================================
echo   Voice Calendar - Yi Jian Qi Dong
echo ============================================
echo.

:: Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Install Python 3.10+
    pause
    exit /b 1
)
echo [OK] Python found

:: Check Node
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found! Install Node.js 18+
    pause
    exit /b 1
)
echo [OK] Node.js found

:: Check .env
if not exist "%~dp0backend\.env" (
    echo [WARN] backend\.env not found, copying from .env.example...
    copy "%~dp0backend\.env.example" "%~dp0backend\.env" >nul
    echo [WARN] Please edit backend\.env with your API keys!
)

:: Install backend deps
echo.
echo [STEP] Checking backend dependencies...
cd /d "%~dp0backend"
pip install -r requirements.txt -q 2>&1
if %errorlevel% neq 0 (
    echo [WARN] pip install failed, trying to continue...
)

:: Install frontend deps
echo [STEP] Checking frontend dependencies...
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo [STEP] Installing frontend deps (npm install)...
    npm install
)

echo.
echo [START] Launching backend on port 8000...
start "Backend-8000" cmd /k "cd /d "%~dp0backend" && uvicorn main:app --host 127.0.0.1 --port 8000"

echo [START] Waiting 3 seconds for backend...
timeout /t 3 /nobreak >nul

echo [START] Launching frontend on port 5173...
start "Frontend-5173" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo [START] Waiting 4 seconds for frontend...
timeout /t 4 /nobreak >nul

echo.
echo ============================================
echo   ALL DONE! Open browser:
echo   http://localhost:5173
echo ============================================
echo.
echo Close backend/frontend windows to stop.
echo Press any key to open browser, or close this window.
pause >nul
start http://localhost:5173
