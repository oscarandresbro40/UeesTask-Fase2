"""Datos demostrativos idempotentes del grupo D4 para presentación y pruebas."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models import (
    Course,
    Enrollment,
    Notification,
    Submission,
    SubmissionStatus,
    Task,
    TaskStatus,
    User,
    UserRole,
)
from app.security import hash_password


MEMBERS = (
    ("Alexis Omar", "Analuisa Jaramillo", "alexis.analuisa@example.test", UserRole.TEACHER, "Arquitectura de software", None),
    ("Joseline Nathaly", "Duarte León", "joseline.duarte@example.test", UserRole.STUDENT, None, "D4-2026-001"),
    ("William Adrian", "Cabrera Maldonado", "william.cabrera@example.test", UserRole.STUDENT, None, "D4-2026-002"),
    ("Oscar Andrés", "Bernal Rodríguez", "oscar.bernal@example.test", UserRole.TEACHER, "Calidad de software", None),
    ("Christian Omar", "Yaguana Díaz", "christian.yaguana@example.test", UserRole.STUDENT, None, "D4-2026-003"),
    ("Ronnie Alexie", "Villón Ramírez", "ronnie.villon.demo@example.test", UserRole.STUDENT, None, "D4-2026-004"),
    ("Edmilson Miguel", "Suárez Rizo", "edmilson.suarez@example.test", UserRole.STUDENT, None, "D4-2026-005"),
)


def get_or_create_user(db, item):
    first_name, last_name, email, role, specialty, student_number = item
    user = db.scalar(select(User).where(User.email == email))
    if user:
        return user
    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=hash_password("GrupoD4-2026!"),
        role=role,
        specialty=specialty,
        student_number=student_number,
        program="Ingeniería en Computación" if role == UserRole.STUDENT else None,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def seed_group_d4() -> None:
    upload_dir = Path("uploads/entregas")
    upload_dir.mkdir(parents=True, exist_ok=True)
    with SessionLocal() as db:
        members = [get_or_create_user(db, item) for item in MEMBERS]
        teachers = [member for member in members if member.role == UserRole.TEACHER]
        students = [member for member in members if member.role == UserRole.STUDENT]
        course_specs = (
            ("D4-DSW-2026", "Diseño de Software — Escenario D4", teachers[0]),
            ("D4-CAL-2026", "Calidad y Pruebas — Escenario D4", teachers[1]),
        )
        courses = []
        for code, name, teacher in course_specs:
            course = db.scalar(select(Course).where(Course.code == code))
            if not course:
                course = Course(
                    code=code, name=name, period="2026-II",
                    description="Curso demostrativo para validar UeesTask con el grupo D4.",
                    teacher_id=teacher.id, is_active=True,
                )
                db.add(course)
                db.flush()
            courses.append(course)
        for course in courses:
            for student in students:
                if not db.get(Enrollment, (course.id, student.id)):
                    db.add(Enrollment(course_id=course.id, student_id=student.id))
        db.flush()
        task_specs = (
            (courses[0], teachers[0], "Modelo UML actualizado", 40.0, 10),
            (courses[0], teachers[0], "Informe final de refactorización", 60.0, 17),
            (courses[1], teachers[1], "Plan integral de pruebas", 50.0, 12),
            (courses[1], teachers[1], "Evidencias y métricas", 50.0, 20),
        )
        tasks = []
        for course, teacher, title, weight, days in task_specs:
            task = db.scalar(select(Task).where(Task.course_id == course.id, Task.title == title))
            if not task:
                task = Task(
                    course_id=course.id, teacher_id=teacher.id, title=title,
                    description=f"Actividad demostrativa asignada al grupo D4: {title}.",
                    due_at=datetime.now(timezone.utc) + timedelta(days=days),
                    weight=weight, status=TaskStatus.PUBLISHED,
                )
                db.add(task)
                db.flush()
                for student in students:
                    db.add(Notification(
                        user_id=student.id, event_type="TAREA_CREADA",
                        title="Nueva tarea académica",
                        message=f"Se publicó «{title}» en {course.name}.",
                    ))
            tasks.append(task)
        db.flush()
        grade_values = (94.0, 91.0, 88.0, 97.0, 93.0)
        for index, student in enumerate(students):
            for task_index, task in enumerate(tasks):
                existing = db.scalar(select(Submission).where(
                    Submission.task_id == task.id, Submission.student_id == student.id
                ))
                if existing:
                    continue
                file_path = upload_dir / f"d4_{student.student_number}_{task.id}.txt"
                file_path.write_text(
                    f"Evidencia demostrativa de {student.full_name} para {task.title}.",
                    encoding="utf-8",
                )
                graded = task_index < 3
                grade = max(0.0, grade_values[index] - task_index) if graded else None
                db.add(Submission(
                    task_id=task.id, student_id=student.id,
                    original_name=f"evidencia_{student.student_number}_{task_index + 1}.txt",
                    storage_path=str(file_path),
                    comment=f"Entrega demostrativa de {student.full_name}.",
                    status=SubmissionStatus.GRADED if graded else SubmissionStatus.SUBMITTED,
                    grade=grade,
                    feedback="Cumple los criterios definidos para el escenario de prueba." if graded else "",
                    graded_at=datetime.now(timezone.utc) if graded else None,
                ))
                db.add(Notification(
                    user_id=task.teacher_id, event_type="ENTREGA_REGISTRADA",
                    title="Nueva entrega", message=f"{student.full_name} entregó «{task.title}».",
                ))
                if graded:
                    db.add(Notification(
                        user_id=student.id, event_type="ENTREGA_CALIFICADA",
                        title="Actividad calificada",
                        message=f"Tu entrega de «{task.title}» recibió {grade:g}/100.",
                    ))
        db.commit()
        print("Escenario demostrativo D4 creado o verificado correctamente.")


if __name__ == "__main__":
    seed_group_d4()
