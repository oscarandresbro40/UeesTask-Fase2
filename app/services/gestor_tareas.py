from datetime import datetime

from app.models.entrega import Entrega
from app.models.tarea import Tarea
from app.models.usuario import Docente, Estudiante
from app.services.gestor_calificaciones import GestorCalificaciones
from app.services.gestor_entregas import GestorEntregas
from app.utils.constantes import (
    FORMATO_FECHA_NOTIFICACION,
    PONDERACION_MAXIMA,
    PONDERACION_MINIMA,
)


class GestorTareas:
    def __init__(self, repositorio, servicio_notificaciones) -> None:
        self.repositorio = repositorio
        self.servicio_notificaciones = servicio_notificaciones
        self.siguiente_tarea_id = 1
        self.gestor_entregas = GestorEntregas(repositorio, servicio_notificaciones)
        self.gestor_calificaciones = GestorCalificaciones(
            repositorio, servicio_notificaciones
        )

    def crear_tarea(
        self,
        docente: Docente,
        curso_id: int,
        titulo: str,
        descripcion: str,
        fecha_entrega: datetime,
        ponderacion: float,
        recursos: list[str] | None = None,
    ) -> Tarea:
        """Implementa CU-04 para que un docente cree una tarea en un curso asignado.

        Valida datos obligatorios, fecha futura, ponderación y autorización del
        docente; luego guarda la tarea y notifica a los estudiantes del curso.
        """
        self._validar_datos_tarea(
            docente, curso_id, titulo, descripcion, fecha_entrega, ponderacion
        )
        curso = self._obtener_curso_del_docente(curso_id, docente)
        tarea = self._construir_tarea(
            docente,
            curso_id,
            titulo,
            descripcion,
            fecha_entrega,
            ponderacion,
            recursos,
        )
        self._guardar_y_notificar_tarea(tarea, curso.id_curso)
        return tarea

    def _validar_datos_tarea(
        self,
        docente: Docente,
        curso_id: int,
        titulo: str,
        descripcion: str,
        fecha_entrega: datetime,
        ponderacion: float,
    ) -> None:
        if docente is None:
            raise ValueError("El docente es obligatorio")
        if curso_id is None or curso_id <= 0:
            raise ValueError("El curso es obligatorio")
        if titulo is None or titulo.strip() == "":
            raise ValueError("El título es obligatorio")
        if descripcion is None or descripcion.strip() == "":
            raise ValueError("La descripción es obligatoria")
        if fecha_entrega is None:
            raise ValueError("La fecha de entrega es obligatoria")
        if fecha_entrega <= datetime.now():
            raise ValueError("La fecha de entrega debe ser futura")
        if ponderacion is None:
            raise ValueError("La ponderación es obligatoria")
        if ponderacion < PONDERACION_MINIMA or ponderacion > PONDERACION_MAXIMA:
            raise ValueError("La ponderación debe estar entre 1 y 100")

    def _obtener_curso_del_docente(self, curso_id: int, docente: Docente):
        curso = self.repositorio.obtener_curso(curso_id)
        if curso is None:
            raise LookupError("El curso no existe")
        if curso.docente_id != docente.id_usuario:
            raise PermissionError("El docente no está asignado al curso")
        return curso

    def _construir_tarea(
        self,
        docente: Docente,
        curso_id: int,
        titulo: str,
        descripcion: str,
        fecha_entrega: datetime,
        ponderacion: float,
        recursos: list[str] | None,
    ) -> Tarea:
        tarea = Tarea(
            id_tarea=self.siguiente_tarea_id,
            titulo=titulo.strip(),
            descripcion=descripcion.strip(),
            fecha_entrega=fecha_entrega,
            ponderacion=ponderacion,
            curso_id=curso_id,
            docente_id=docente.id_usuario,
            recursos=recursos or [],
        )
        self.siguiente_tarea_id += 1
        return tarea

    def _guardar_y_notificar_tarea(self, tarea: Tarea, curso_id: int) -> None:
        tarea.agregar_observador(self.servicio_notificaciones)
        self.repositorio.guardar_tarea(tarea)
        tarea.notificar_observadores(
            "TAREA_CREADA",
            {
                "titulo": tarea.titulo,
                "fecha_entrega": tarea.fecha_entrega.strftime(FORMATO_FECHA_NOTIFICACION),
                "destinatario": f"curso-{curso_id}",
            },
        )

    def entregar_tarea(
        self,
        estudiante: Estudiante,
        tarea_id: int,
        archivo: str,
        comentario: str = "",
    ) -> Entrega:
        """Implementa CU-07 para registrar la entrega de una tarea.

        Verifica existencia de la tarea, matrícula del estudiante, fecha límite,
        archivo adjunto y posibles entregas duplicadas; luego guarda la entrega
        y genera una notificación.
        """
        return self.gestor_entregas.entregar_tarea(
            estudiante, tarea_id, archivo, comentario
        )

    def calificar_entrega(
        self,
        docente: Docente,
        entrega_id: int,
        nota: float,
        retroalimentacion: str,
    ) -> Entrega:
        """Implementa CU-08 para que un docente califique una entrega.

        Valida la nota, la autorización del docente y que la entrega no haya
        sido calificada previamente; luego registra la retroalimentación, cambia
        el estado a CALIFICADA y notifica al estudiante.
        """
        return self.gestor_calificaciones.calificar_entrega(
            docente, entrega_id, nota, retroalimentacion
        )
