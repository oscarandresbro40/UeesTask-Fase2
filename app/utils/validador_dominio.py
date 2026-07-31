from datetime import datetime


class ValidadorDominio:
    """Centraliza validaciones comunes sin depender de repositorios."""

    @staticmethod
    def requerido(valor, mensaje: str) -> None:
        if valor is None:
            raise ValueError(mensaje)

    @staticmethod
    def identificador_positivo(valor: int, mensaje: str) -> None:
        if valor is None or valor <= 0:
            raise ValueError(mensaje)

    @staticmethod
    def texto_requerido(valor: str, mensaje: str) -> None:
        if valor is None or valor.strip() == "":
            raise ValueError(mensaje)

    @staticmethod
    def fecha_futura(valor: datetime, mensaje: str) -> None:
        if valor is None or valor <= datetime.now():
            raise ValueError(mensaje)

    @staticmethod
    def longitud_maxima(valor: str, maximo: int, mensaje: str) -> None:
        if len(valor) > maximo:
            raise ValueError(mensaje)
