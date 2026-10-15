@echo off
title SmartCity Backend Server
echo ==========================================================
echo  [SmartCity] Backend Server Starting...
echo ==========================================================
echo.
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    pause
    exit /b 1
)

:: 8080 포트 점유 중인 프로세스 자동 정리 (충돌 원천 차단)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8080" ^| findstr "LISTENING"') do (
    echo [*] Clearing existing port 8080 process (PID: %%a)...
    taskkill /F /PID %%a > nul 2>&1
)

echo [*] Starting SmartCity REST and Nexacro API Server (Port 8080)...
echo [*] URL: http://localhost:8080/api
echo [*] Press Ctrl+C to stop.
echo.
python backend\server.py
pause