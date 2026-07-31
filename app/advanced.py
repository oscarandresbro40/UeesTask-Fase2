from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import full as full_module
from app import web as web_module
from app.database import get_db
from app.full import (
    app,
    authenticated_user,
    page_context,
    require_role,
    set_flash,
)
from app.models import (
    Course,
    Enrollment,
    Submission,
    Task,
    TaskStatus,
    User,
    UserRole,
)
from app.services import DomainError, parse_local_datetime


templates = Jinja2Templates(directory="app/templates_advanced")
templates.env.loader = ChoiceLoader(
    [
        FileSystemLoader("app/templates_advanced"),
        FileSystemLoader("app/templates_full"),
        FileSystemLoader("app/templates_uees"),
        FileSystemLoader("app/templates"),
    ]
)
web_module.templates = templates
full_module.templates = templates


def manageable_courses(db: Session, user: User) -> list[Course]:
    query = select(Course).options(
        selectinload(Course.teacher),
        selectinload(Course.enrollments).selectinload(Enrollment.student),
        selectinload(Course.tasks).selectinload(Task.submissions),
    )
    if user.role == UserRole.TEACHER:
        query = query.where(Course.teacher_id == user.id)
    return db.scalars(query.order_by(Course.name)).unique().all()


@app.get("/gestion", name="management_page")
def management_page(request: Request, db: Session = Depends(get_db)):
    user = authenticated_user(request, db)
    require_role(user, UserRole.ADMIN, UserRole.TEACHER)
    users = (
        db.scalars(select(User).order_by(User.role, User.last_name)).all()
        if user.role == UserRole.ADMIN
        else []
    )
    return templates.TemplateResponse(
        request,
        "management.html",
        page_context(
            request,
            user,
            users=users,
            courses=manageable_courses(db, user),
        ),
    )


@app.post("/usuarios/{user_id}/editar")
def user_update(
    user_id: int,
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    specialty: str = Form(""),
    student_number: str = Form(""),
    program: str = Form(""),
    db: Session = Depends(get_db),
):
    actor = authenticated_user(request, db)
    require_role(actor, UserRole.ADMIN)
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    email = email.strip().lower()
    duplicate = db.scalar(
        select(User.id).where(User.email == email, User.id != target.id)
    )
    if duplicate:
        set_flash(request, "El correo ya pertenece a otro usuario.", "error")
        return RedirectResponse("/gestion", status_code=303)
    if not first_name.strip() or not last_name.strip() or "@" not in email:
        set_flash(request, "Nombre, apellido y correo válido son obligatorios.", "error")
        return RedirectResponse("/gestion", status_code=303)
    target.first_name = first_name.strip()
    target.last_name = last_name.strip()
    target.email = email
    target.specialty = specialty.strip() or None
    target.student_number = student_number.strip() or None
    target.program = program.strip() or None
    try:
        db.commit()
        set_flash(request, f"Datos de {target.full_name} actualizados.")
    except Exception:
        db.rollback()
        set_flash(request, "No fue posible actualizar: verifica correo y matrícula.", "error")
    return RedirectResponse("/gestion", status_code=303)


@app.post("/usuarios/{user_id}/estado")
def user_toggle(user_id: int, request: Request, db: Session = Depends(get_db)):
    actor = authenticated_user(request, db)
    require_role(actor, UserRole.ADMIN)
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if target.id == actor.id:
        set_flash(request, "No puedes desactivar tu propia cuenta.", "error")
    else:
        target.is_active = not target.is_active
        db.commit()
        state = "activado" if target.is_active else "desactivado"
        set_flash(request, f"Usuario {state} correctamente.")
    return RedirectResponse("/gestion", status_code=303)


@app.post("/cursos/{course_id}/estado")
def course_toggle(course_id: int, request: Request, db: Session = Depends(get_db)):
    actor = authenticated_user(request, db)
    require_role(actor, UserRole.ADMIN)
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado.")
    course.is_active = not course.is_active
    db.commit()
    state = "activado" if course.is_active else "cerrado"
    set_flash(request, f"Curso {state} correctamente.")
    return RedirectResponse("/gestion", status_code=303)


