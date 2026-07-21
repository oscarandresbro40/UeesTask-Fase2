from datetime import datetime, timedelta

from app.controllers.controlador_tareas import ControladorTareas
from app.models.curso import Curso
from app.models.usuario import Docente, Estudiante
from app.notifications.servicio_notificaciones import ServicioNotificaciones
from app.repositories.repositorio_memoria import RepositorioMemoria
from app.services.gestor_tareas import GestorTareas


def ejecutar_demo() -> None:
    repositorio = RepositorioMemoria()
    notificador = ServicioNotificaciones()
    gestor = GestorTareas(repositorio, notificador)
    controlador = ControladorTareas(gestor)

    docente = Docente(
        id_usuario=1,
        nombre="María",
        apellido="López",
        email="maria.lopez@uees.edu.ec",
        password="Docente123",
        especialidad="Desarrollo de Software",
    )

    estudiante = Estudiante(
        id_usuario=2,
        nombre="Carlos",
        apellido="Mendoza",
        email="carlos.mendoza@uees.edu.ec",
        password="Estudiante123",
        matricula="UEES-2026-001",
        carrera="Ingeniería en Computación",
    )

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

    print("\n=== UEESTASK — FASE 2 ===")

    tarea = controlador.crear_tarea(
        docente=docente,
        curso_id=curso.id_curso,
        titulo="Implementación de casos de uso",
        descripcion="Desarrollar los tres casos de uso principales de UeesTask.",
        fecha_entrega=datetime.now() + timedelta(days=7),
        ponderacion=25,
        recursos=["guia_fase2.pdf"],
    )
    print(f"[CU-04] Tarea creada: {tarea.titulo}")

    entrega = controlador.entregar_tarea(
        estudiante=estudiante,
        tarea_id=tarea.id_tarea,
        archivo="fase2_grupo.zip",
        comentario="Adjuntamos la implementación solicitada.",
    )
    print(f"[CU-07] Entrega registrada: {entrega.archivo}")

    calificada = controlador.calificar_entrega(
        docente=docente,
        entrega_id=entrega.id_entrega,
        nota=95,
        retroalimentacion="Implementación correcta y bien estructurada.",
    )
    print(f"[CU-08] Entrega calificada: {calificada.calificacion}/100")

    print("\nNotificaciones generadas:")
    for notificacion in notificador.notificaciones:
        print(
            f"- {notificacion.destinatario} | "
            f"{notificacion.asunto} | {notificacion.mensaje}"
        )


if __name__ == "__main__":
    ejecutar_demo()
