@echo off
chcp 65001 >nul
title Instalador de UeesTask
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar.ps1"
if errorlevel 1 (
  echo.
  echo La instalación no pudo completarse. Revise el mensaje anterior.
  pause
  exit /b 1
)
pause
