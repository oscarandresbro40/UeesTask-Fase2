@echo off
chcp 65001 >nul
title Requisitos de UeesTask
where winget >nul 2>&1
if errorlevel 1 (
  echo Windows Package Manager no está disponible.
  echo Instale manualmente Docker Desktop y Python 3.12.
  pause
  exit /b 1
)
echo Instalando o actualizando Python 3.12...
winget install --id Python.Python.3.12 --exact --accept-package-agreements --accept-source-agreements
echo.
echo Instalando o actualizando Docker Desktop...
winget install --id Docker.DockerDesktop --exact --accept-package-agreements --accept-source-agreements
echo.
echo Reinicie Windows si Docker Desktop lo solicita.
echo Después ejecute INSTALAR_UEESTASK.bat.
pause