@app.post("/cursos/{course_id}/matriculas/{student_id}/retirar")
def enrollment_remove(
    course_id: int,
    student_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    actor = authenticated_user(request, db)
    require_role(actor, UserRole.ADMIN)
    enrollment = db.get(Enrollment, (course_id, student_id))
    if not enrollment:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada.")
    has_submissions = db.scalar(
        select(Submission.id)
        .join(Task)
        .where(Task.course_id == course_id, Submission.student_id == student_id)
        .limit(1)
    )
    if has_submissions:
        set_flash(
            request,
            "No se puede retirar: el estudiante ya tiene entregas en el curso.",
            "error",
        )
    else:
        db.delete(enrollment)
        db.commit()
        set_flash(request, "Matrícula retirada correctamente.")
    return RedirectResponse("/gestion", status_code=303)


@app.post("/tareas/{task_id}/editar")
def task_update(
    task_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    due_at: str = Form(...),
    weight: float = Form(...),
    db: Session = Depends(get_db),
):
    actor = authenticated_user(request, db)
    require_role(actor, UserRole.TEACHER)
    task = db.get(Task, task_id)
    if not task or task.teacher_id != actor.id:
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")
    try:
        if not title.strip() or not description.strip():
            raise DomainError("Título y descripción son obligatorios.")
        if not 1 <= weight <= 100:
            raise DomainError("La ponderación debe estar entre 1 y 100.")
        parsed_due = parse_local_datetime(due_at)
        if parsed_due <= datetime.now(timezone.utc):
            raise DomainError("La fecha de entrega debe ser futura.")
        task.title = title.strip()
        task.description = description.strip()
        task.due_at = parsed_due
        task.weight = weight
        db.commit()
        set_flash(request, "Tarea actualizada correctamente.")
    except DomainError as exc:
        db.rollback()
        set_flash(request, str(exc), "error")
    return RedirectResponse("/gestion", status_code=303)


@app.post("/tareas/{task_id}/estado")
def task_toggle(task_id: int, request: Request, db: Session = Depends(get_db)):
    actor = authenticated_user(request, db)
    require_role(actor, UserRole.TEACHER)
    task = db.get(Task, task_id)
    if not task or task.teacher_id != actor.id:
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")
    task.status = (
        TaskStatus.PUBLISHED
        if task.status == TaskStatus.CLOSED
        else TaskStatus.CLOSED
    )
    db.commit()
    state = "reabierta" if task.status == TaskStatus.PUBLISHED else "cerrada"
    set_flash(request, f"Tarea {state} correctamente.")
    return RedirectResponse("/gestion", status_code=303)


def gradebook_for_course(db: Session, course: Course) -> tuple[list[Task], list[dict]]:
    tasks = db.scalars(
        select(Task).where(Task.course_id == course.id).order_by(Task.due_at)
    ).all()
    students = db.scalars(
        select(User)
        .join(Enrollment)
        .where(Enrollment.course_id == course.id)
        .order_by(User.last_name)
    ).all()
    submissions = db.scalars(
        select(Submission)
        .join(Task)
        .where(Task.course_id == course.id)
    ).all()
    by_key = {(item.student_id, item.task_id): item for item in submissions}
    rows = []
    for student in students:
        grades = []
        weighted_total = 0.0
        graded_weight = 0.0
        for task in tasks:
            submission = by_key.get((student.id, task.id))
            grade = submission.grade if submission else None
            grades.append(grade)
            if grade is not None:
                weighted_total += grade * task.weight
                graded_weight += task.weight
        average = weighted_total / graded_weight if graded_weight else None
        rows.append({"student": student, "grades": grades, "average": average})
    return tasks, rows


@app.get("/calificaciones", name="gradebook_page")
def gradebook_page(
    request: Request,
    course_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    user = authenticated_user(request, db)
    if user.role == UserRole.STUDENT:
        submissions = db.scalars(
            select(Submission)
            .options(selectinload(Submission.task).selectinload(Task.course))
            .where(Submission.student_id == user.id)
            .order_by(Submission.submitted_at.desc())
        ).all()
        graded = [item.grade for item in submissions if item.grade is not None]
        average = sum(graded) / len(graded) if graded else None
        return templates.TemplateResponse(
            request,
            "student_grades.html",
            page_context(
                request,
                user,
                submissions=submissions,
                average=average,
            ),
        )

    courses = manageable_courses(db, user)
    selected = next((item for item in courses if item.id == course_id), None)
    if not selected and courses:
        selected = courses[0]
    tasks, rows = gradebook_for_course(db, selected) if selected else ([], [])
    return templates.TemplateResponse(
        request,
        "gradebook.html",
        page_context(
            request,
            user,
            courses=courses,
            selected=selected,
            tasks=tasks,
            rows=rows,
        ),
    )
