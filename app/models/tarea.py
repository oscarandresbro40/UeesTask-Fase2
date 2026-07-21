from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, List


class EstadoTarea(str, Enum):
    PENDIENTE = "PENDIENTE"
    PUBLICADA = "PUBLICADA"
    VENCIDA = "VENCIDA"
    CERRADA = "CERRADA"


@dataclass
class Tarea:
    id_tarea: int
    titulo: str
    descripcion: str
    fecha_entrega: datetime
    ponderacion: float
    curso_id: int
    docente_id: int
    estado: EstadoTarea = EstadoTarea.PUBLICADA
    recursos: List[str] = field(default_factory=list)
    observadores: List[Any] = field(default_factory=list, repr=False)

    def esta_vencida(self) -> bool:
        return datetime.now() > self.fecha_entrega

    def agregar_observador(self, observador: Any) -> None:
        if observador not in self.observadores:
            self.observadores.append(observador)

    def eliminar_observador(self, observador: Any) -> None:
        if observador in self.observadores:
            self.observadores.remove(observador)

    def notificar_observadores(self, evento: str, datos: dict) -> None:
        for observador in self.observadores:
            observador.actualizar(evento, datos)
