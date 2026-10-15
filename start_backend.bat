@echo off
chcp 65001 > nul
title [SmartCity] 통합관제 백엔드 서버 (Port 8080)

echo ==========================================================
echo  [SmartCity] 스마트시티 공공시설 & 민원 통합관제 백엔드 구동
echo ==========================================================
echo.

:: 1. 파이썬 환경 체크
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 런타임을 찾을 수 없습니다.
    echo 시스템에 Python이 설치되어 있고 PATH에 등록되어 있는지 확인해주세요.
    echo.
    pause
    exit /b 1
)

:: 2. 포트 8080 점유 여부 체크
netstat -ano | findstr ":8080" > nul 2>&1
if %errorlevel% equ 0 (
    echo [주의] 8080 포트가 이미 사용 중입니다. 기존 프로세스를 종료 후 다시 실행해주세요.
    echo.
)

echo [*] 백엔드 REST & 넥사크로(Nexacro) API 서버를 시작합니다...
echo [*] Base URL : http://localhost:8080/api
echo [*] 종료하려면 이 창에서 Ctrl + C 를 누르세요.
echo.

python backend\server.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 서버 비정상 종료 (에러 코드: %errorlevel%)
    pause
)
