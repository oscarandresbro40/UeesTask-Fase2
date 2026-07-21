class ControladorTareas:
    def __init__(self, gestor_tareas) -> None:
        self.gestor_tareas = gestor_tareas

    def crear_tarea(self, **datos):
        return self.gestor_tareas.crear_tarea(**datos)

    def entregar_tarea(self, **datos):
        return self.gestor_tareas.entregar_tarea(**datos)

    def calificar_entrega(self, **datos):
        return self.gestor_tareas.calificar_entrega(**datos)
