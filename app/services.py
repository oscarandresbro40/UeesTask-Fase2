import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Course,
    Enrollment,
    Notification,
    Submission,
    SubmissionStatus,
    Task,
    TaskResource,
    TaskStatus,
    User,
    UserRole,
)
from app.security import hash_password


UPLOAD_ROOT = Path("uploads")
ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".txt", ".zip", ".rar", ".7z", ".png", ".jpg", ".jpeg",
}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024


class DomainError(ValueError):
    pass


def create_user(
    db: Session,
    first_name: str,
    last_name: str,
    email: str,
    password: str,
    role: UserRole,
    specialty: str = "",
    student_number: str = "",
    program: str = "",
) -> User:
    email = email.strip().lower()
    if not first_name.strip() or not last_name.strip():
        raise DomainError("El nombre y el apellido son obligatorios.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise DomainError("El correo electrónico no es válido.")
    if db.scalar(select(User.id).where(User.email == email)):
        raise DomainError("Ya existe un usuario con ese correo.")
    if len(password) < 8:
        raise DomainError("La contraseña debe tener al menos 8 caracteres.")
    if role == UserRole.STUDENT and not student_number.strip():
        raise DomainError("La matrícula es obligatoria para estudiantes.")
    if student_number.strip() and db.scalar(
        select(User.id).where(User.student_number == student_number.strip())
    ):
        raise DomainError("La matrícula ya está registrada.")

    user = User(
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        email=email,
        password_hash=hash_password(password),
        role=role,
        specialty=specialty.strip() or None,
        student_number=student_number.strip() or None,
        program=program.strip() or None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_course(
    db: Session,
    code: str,
    name: str,
    period: str,
    description: str,
    teacher_id: int,
) -> Course:
    if not code.strip() or not name.strip() or not period.strip():
        raise DomainError("Código, nombre y período son obligatorios.")
    if db.scalar(select(Course.id).where(Course.code == code.strip().upper())):
        raise DomainError("Ya existe un curso con ese código.")
    teacher = db.get(User, teacher_id)
    if not teacher or teacher.role != UserRole.TEACHER:
        raise DomainError("Debe seleccionar un docente válido.")
    course = Course(
        code=code.strip().upper(),
        name=name.strip(),
        period=period.strip(),
        description=description.strip(),
        teacher_id=teacher.id,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def enroll_student(db: Session, course_id: int, student_id: int) -> Enrollment:
    course = db.get(Course, course_id)
    student = db.get(User, student_id)
    if not course:
        raise DomainError("El curso no existe.")
    if not student or student.role != UserRole.STUDENT:
        raise DomainError("Debe seleccionar un estudiante válido.")
    if db.get(Enrollment, (course_id, student_id)):
        raise DomainError("El estudiante ya está matriculado en este curso.")
    enrollment = Enrollment(course_id=course_id, student_id=student_id)
    db.add(enrollment)
    db.commit()
    return enrollment


def parse_local_datetime(value: str) -> datetime:
    try:
        local_value = datetime.fromisoformat(value)
    except ValueError as exc:
        raise DomainError("La fecha de entrega no es válida.") from exc
    if local_value.tzinfo is None:
        local_value = local_value.replace(tzinfo=ZoneInfo("America/Guayaquil"))
    return local_value.astimezone(timezone.utc)


def save_upload(upload: UploadFile, category: str) -> tuple[str, str]:
    original_name = Path(upload.filename or "").name
    extension = Path(original_name).suffix.lower()
    if not original_name or extension not in ALLOWED_EXTENSIONS:
        raise DomainError("El tipo de archivo no está permitido.")
    target_dir = UPLOAD_ROOT / category
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{uuid4().hex}{extension}"
    total = 0
    try:
        with target.open("wb") as output:
            while chunk := upload.file.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise DomainError("El archivo supera el límite de 15 MB.")
                output.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:
        upload.file.close()
    return original_name, str(target)


def create_task(
    db: Session,
    teacher: User,
    course_id: int,
    title: str,
    description: str,
    due_value: str,
    weight: float,
    resource: UploadFile | None,
) -> Task:
    course = db.get(Course, course_id)
    if not course:
        raise DomainError("El curso no existe.")
    if course.teacher_id != teacher.id:
        raise DomainError("El docente no está asignado a este curso.")
    if not title.strip() or not description.strip():
        raise DomainError("El título y la descripción son obligatorios.")
    due_at = parse_local_datetime(due_value)
    if due_at <= datetime.now(timezone.utc):
        raise DomainError("La fecha de entrega debe ser futura.")
    if not 1 <= weight <= 100:
        raise DomainError("La ponderación debe estar entre 1 y 100.")
    task = Task(
        course_id=course.id,
        teacher_id=teacher.id,
        title=title.strip(),
        description=description.strip(),
        due_at=due_at,
        weight=weight,
        status=TaskStatus.PUBLISHED,
    )
    db.add(task)
    db.flush()
    if resource and resource.filename:
        original_name, storage_path = save_upload(resource, "recursos")
        db.add(
            TaskResource(
                task_id=task.id,
                original_name=original_name,
                storage_path=storage_path,
            )
        )
    student_ids = db.scalars(
        select(Enrollment.student_id).where(Enrollment.course_id == course.id)
    ).all()
    for student_id in student_ids:
        db.add(
            Notification(
                user_id=student_id,
                event_type="TAREA_CREADA",
                title="Nueva tarea académica",
                message=f"Se publicó «{task.title}» en {course.name}.",
            )
        )
    db.commit()
    db.refresh(task)
    return task


def submit_task(
    db: Session,
    student: User,
    task_id: int,
    comment: str,
    uploaded_file: UploadFile,
) -> Submission:
    task = db.get(Task, task_id)
    if not task:
        raise DomainError("La tarea no existe.")
    if not db.get(Enrollment, (task.course_id, student.id)):
        raise DomainError("El estudiante no está matriculado en el curso.")
    due_at = task.due_at
    if due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=timezone.utc)
    if due_at <= datetime.now(timezone.utc):
        raise DomainError("La tarea está vencida.")
    if db.scalar(
        select(Submission.id).where(
            Submission.task_id == task.id,
            Submission.student_id == student.id,
        )
    ):
        raise DomainError("Ya registraste una entrega para esta tarea.")
    original_name, storage_path = save_upload(uploaded_file, "entregas")
    submission = Submission(
        task_id=task.id,
        student_id=student.id,
        original_name=original_name,
        storage_path=storage_path,
        comment=comment.strip(),
        status=SubmissionStatus.SUBMITTED,
    )
    db.add(submission)
    db.add(
        Notification(
            user_id=task.teacher_id,
            event_type="ENTREGA_REGISTRADA",
            title="Nueva entrega",
            message=f"{student.full_name} entregó «{task.title}».",
        )
    )
    db.commit()
    db.refresh(submission)
    return submission


def grade_submission(
    db: Session,
    teacher: User,
    submission_id: int,
    grade: float,
    feedback: str,
) -> Submission:
    submission = db.get(Submission, submission_id)
    if not submission:
        raise DomainError("La entrega no existe.")
    if submission.task.teacher_id != teacher.id:
        raise DomainError("El docente no puede calificar esta entrega.")
    if submission.status == SubmissionStatus.GRADED:
        raise DomainError("La entrega ya fue calificada.")
    if not 0 <= grade <= 100:
        raise DomainError("La nota debe estar entre 0 y 100.")
    if len(feedback) > 500:
        raise DomainError("La retroalimentación supera los 500 caracteres.")
    submission.grade = grade
    submission.feedback = feedback.strip()
    submission.status = SubmissionStatus.GRADED
    submission.graded_at = datetime.now(timezone.utc)
    db.add(
        Notification(
            user_id=submission.student_id,
            event_type="ENTREGA_CALIFICADA",
            title="Actividad calificada",
            message=f"Tu entrega de «{submission.task.title}» recibió {grade:g}/100.",
        )
    )
    db.commit()
    db.refresh(submission)
    return submission
