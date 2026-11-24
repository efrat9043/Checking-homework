@echo off
rem Double-click to open the grading app in the browser.
chcp 65001 >nul
cd /d "%~dp0"
title Machvan - grading app

if not exist ".venv\Scripts\python.exe" (
  echo [!] The virtual environment .venv was not found. See README - installation.
  pause
  exit /b 1
)
if not exist ".env" (
  echo [!] The .env file was not found. Copy .env.example to .env and fill in the keys.
  pause
  exit /b 1
)

echo Starting the app. The browser will open in a few seconds...
echo Keep this window open while you use the app. Close it to stop.
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 5; Start-Process 'http://localhost:8501'"
".venv\Scripts\python.exe" -m streamlit run app.py
pause
