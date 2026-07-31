@echo off
chcp 65001 >nul
title Verificación de UeesTask
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Falta el entorno virtual. Ejecute INSTALAR_UEESTASK.bat.
  pause
  exit /b 1
)

echo Ejecutando pruebas automatizadas...
".venv\Scripts\python.exe" -m pytest -q
if errorlevel 1 (
  echo La verificación encontró errores.
  pause
  exit /b 1
)

echo.
echo Verificando datos restaurados...
docker exec ueestask-postgres psql -U ueestask -d ueestask -c "SELECT 'usuarios' tabla,count(*) registros FROM usuarios UNION ALL SELECT 'cursos',count(*) FROM cursos UNION ALL SELECT 'entregas',count(*) FROM entregas UNION ALL SELECT 'notificaciones',count(*) FROM notificaciones;"
pause
