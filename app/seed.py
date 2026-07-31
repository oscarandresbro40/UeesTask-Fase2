from sqlalchemy import select

from app.database import SessionLocal
from app.models import Course, Enrollment, User, UserRole
from app.security import hash_password


DEMO_USERS = (
    {
        "first_name": "Andrea",
        "last_name": "Administrador",
        "email": "admin@uees.edu.ec",
        "password": "Admin123!",
        "role": UserRole.ADMIN,
    },
    {
        "first_name": "María",
        "last_name": "López",
        "email": "docente@uees.edu.ec",
        "password": "Docente123!",
        "role": UserRole.TEACHER,
        "specialty": "Desarrollo de Software",
    },
    {
        "first_name": "Carlos",
        "last_name": "Mendoza",
        "email": "estudiante@uees.edu.ec",
        "password": "Estudiante123!",
        "role": UserRole.STUDENT,
        "student_number": "UEES-2026-001",
        "program": "Ingeniería en Computación",
    },
)


def seed_database() -> None:
    with SessionLocal() as db:
        if db.scalar(select(User.id).limit(1)):
            print("La base ya contiene usuarios; no se insertaron duplicados.")
            return
        users = []
        for item in DEMO_USERS:
            data = dict(item)
            password = data.pop("password")
            users.append(User(**data, password_hash=hash_password(password)))
        db.add_all(users)
        db.flush()
        teacher = next(user for user in users if user.role == UserRole.TEACHER)
        student = next(user for user in users if user.role == UserRole.STUDENT)
        course = Course(
            code="DSW-2026-II",
            name="Desarrollo de Software",
            period="2026-II",
            description="Curso demostrativo para los casos de uso de UeesTask.",
            teacher_id=teacher.id,
        )
        db.add(course)
        db.flush()
        db.add(Enrollment(course_id=course.id, student_id=student.id))
        db.commit()
        print("Datos de demostración creados correctamente.")


if __name__ == "__main__":
    seed_database()
