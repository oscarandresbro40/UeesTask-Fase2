from datetime import datetime

from app.models.entrega import Entrega
from app.models.usuario import Estudiante


class GestorEntregas:
    """Responsable del caso de uso CU-07: entregar una tarea."""

    def __init__(self, repositorio, servicio_notificaciones) -> None:
        self.repositorio = repositorio
        self.servicio_notificaciones = servicio_notificaciones
        self.siguiente_entrega_id = 1

    def entregar_tarea(
        self,
        estudiante: Estudiante,
        tarea_id: int,
        archivo: str,
        comentario: str = "",
    ) -> Entrega:
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
