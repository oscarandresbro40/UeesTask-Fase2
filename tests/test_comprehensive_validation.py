from datetime import datetime, timedelta
from io import BytesIO

import pytest
from fastapi import UploadFile
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Enrollment, Notification, SubmissionStatus, UserRole
from app.services import (
    DomainError, create_course, create_task, create_user, enroll_student,
    grade_submission, parse_local_datetime, submit_task,
)


MEMBERS = (
    ("Alexis Omar", "Analuisa Jaramillo"),
    ("Joseline Nathaly", "Duarte León"),
    ("William Adrian", "Cabrera Maldonado"),
    ("Oscar Andrés", "Bernal Rodríguez"),
    ("Christian Omar", "Yaguana Díaz"),
    ("Ronnie Alexie", "Villón Ramírez"),
    ("Edmilson Miguel", "Suárez Rizo"),
)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session


def context(db):
    teacher = create_user(
        db, "Alexis Omar", "Analuisa Jaramillo", "teacher@d4.test",
        "Password123!", UserRole.TEACHER,
    )
    student = create_user(
        db, "Joseline Nathaly", "Duarte León", "student@d4.test",
        "Password123!", UserRole.STUDENT, student_number="D4-T001",
    )
    course = create_course(db, "D4-TST", "Curso D4", "2026-II", "", teacher.id)
    enroll_student(db, course.id, student.id)
    return teacher, student, course


@pytest.mark.parametrize("index,names", tuple(enumerate(MEMBERS, start=1)))
def test_group_member_names_preserve_accents(db, index, names):
    first_name, last_name = names
    user = create_user(
        db, first_name, last_name, f"member{index}@example.test",
        "Password123!", UserRole.STUDENT, student_number=f"D4-M{index:03}",
    )
    assert user.full_name == f"{first_name} {last_name}"


@pytest.mark.parametrize(
    "email,password,message",
    (("correo-invalido", "Password123!", "correo"), ("valid@example.test", "corta", "8")),
)
def test_invalid_registration_is_rejected(db, email, password, message):
    with pytest.raises(DomainError, match=message):
        create_user(db, "Nombre", "Prueba", email, password, UserRole.ADMIN)


def test_student_number_is_required_and_unique(db):
    with pytest.raises(DomainError, match="matr"):
        create_user(
            db, "Sin", "Matrícula", "missing@example.test",
            "Password123!", UserRole.STUDENT,
        )
    create_user(
        db, "Uno", "Estudiante", "one@example.test", "Password123!",
        UserRole.STUDENT, student_number="D4-UNIQUE",
    )
    with pytest.raises(DomainError, match="registrada"):
        create_user(
            db, "Dos", "Estudiante", "two@example.test", "Password123!",
            UserRole.STUDENT, student_number="D4-UNIQUE",
        )


def test_duplicate_email_is_case_insensitive(db):
    create_user(db, "Ana", "Paz", "ana@example.test", "Password123!", UserRole.ADMIN)
    with pytest.raises(DomainError, match="correo"):
        create_user(db, "Otra", "Ana", "ANA@example.test", "Password123!", UserRole.ADMIN)


def test_course_requires_teacher_and_unique_code(db):
    _, student, _ = context(db)
    with pytest.raises(DomainError, match="docente"):
        create_course(db, "INVALID", "Inválido", "2026-II", "", student.id)
    teacher = create_user(
        db, "Oscar", "Bernal", "teacher2@d4.test", "Password123!", UserRole.TEACHER
    )
    create_course(db, "UNIQUE", "Curso único", "2026-II", "", teacher.id)
    with pytest.raises(DomainError, match="código"):
        create_course(db, "unique", "Duplicado", "2026-II", "", teacher.id)


def test_duplicate_enrollment_is_rejected(db):
    _, student, course = context(db)
    with pytest.raises(DomainError, match="matriculado"):
        enroll_student(db, course.id, student.id)


