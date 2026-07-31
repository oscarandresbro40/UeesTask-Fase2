from datetime import datetime, timedelta
from io import BytesIO

import pytest
from fastapi import UploadFile
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Notification, SubmissionStatus, UserRole
from app.services import (
    DomainError,
    create_course,
    create_task,
    create_user,
    enroll_student,
    grade_submission,
    submit_task,
)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session


def create_academic_context(db):
    teacher = create_user(
        db,
        "María",
        "López",
        "teacher@test.edu",
        "Teacher123!",
        UserRole.TEACHER,
    )
    student = create_user(
        db,
        "Carlos",
        "Mendoza",
        "student@test.edu",
        "Student123!",
        UserRole.STUDENT,
        student_number="TEST-001",
    )
    course = create_course(
        db, "TEST-101", "Curso de prueba", "2026-II", "", teacher.id
    )
    enroll_student(db, course.id, student.id)
    return teacher, student, course


def test_duplicate_email_is_rejected(db):
    create_user(
        db, "Ana", "Paz", "ana@test.edu", "Password123!", UserRole.ADMIN
    )
    with pytest.raises(DomainError, match="correo"):
        create_user(
            db, "Otra", "Persona", "ana@test.edu", "Password123!", UserRole.ADMIN
        )


def test_complete_task_submission_and_grading_flow(db, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.UPLOAD_ROOT", tmp_path)
    teacher, student, course = create_academic_context(db)
    due = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
    task = create_task(
        db, teacher, course.id, "Proyecto", "Entregar solución", due, 25, None
    )
    upload = UploadFile(filename="proyecto.pdf", file=BytesIO(b"contenido"))
    submission = submit_task(db, student, task.id, "Trabajo terminado", upload)
    graded = grade_submission(db, teacher, submission.id, 95, "Excelente")

    assert graded.status == SubmissionStatus.GRADED
    assert graded.grade == 95
    assert graded.feedback == "Excelente"
    assert db.scalar(select(func.count(Notification.id))) == 3


def test_unenrolled_student_cannot_submit(db, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.UPLOAD_ROOT", tmp_path)
    teacher, _, course = create_academic_context(db)
    outsider = create_user(
        db,
        "Luis",
        "Vera",
        "outsider@test.edu",
        "Student123!",
        UserRole.STUDENT,
        student_number="TEST-002",
    )
    due = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
    task = create_task(db, teacher, course.id, "Proyecto", "Descripción", due, 20, None)
    upload = UploadFile(filename="archivo.pdf", file=BytesIO(b"contenido"))
    with pytest.raises(DomainError, match="matriculado"):
        submit_task(db, outsider, task.id, "", upload)
