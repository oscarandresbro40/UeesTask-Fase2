from datetime import datetime, timedelta
import pytest

from app.models.curso import Curso
from app.models.usuario import Docente, Estudiante
from app.notifications.servicio_notificaciones import ServicioNotificaciones
from app.repositories.repositorio_memoria import RepositorioMemoria
from app.services.gestor_tareas import GestorTareas


@pytest.fixture
def repositorio():
    return RepositorioMemoria()


@pytest.fixture
def notificador():
    return ServicioNotificaciones()


@pytest.fixture
def gestor(repositorio, notificador):
    return GestorTareas(repositorio, notificador)


@pytest.fixture
def docente():
    return Docente(
        id_usuario=1,
        nombre="María",
        apellido="López",
        email="maria.lopez@uees.edu.ec",
        password="Docente123",
        especialidad="Desarrollo de Software",
    )


@pytest.fixture
def otro_docente():
    return Docente(
        id_usuario=99,
        nombre="Pedro",
        apellido="Vera",
        email="pedro.vera@uees.edu.ec",
        password="Docente999",
        especialidad="Algoritmos",
    )


@pytest.fixture
def estudiante():
    return Estudiante(
        id_usuario=2,
        nombre="Carlos",
        apellido="Mendoza",
        email="carlos.mendoza@uees.edu.ec",
        password="Estudiante123",
        matricula="UEES-2026-001",
        carrera="Ingeniería en Computación",
    )


@pytest.fixture
def otro_estudiante():
    return Estudiante(
        id_usuario=3,
        nombre="Ana",
        apellido="Torres",
        email="ana.torres@uees.edu.ec",
        password="Estudiante456",
        matricula="UEES-2026-002",
        carrera="Ingeniería en Computación",
    )


@pytest.fixture
def curso(repositorio, docente, estudiante):
    curso = Curso(
        id_curso=1,
        nombre="Desarrollo de Software",
        periodo="2026-II",
        docente_id=docente.id_usuario,
    )
    curso.matricular_estudiante(estudiante.id_usuario)
    repositorio.guardar_usuario(docente)
    repositorio.guardar_usuario(estudiante)
    repositorio.guardar_curso(curso)
    return curso


@pytest.fixture
def tarea_valida(gestor, docente, curso):
    return gestor.crear_tarea(
        docente=docente,
        curso_id=curso.id_curso,
        titulo="Implementación UML",
        descripcion="Desarrollar los diagramas y el código base.",
        fecha_entrega=datetime.now() + timedelta(days=5),
        ponderacion=25,
        recursos=["guia.pdf"],
    )


@pytest.fixture
def entrega_valida(gestor, estudiante, tarea_valida):
    return gestor.entregar_tarea(
        estudiante=estudiante,
        tarea_id=tarea_valida.id_tarea,
        archivo="entrega.zip",
        comentario="Adjunto el trabajo.",
    )
