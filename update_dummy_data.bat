@echo off
chcp 65001 > nul
title [SmartCity] Dummy Data & Excel Generator

echo ==========================================================
echo  [SmartCity] 대용량 가상 데이터 자동 공급 및 엑셀 리포트 생성
echo ==========================================================
echo.

:: 파이썬 실행 경로 확인
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python이 설치되어 있지 않거나 PATH에 등록되지 않았습니다.
    pause
    exit /b 1
)

echo [*] 대용량 가상 민원 / 공공시설물 / IoT 센서 데이터 생성 중...
echo [*] 엑셀(Excel) 날짜별 기록 및 웹 Mock 데이터 자동 갱신 진행...
echo.

python db\generate_dummy.py

if %errorlevel% equ 0 (
    echo.
    echo ==========================================================
    echo  [성공] 데이터 생성 및 엑셀 기록이 완료되었습니다!
    echo  - 엑셀 파일 저장 위치: db\excel_logs\
    echo  - 웹 Mock 동기화 위치: web_portal\mock_data\
    echo ==========================================================
) else (
    echo.
    echo [ERROR] 데이터 생성 중 오류가 발생했습니다.
)

echo.
echo 아무 키나 누르면 창이 닫힙니다.
pause > nul
