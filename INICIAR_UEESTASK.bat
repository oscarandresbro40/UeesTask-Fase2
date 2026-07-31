@echo off
chcp 65001 >nul
title UeesTask
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo UeesTask todavía no está instalado.
  echo Ejecute primero INSTALAR_UEESTASK.bat.
  pause
  exit /b 1
)

docker compose up -d db
if errorlevel 1 (
  echo No fue posible iniciar PostgreSQL. Abra Docker Desktop e inténtelo nuevamente.
  pause
  exit /b 1
)

start "" powershell.exe -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://localhost:8000'"
".venv\Scripts\python.exe" -m uvicorn app.final:app --host 127.0.0.1 --port 8000
