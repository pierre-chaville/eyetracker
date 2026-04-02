@echo off
title Eye Tracker Launcher
cd /d "%~dp0"
:: Try the backend venv Python first, fall back to system Python
if exist "..\backend\venv\Scripts\python.exe" (
    "..\backend\venv\Scripts\python.exe" launcher.py
) else (
    python launcher.py
)
pause
