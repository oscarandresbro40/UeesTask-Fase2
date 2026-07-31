from app.models.entrega import Entrega, EstadoEntrega
from app.models.usuario import Docente
from app.utils.constantes import (
    MAX_CARACTERES_RETROALIMENTACION,
    NOTA_MAXIMA,
    NOTA_MINIMA,
)
from app.utils.validador_dominio import ValidadorDominio


class GestorCalificaciones:
    """Responsable del caso de uso CU-08: calificar una entrega."""

    def __init__(self, repositorio, publicador_eventos) -> None:
        self.repositorio = repositorio
        self.publicador_eventos = publicador_eventos

    def calificar_entrega(
        self,
        docente: Docente,
        entrega_id: int,
        nota: float,
        retroalimentacion: str,
    ) -> Entrega:
        ValidadorDominio.requerido(docente, "El docente es obligatorio")
        ValidadorDominio.identificador_positivo(
            entrega_id, "El identificador de la entrega no es válido"
        )
        nota_invalida = nota is None or not NOTA_MINIMA <= nota <= NOTA_MAXIMA
        if nota_invalida:
            mensaje = (
                "La nota es obligatoria"
                if nota is None
                else "La nota debe estar entre 0 y 100"
            )
            raise ValueError(mensaje)
        if retroalimentacion is None:
            retroalimentacion = ""
        ValidadorDominio.longitud_maxima(
            retroalimentacion,
            MAX_CARACTERES_RETROALIMENTACION,
            "La retroalimentación supera el máximo permitido",
        )

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

        self.publicador_eventos.publicar(
            entrega,
            "ENTREGA_CALIFICADA",
            {
                "nota": nota,
                "retroalimentacion": entrega.retroalimentacion,
                "destinatario": estudiante.email,
            },
        )
        return entrega
