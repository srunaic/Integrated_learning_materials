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
echo [*] Starting SmartCity REST and Nexacro API Server (Port 8080)...
echo [*] URL: http://localhost:8080/api
echo [*] Press Ctrl+C to stop.
echo.
python backend\server.py
pause