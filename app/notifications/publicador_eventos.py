class PublicadorEventos:
    """Registra el observador y publica eventos de dominio.

    Evita que los servicios de aplicacion conozcan los detalles internos
    del patron Observer.
    """

    def __init__(self, observador) -> None:
        self.observador = observador

    def publicar(self, entidad, evento: str, datos: dict) -> None:
        entidad.agregar_observador(self.observador)
        entidad.notificar_observadores(evento, datos)
