@echo off
setlocal
chcp 65001 >nul
title Student Performance Analytics - FastAPI Backend
echo ======================================================================
echo Starting FastAPI Backend Layer on http://127.0.0.1:8000 ...
echo Interactive Swagger Documentation: http://127.0.0.1:8000/docs
echo ======================================================================
cd /d "%~dp0"
call .venv\Scripts\activate.bat
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
if errorlevel 1 (
    echo.
    echo FastAPI Backend encountered an error.
    pause
)
endlocal
