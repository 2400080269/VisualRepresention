@echo off
setlocal
chcp 65001 >nul
title Student Performance Analytics & Early-Warning Platform
echo ======================================================================
echo Launching Full Stack Platform (FastAPI Backend + Streamlit Dashboard)...
echo ======================================================================
cd /d "%~dp0"

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "FastAPI Backend Layer" "%~dp0run_backend.bat"

echo [2/2] Launching Interactive Streamlit Dashboard...
if exist "%~dp0.venv\Scripts\streamlit.exe" (
    "%~dp0.venv\Scripts\streamlit.exe" run dashboard\app.py --browser.gatherUsageStats false
) else (
    streamlit run dashboard\app.py --browser.gatherUsageStats false
)

if errorlevel 1 (
    echo.
    echo Streamlit failed to start. Check the terminal output above.
    pause
)
endlocal
