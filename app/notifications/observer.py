from abc import ABC, abstractmethod


class Observador(ABC):
    @abstractmethod
    def actualizar(self, evento: str, datos: dict) -> None:
        raise NotImplementedError
