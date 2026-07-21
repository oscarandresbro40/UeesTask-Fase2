from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Any, List


class EstadoEntrega(str, Enum):
    ENVIADA = "ENVIADA"
    CALIFICADA = "CALIFICADA"
    RECHAZADA = "RECHAZADA"


@dataclass
class Entrega:
    id_entrega: int
    tarea_id: int
    estudiante_id: int
    archivo: str
    fecha: datetime
    comentario: str = ""
    calificacion: Optional[float] = None
    retroalimentacion: str = ""
    estado: EstadoEntrega = EstadoEntrega.ENVIADA
    observadores: List[Any] = None

    def __post_init__(self) -> None:
        if self.observadores is None:
            self.observadores = []

    def agregar_observador(self, observador: Any) -> None:
        if observador not in self.observadores:
            self.observadores.append(observador)

    def notificar_observadores(self, evento: str, datos: dict) -> None:
        for observador in self.observadores:
            observador.actualizar(evento, datos)
