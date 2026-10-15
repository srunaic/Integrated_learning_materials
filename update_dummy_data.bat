@echo off
title SmartCity Dummy Data and Excel Generator
echo ==========================================================
echo  [SmartCity] Data Generator and Excel Reporter
echo ==========================================================
echo.
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    pause
    exit /b 1
)
echo [*] Generating dummy data and Excel reports...
python db\generate_dummy.py
echo.
echo ==========================================================
echo  [SUCCESS] Completed. Check db\excel_logs folder.
echo ==========================================================
pause