from datetime import datetime

from app.models.entrega import Entrega, EstadoEntrega
from app.models.tarea import Tarea
from app.models.usuario import Docente, Estudiante


class GestorTareas:
    def __init__(self, repositorio, servicio_notificaciones) -> None:
        self.repositorio = repositorio
        self.servicio_notificaciones = servicio_notificaciones
        self.siguiente_tarea_id = 1
        self.siguiente_entrega_id = 1

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
        # Código base deliberadamente extenso para el diagnóstico de Fase 2.
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
        if ponderacion <= 0 or ponderacion > 100:
            raise ValueError("La ponderación debe estar entre 1 y 100")

        curso = self.repositorio.obtener_curso(curso_id)
        if curso is None:
            raise LookupError("El curso no existe")
        if curso.docente_id != docente.id_usuario:
            raise PermissionError("El docente no está asignado al curso")

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

        tarea.agregar_observador(self.servicio_notificaciones)
        self.repositorio.guardar_tarea(tarea)
        tarea.notificar_observadores(
            "TAREA_CREADA",
            {
                "titulo": tarea.titulo,
                "fecha_entrega": tarea.fecha_entrega.strftime("%Y-%m-%d %H:%M"),
                "destinatario": f"curso-{curso.id_curso}",
            },
        )
        return tarea

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
        if estudiante is None:
            raise ValueError("El estudiante es obligatorio")
        if tarea_id is None or tarea_id <= 0:
            raise ValueError("El identificador de la tarea no es válido")
        if archivo is None or archivo.strip() == "":
            raise ValueError("Debe adjuntar un archivo")
        if comentario is None:
            comentario = ""

        tarea = self.repositorio.obtener_tarea(tarea_id)
        if tarea is None:
            raise LookupError("La tarea no existe")

        curso = self.repositorio.obtener_curso(tarea.curso_id)
        if curso is None:
            raise LookupError("El curso relacionado no existe")
        if estudiante.id_usuario not in curso.estudiantes_ids:
            raise PermissionError("El estudiante no está matriculado en el curso")
        if tarea.esta_vencida():
            raise ValueError("La tarea está vencida")
        if self.repositorio.buscar_entrega(tarea_id, estudiante.id_usuario):
            raise ValueError("El estudiante ya registró una entrega para esta tarea")

        entrega = Entrega(
            id_entrega=self.siguiente_entrega_id,
            tarea_id=tarea_id,
            estudiante_id=estudiante.id_usuario,
            archivo=archivo.strip(),
            fecha=datetime.now(),
            comentario=comentario.strip(),
        )
        self.siguiente_entrega_id += 1

        entrega.agregar_observador(self.servicio_notificaciones)
        self.repositorio.guardar_entrega(entrega)
        entrega.notificar_observadores(
            "ENTREGA_REGISTRADA",
            {
                "archivo": entrega.archivo,
                "destinatario": estudiante.email,
            },
        )
        return entrega

    def calificar_entrega(
        self,
        docente: Docente,
        entrega_id: int,
        nota: float,
        retroalimentacion: str,
    ) -> Entrega:
        if docente is None:
            raise ValueError("El docente es obligatorio")
        if entrega_id is None or entrega_id <= 0:
            raise ValueError("El identificador de la entrega no es válido")
        if nota is None:
            raise ValueError("La nota es obligatoria")
        if nota < 0 or nota > 100:
            raise ValueError("La nota debe estar entre 0 y 100")
        if retroalimentacion is None:
            retroalimentacion = ""
        if len(retroalimentacion) > 500:
            raise ValueError("La retroalimentación supera el máximo permitido")

        entrega = self.repositorio.obtener_entrega(entrega_id)
        if entrega is None:
            raise LookupError("La entrega no existe")

        tarea = self.repositorio.obtener_tarea(entrega.tarea_id)
        if tarea is None:
            raise LookupError("La tarea relacionada no existe")
        if tarea.docente_id != docente.id_usuario:
            raise PermissionError("El docente no puede calificar esta entrega")
        if entrega.estado == EstadoEntrega.CALIFICADA:
            raise ValueError("La entrega ya fue calificada")

        estudiante = self.repositorio.obtener_usuario(entrega.estudiante_id)
        if estudiante is None:
            raise LookupError("El estudiante no existe")

        entrega.calificacion = nota
        entrega.retroalimentacion = retroalimentacion.strip()
        entrega.estado = EstadoEntrega.CALIFICADA
        self.repositorio.guardar_entrega(entrega)

        if self.servicio_notificaciones not in entrega.observadores:
            entrega.agregar_observador(self.servicio_notificaciones)

        entrega.notificar_observadores(
            "ENTREGA_CALIFICADA",
            {
                "nota": nota,
                "retroalimentacion": entrega.retroalimentacion,
                "destinatario": estudiante.email,
            },
        )
        return entrega
