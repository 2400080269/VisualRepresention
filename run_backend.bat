@echo off
setlocal
chcp 65001 >nul
title Student Performance Analytics - FastAPI Backend
echo ======================================================================
echo Starting FastAPI Backend Layer on http://127.0.0.1:8000 ...
echo Interactive Swagger Documentation: http://127.0.0.1:8000/docs
echo ======================================================================
cd /d "%~dp0"

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

if exist "%~dp0.venv\Scripts\python.exe" (
    echo Using project virtual environment: .venv
    "%~dp0.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
) else (
    echo Using system Python
    python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
)

if errorlevel 1 (
    echo.
    echo FastAPI Backend encountered an error.
    pause
)
endlocal
