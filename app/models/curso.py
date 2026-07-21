from dataclasses import dataclass, field
from typing import List


@dataclass
class Curso:
    id_curso: int
    nombre: str
    periodo: str
    docente_id: int
    estudiantes_ids: List[int] = field(default_factory=list)

    def matricular_estudiante(self, estudiante_id: int) -> None:
        if estudiante_id not in self.estudiantes_ids:
            self.estudiantes_ids.append(estudiante_id)
