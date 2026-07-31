from datetime import datetime

from app.models.entrega import Entrega
from app.models.usuario import Estudiante
from app.utils.validador_dominio import ValidadorDominio


class GestorEntregas:
    """Responsable del caso de uso CU-07: entregar una tarea."""

    def __init__(self, repositorio, publicador_eventos) -> None:
        self.repositorio = repositorio
        self.publicador_eventos = publicador_eventos
        self.siguiente_entrega_id = 1

    def entregar_tarea(
        self,
        estudiante: Estudiante,
        tarea_id: int,
        archivo: str,
        comentario: str = "",
    ) -> Entrega:
        ValidadorDominio.requerido(estudiante, "El estudiante es obligatorio")
        ValidadorDominio.identificador_positivo(
            tarea_id, "El identificador de la tarea no es válido"
        )
        ValidadorDominio.texto_requerido(archivo, "Debe adjuntar un archivo")
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

        self.repositorio.guardar_entrega(entrega)
        self.publicador_eventos.publicar(
            entrega,
            "ENTREGA_REGISTRADA",
            {
                "archivo": entrega.archivo,
                "destinatario": estudiante.email,
            },
        )
        return entrega
