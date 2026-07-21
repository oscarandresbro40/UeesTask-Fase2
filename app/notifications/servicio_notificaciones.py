from datetime import datetime

from app.models.notificacion import Notificacion
from app.notifications.observer import Observador


class ServicioNotificaciones(Observador):
    def __init__(self) -> None:
        self.notificaciones: list[Notificacion] = []
        self.siguiente_id = 1

    def actualizar(self, evento: str, datos: dict) -> None:
        if evento == "TAREA_CREADA":
            asunto = "Nueva tarea académica"
            mensaje = (
                f"Se publicó la tarea '{datos['titulo']}' "
                f"con fecha límite {datos['fecha_entrega']}."
            )
            destinatario = datos.get("destinatario", "estudiantes-del-curso")
        elif evento == "ENTREGA_REGISTRADA":
            asunto = "Entrega registrada"
            mensaje = f"El archivo '{datos['archivo']}' fue registrado correctamente."
            destinatario = datos["destinatario"]
        elif evento == "ENTREGA_CALIFICADA":
            asunto = "Actividad calificada"
            mensaje = (
                f"La entrega recibió {datos['nota']}/100. "
                f"Retroalimentación: {datos['retroalimentacion']}"
            )
            destinatario = datos["destinatario"]
        else:
            asunto = "Notificación UeesTask"
            mensaje = str(datos)
            destinatario = datos.get("destinatario", "usuario")

        notificacion = Notificacion(
            id_notificacion=self.siguiente_id,
            destinatario=destinatario,
            asunto=asunto,
            mensaje=mensaje,
            fecha=datetime.now(),
        )
        self.siguiente_id += 1
        self.notificaciones.append(notificacion)
