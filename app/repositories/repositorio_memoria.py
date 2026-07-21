from typing import Dict, Optional

from app.models.curso import Curso
from app.models.entrega import Entrega
from app.models.tarea import Tarea
from app.models.usuario import Usuario


class RepositorioMemoria:
    def __init__(self) -> None:
        self.usuarios: Dict[int, Usuario] = {}
        self.cursos: Dict[int, Curso] = {}
        self.tareas: Dict[int, Tarea] = {}
        self.entregas: Dict[int, Entrega] = {}

    def guardar_usuario(self, usuario: Usuario) -> None:
        self.usuarios[usuario.id_usuario] = usuario

    def obtener_usuario(self, usuario_id: int) -> Optional[Usuario]:
        return self.usuarios.get(usuario_id)

    def guardar_curso(self, curso: Curso) -> None:
        self.cursos[curso.id_curso] = curso

    def obtener_curso(self, curso_id: int) -> Optional[Curso]:
        return self.cursos.get(curso_id)

    def guardar_tarea(self, tarea: Tarea) -> None:
        self.tareas[tarea.id_tarea] = tarea

    def obtener_tarea(self, tarea_id: int) -> Optional[Tarea]:
        return self.tareas.get(tarea_id)

    def listar_tareas_por_curso(self, curso_id: int) -> list[Tarea]:
        return [t for t in self.tareas.values() if t.curso_id == curso_id]

    def guardar_entrega(self, entrega: Entrega) -> None:
        self.entregas[entrega.id_entrega] = entrega

    def obtener_entrega(self, entrega_id: int) -> Optional[Entrega]:
        return self.entregas.get(entrega_id)

    def buscar_entrega(self, tarea_id: int, estudiante_id: int) -> Optional[Entrega]:
        for entrega in self.entregas.values():
            if entrega.tarea_id == tarea_id and entrega.estudiante_id == estudiante_id:
                return entrega
        return None

    def listar_entregas_por_tarea(self, tarea_id: int) -> list[Entrega]:
        return [e for e in self.entregas.values() if e.tarea_id == tarea_id]
