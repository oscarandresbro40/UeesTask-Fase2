import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    TEACHER = "DOCENTE"
    STUDENT = "ESTUDIANTE"


class TaskStatus(str, enum.Enum):
    PUBLISHED = "PUBLICADA"
    CLOSED = "CERRADA"


class SubmissionStatus(str, enum.Enum):
    SUBMITTED = "ENVIADA"
    GRADED = "CALIFICADA"
    REJECTED = "RECHAZADA"


class User(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="rol_usuario"))
    specialty: Mapped[str | None] = mapped_column(String(160), nullable=True)
    student_number: Mapped[str | None] = mapped_column(
        String(40), unique=True, nullable=True
    )
    program: Mapped[str | None] = mapped_column(String(160), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    taught_courses: Mapped[list["Course"]] = relationship(back_populates="teacher")
    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Course(Base):
    __tablename__ = "cursos"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    period: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(Text, default="")
    teacher_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    teacher: Mapped[User] = relationship(back_populates="taught_courses")
    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )


class Enrollment(Base):
    __tablename__ = "matriculas"

    course_id: Mapped[int] = mapped_column(
        ForeignKey("cursos.id", ondelete="CASCADE"), primary_key=True
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    course: Mapped[Course] = relationship(back_populates="enrollments")
    student: Mapped[User] = relationship(back_populates="enrollments")


class Task(Base):
    __tablename__ = "tareas"
    __table_args__ = (
        CheckConstraint("ponderacion >= 1 AND ponderacion <= 100", name="ck_ponderacion"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("cursos.id"))
    teacher_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    weight: Mapped[float] = mapped_column("ponderacion", Float)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="estado_tarea"), default=TaskStatus.PUBLISHED
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    course: Mapped[Course] = relationship(back_populates="tasks")
    teacher: Mapped[User] = relationship(foreign_keys=[teacher_id])
    resources: Mapped[list["TaskResource"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )


class TaskResource(Base):
    __tablename__ = "recursos_tarea"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tareas.id", ondelete="CASCADE"))
    original_name: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    task: Mapped[Task] = relationship(back_populates="resources")


class Submission(Base):
    __tablename__ = "entregas"
    __table_args__ = (
        UniqueConstraint("task_id", "student_id", name="uq_entrega_tarea_estudiante"),
        CheckConstraint(
            "calificacion IS NULL OR (calificacion >= 0 AND calificacion <= 100)",
            name="ck_calificacion",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tareas.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    original_name: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500))
    comment: Mapped[str] = mapped_column(Text, default="")
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    grade: Mapped[float | None] = mapped_column("calificacion", Float, nullable=True)
    feedback: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="estado_entrega"),
        default=SubmissionStatus.SUBMITTED,
    )
    graded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    task: Mapped[Task] = relationship(back_populates="submissions")
    student: Mapped[User] = relationship()


class Notification(Base):
    __tablename__ = "notificaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(60))
    title: Mapped[str] = mapped_column(String(180))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[User] = relationship(back_populates="notifications")
