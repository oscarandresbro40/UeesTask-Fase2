from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.full import app
from app.models import Course, Enrollment, Submission, SubmissionStatus, Task, User, UserRole
from app.security import hash_password


@pytest.fixture
def web_context(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.UPLOAD_ROOT", tmp_path)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        teacher = User(
            first_name="María",
            last_name="López",
            email="teacher@http.test",
            password_hash=hash_password("Teacher123!"),
            role=UserRole.TEACHER,
        )
        student = User(
            first_name="Carlos",
            last_name="Mendoza",
            email="student@http.test",
            password_hash=hash_password("Student123!"),
            role=UserRole.STUDENT,
            student_number="HTTP-001",
        )
        db.add_all([teacher, student])
        db.flush()
        course = Course(
            code="HTTP-101",
            name="Curso HTTP",
            period="2026-II",
            teacher_id=teacher.id,
        )
        db.add(course)
        db.flush()
        db.add(Enrollment(course_id=course.id, student_id=student.id))
        db.commit()

    def override_db():
        with Session(engine, expire_on_commit=False) as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client, engine
    app.dependency_overrides.clear()


def login(client: TestClient, email: str, password: str):
    response = client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Hola," in response.text


def test_complete_http_workflow(web_context):
    client, engine = web_context
    login(client, "teacher@http.test", "Teacher123!")
    with Session(engine) as db:
        course_id = db.scalar(select(Course.id))
    due = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M")
    response = client.post(
        "/tareas",
        data={
            "course_id": str(course_id),
            "title": "Tarea integral",
            "description": "Flujo completo",
            "due_at": due,
            "weight": "30",
        },
        files={"resource": ("guia.pdf", b"guia", "application/pdf")},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Tarea integral" in response.text

    client.post("/logout")
    login(client, "student@http.test", "Student123!")
    with Session(engine) as db:
        task_id = db.scalar(select(Task.id))
    response = client.post(
        f"/tareas/{task_id}/entregar",
        data={"comment": "Entrega terminada"},
        files={"attachment": ("solucion.pdf", b"solucion", "application/pdf")},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Entrega registrada" in response.text

    client.post("/logout")
    login(client, "teacher@http.test", "Teacher123!")
    with Session(engine) as db:
        submission_id = db.scalar(select(Submission.id))
    response = client.post(
        f"/entregas/{submission_id}/calificar",
        data={"grade": "96", "feedback": "Excelente trabajo"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "96.0/100" in response.text
    with Session(engine) as db:
        submission = db.get(Submission, submission_id)
        assert submission.status == SubmissionStatus.GRADED
