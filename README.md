# UeesTask

Plataforma web para seguimiento de tareas academicas con notificaciones.

## Dominio
- D4

## Objetivo
Gestionar el ciclo academico de tareas en cursos universitarios: publicacion de actividades, entregas, calificacion, notificaciones y controles administrativos.

## Funcionalidades principales
- Autenticacion y sesion web.
- Paneles por rol (administrador, docente, estudiante).
- Gestion de usuarios.
- Gestion de cursos y matriculas.
- Gestion de tareas y recursos.
- Registro de entregas.
- Calificaciones y retroalimentacion.
- Notificaciones.
- Gestion avanzada (edicion/estado de usuarios, cursos y tareas).
- Reglas academicas a nivel de sesion SQLAlchemy.

## Tecnologias reales
- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Jinja2
- pytest
- Docker Compose

## Estructura actual del repositorio
- app/: aplicacion web y dominio de negocio.
- migrations/: migraciones Alembic.
- tests/: pruebas automatizadas.
- database/: respaldo de datos demostrativos.
- docs/: evidencias y documentacion tecnica.
- uploads/: almacenamiento local de archivos.

## Requisitos
- Windows
- Python 3.12 o posterior
- Docker Desktop

## Instalacion para usuario
1. Ejecutar INSTALAR_REQUISITOS.bat solo si faltan requisitos del entorno.
2. Ejecutar INSTALAR_UEESTASK.bat.
3. Ejecutar INICIAR_UEESTASK.bat.
4. Abrir http://localhost:8000.

## Instalacion manual para desarrollo
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
docker compose up -d db
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m uvicorn app.final:app --reload
```

## Entry point oficial
- app.final:app

## Ejecucion de pruebas
```powershell
.\.venv\Scripts\python.exe -m pytest
```
Resultado actual: 32 passed.

## Cuentas demostrativas
Credenciales solo para uso local de demostracion academica.
- admin@uees.edu.ec / Admin123!
- docente@uees.edu.ec / Docente123!
- estudiante@uees.edu.ec / Estudiante123!

## Base de datos demostrativa
- Archivo: database/ueestask_demo_d4.dump
- Uso: datos de demostracion reproducibles para entorno local.

## Reglas de negocio finales
- La suma de ponderaciones de tareas por curso no puede superar 100%.
- No se aceptan entregas cuando la tarea esta cerrada.
- Las reglas se aplican en before_flush de SQLAlchemy (app.final).

## Historial de refactorizacion
- Tag de linea base: fase2-final
- Tag de checkpoint refactorizado: fase3-refactor-domain
- Rama de refactorizacion: refactor/fase3-domain
- Rama de evolucion web: feature/fase3-web

## Informe tecnico
- docs/Informe_Final_Fase3_UeesTask.md

## Repositorio
- https://github.com/oscarandresbro40/UeesTask-Fase2

## Nota de seguridad
- No usar contrasenas demostrativas en produccion.
- Configurar secretos y conexion mediante variables de entorno.
- Proyecto academico: no se declara listo para produccion.