@pytest.mark.parametrize("weight", (0, 101))
def test_task_weight_outside_range_is_rejected(db, weight):
    teacher, _, course = context(db)
    due = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
    with pytest.raises(DomainError, match="ponderación"):
        create_task(db, teacher, course.id, "Tarea", "Descripción", due, weight, None)


def test_past_and_invalid_dates_are_rejected(db):
    teacher, _, course = context(db)
    past = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
    with pytest.raises(DomainError, match="futura"):
        create_task(db, teacher, course.id, "Tarea", "Descripción", past, 20, None)
    with pytest.raises(DomainError, match="válida"):
        parse_local_datetime("fecha-imposible")


def test_teacher_cannot_use_another_course(db):
    _, _, course = context(db)
    outsider = create_user(
        db, "Oscar", "Bernal", "outsider@d4.test", "Password123!", UserRole.TEACHER
    )
    due = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
    with pytest.raises(DomainError, match="asignado"):
        create_task(db, outsider, course.id, "Tarea", "Descripción", due, 20, None)


def test_task_notifies_all_students(db):
    teacher, _, course = context(db)
    second = create_user(
        db, "William", "Cabrera", "second@d4.test", "Password123!",
        UserRole.STUDENT, student_number="D4-T002",
    )
    enroll_student(db, course.id, second.id)
    due = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
    create_task(db, teacher, course.id, "Tarea", "Descripción", due, 20, None)
    assert db.scalar(select(func.count(Notification.id))) == 2


def prepared_submission(db, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.UPLOAD_ROOT", tmp_path)
    teacher, student, course = context(db)
    due = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
    task = create_task(db, teacher, course.id, "Tarea", "Descripción", due, 20, None)
    submission = submit_task(
        db, student, task.id, "Listo",
        UploadFile(filename="entrega.pdf", file=BytesIO(b"contenido")),
    )
    return teacher, student, task, submission


def test_invalid_extension_is_rejected(db, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.UPLOAD_ROOT", tmp_path)
    teacher, student, course = context(db)
    due = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
    task = create_task(db, teacher, course.id, "Tarea", "Descripción", due, 20, None)
    with pytest.raises(DomainError, match="tipo de archivo"):
        submit_task(
            db, student, task.id, "",
            UploadFile(filename="malware.exe", file=BytesIO(b"contenido")),
        )


def test_duplicate_submission_is_rejected(db, tmp_path, monkeypatch):
    _, student, task, _ = prepared_submission(db, tmp_path, monkeypatch)
    with pytest.raises(DomainError, match="Ya registraste"):
        submit_task(
            db, student, task.id, "Segunda",
            UploadFile(filename="segunda.pdf", file=BytesIO(b"dos")),
        )


@pytest.mark.parametrize("grade", (-1, 101))
def test_invalid_grade_is_rejected(db, tmp_path, monkeypatch, grade):
    teacher, _, _, submission = prepared_submission(db, tmp_path, monkeypatch)
    with pytest.raises(DomainError, match="entre 0 y 100"):
        grade_submission(db, teacher, submission.id, grade, "")


def test_wrong_teacher_long_feedback_and_double_grading(
    db, tmp_path, monkeypatch
):
    teacher, _, _, submission = prepared_submission(db, tmp_path, monkeypatch)
    other = create_user(
        db, "Oscar", "Bernal", "other@d4.test", "Password123!", UserRole.TEACHER
    )
    with pytest.raises(DomainError, match="no puede"):
        grade_submission(db, other, submission.id, 90, "")
    with pytest.raises(DomainError, match="500"):
        grade_submission(db, teacher, submission.id, 90, "x" * 501)
    graded = grade_submission(db, teacher, submission.id, 100, "Excelente")
    assert graded.status == SubmissionStatus.GRADED
    with pytest.raises(DomainError, match="ya fue"):
        grade_submission(db, teacher, submission.id, 95, "Cambio")


def test_enrollment_can_be_removed_without_submissions(db):
    _, student, course = context(db)
    enrollment = db.get(Enrollment, (course.id, student.id))
    db.delete(enrollment)
    db.commit()
    assert db.get(Enrollment, (course.id, student.id)) is None
