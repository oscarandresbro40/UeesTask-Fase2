$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

function Step([string]$Message) {
    Write-Host ''
    Write-Host "==> $Message" -ForegroundColor Cyan
}
function Has-Command([string]$Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

Write-Host 'UEESTASK - INSTALACION AUTOMATICA' -ForegroundColor Magenta
Write-Host 'El proceso conserva los datos demostrativos D4 en PostgreSQL.'

Step 'Comprobando Docker Desktop'
if (-not (Has-Command 'docker')) {
    throw 'Docker Desktop no esta instalado. Ejecute INSTALAR_REQUISITOS.bat y reinicie Windows si se solicita.'
}
$null = & docker info 2>$null
if ($LASTEXITCODE -ne 0) {
    $dockerDesktop = 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
    if (-not (Test-Path -LiteralPath $dockerDesktop)) {
        throw 'Docker Desktop no esta activo. Abralo y repita la instalacion.'
    }
    Write-Host 'Iniciando Docker Desktop...'
    Start-Process -FilePath $dockerDesktop
    $ready = $false
    for ($attempt = 1; $attempt -le 60; $attempt++) {
        Start-Sleep -Seconds 2
        $null = & docker info 2>$null
        if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    }
    if (-not $ready) { throw 'Docker Desktop no respondio despues de dos minutos.' }
}

Step 'Comprobando Python 3.12 o posterior'
$pythonMode = ''
if (Has-Command 'py') {
    $valid = & py -3.12 -c 'import sys; print(sys.version_info >= (3, 12))' 2>$null
    if ($valid -eq 'True') { $pythonMode = 'py' }
}
if (-not $pythonMode -and (Has-Command 'python')) {
    $valid = & python -c 'import sys; print(sys.version_info >= (3, 12))' 2>$null
    if ($valid -eq 'True') { $pythonMode = 'python' }
}
if (-not $pythonMode) {
    throw 'Se requiere Python 3.12 o posterior. Ejecute INSTALAR_REQUISITOS.bat.'
}

Step 'Creando entorno virtual e instalando dependencias'
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    if ($pythonMode -eq 'py') { & py -3.12 -m venv .venv }
    else { & python -m venv .venv }
}
& '.venv\Scripts\python.exe' -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'No fue posible actualizar pip.' }
& '.venv\Scripts\python.exe' -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'No fue posible instalar las dependencias.' }

Step 'Iniciando PostgreSQL 16'
& docker compose up -d db
if ($LASTEXITCODE -ne 0) { throw 'Docker no pudo crear el contenedor PostgreSQL.' }
$databaseReady = $false
for ($attempt = 1; $attempt -le 40; $attempt++) {
    & docker exec ueestask-postgres pg_isready -U ueestask -d ueestask *> $null
    if ($LASTEXITCODE -eq 0) { $databaseReady = $true; break }
    Start-Sleep -Seconds 2
}
if (-not $databaseReady) { throw 'PostgreSQL no quedo disponible.' }

Step 'Restaurando la base demostrativa'
$schema = & docker exec ueestask-postgres psql -U ueestask -d ueestask -Atqc "SELECT to_regclass('public.usuarios');"
if ([string]::IsNullOrWhiteSpace($schema)) {
    & docker cp 'database\ueestask_demo_d4.dump' 'ueestask-postgres:/tmp/ueestask_demo_d4.dump'
    if ($LASTEXITCODE -ne 0) { throw 'No fue posible copiar el respaldo al contenedor.' }
    & docker exec ueestask-postgres pg_restore -U ueestask -d ueestask --no-owner --no-privileges '/tmp/ueestask_demo_d4.dump'
    if ($LASTEXITCODE -ne 0) { throw 'No fue posible restaurar la base demostrativa.' }
    Write-Host 'Datos D4 restaurados correctamente.' -ForegroundColor Green
} else {
    Write-Host 'La base ya contiene informacion; no se sobrescribieron datos.' -ForegroundColor Yellow
}

Step 'Verificando migraciones y pruebas'
& '.venv\Scripts\python.exe' -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Alembic no pudo verificar el esquema.' }
& '.venv\Scripts\python.exe' -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Las pruebas no fueron aprobadas.' }

Step 'Creando acceso directo'
try {
    $desktop = [Environment]::GetFolderPath('Desktop')
    $shortcutPath = Join-Path $desktop 'UeesTask.lnk'
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = Join-Path $PSScriptRoot 'INICIAR_UEESTASK.bat'
    $shortcut.WorkingDirectory = $PSScriptRoot
    $shortcut.Description = 'Iniciar UeesTask'
    $shortcut.Save()
} catch {
    Write-Host 'Use INICIAR_UEESTASK.bat para abrir el sistema.' -ForegroundColor Yellow
}

Write-Host ''
Write-Host 'INSTALACION COMPLETADA' -ForegroundColor Green
Write-Host 'Direccion: http://localhost:8000'
Write-Host 'Administrador: admin@uees.edu.ec / Admin123!'
Write-Host 'Docente: docente@uees.edu.ec / Docente123!'
Write-Host 'Estudiante: estudiante@uees.edu.ec / Estudiante123!'
Write-Host 'Ejecute INICIAR_UEESTASK.bat.'