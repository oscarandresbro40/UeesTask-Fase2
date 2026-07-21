from dataclasses import dataclass


@dataclass
class Usuario:
    id_usuario: int
    nombre: str
    apellido: str
    email: str
    password: str

    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"


@dataclass
class Docente(Usuario):
    especialidad: str


@dataclass
class Estudiante(Usuario):
    matricula: str
    carrera: str


@dataclass
class Administrador(Usuario):
    cargo: str = "Administrador"
