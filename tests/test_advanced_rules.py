from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.final import validate_academic_rules
from app.models import Course, Task, TaskStatus, User, UserRole
from app.security import hash_password
from app.services import DomainError


def test_course_task_weights_cannot_exceed_one_hundred():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        teacher = User(
            first_name="Docente",
            last_name="Prueba",
            email="weight@test.edu",
            password_hash=hash_password("Password123!"),
            role=UserRole.TEACHER,
        )
        db.add(teacher)
        db.flush()
        course = Course(
            code="WEIGHT-1",
            name="Ponderaciones",
            period="2026-II",
            teacher_id=teacher.id,
        )
        db.add(course)
        db.flush()
        db.add(
            Task(
                course_id=course.id,
                teacher_id=teacher.id,
                title="Primera",
                description="Prueba",
                due_at=datetime.now(timezone.utc) + timedelta(days=2),
                weight=70,
                status=TaskStatus.PUBLISHED,
            )
        )
        db.commit()
        db.add(
            Task(
                course_id=course.id,
                teacher_id=teacher.id,
                title="Segunda",
                description="Prueba",
                due_at=datetime.now(timezone.utc) + timedelta(days=3),
                weight=40,
                status=TaskStatus.PUBLISHED,
            )
        )
        with pytest.raises(DomainError, match="100"):
            db.commit()
