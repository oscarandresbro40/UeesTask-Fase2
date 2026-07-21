from dataclasses import dataclass
from datetime import datetime


@dataclass
class Notificacion:
    id_notificacion: int
    destinatario: str
    asunto: str
    mensaje: str
    fecha: datetime
