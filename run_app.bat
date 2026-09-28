@echo off
title Student Performance Analytics & Visualization Platform
echo ======================================================================
echo Launching Student Performance Analytics Platform...
echo ======================================================================
cd /d "%~dp0"
call .venv\Scripts\activate.bat
streamlit run dashboard\app.py
pause
