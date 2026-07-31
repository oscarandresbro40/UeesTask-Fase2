from pathlib import Path

from fastapi import Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import web as web_module
from app.database import get_db
from app.models import (
    Course,
    Enrollment,
    Notification,
    Submission,
    SubmissionStatus,
    Task,
    TaskResource,
    User,
    UserRole,
)
from app.services import (
    DomainError,
    create_course,
    create_task,
    create_user,
    enroll_student,
    grade_submission,
    submit_task,
)
from app.uees import app


templates = Jinja2Templates(directory="app/templates_full")
templates.env.loader = ChoiceLoader(
    [
        FileSystemLoader("app/templates_full"),
        FileSystemLoader("app/templates_uees"),
        FileSystemLoader("app/templates"),
    ]
)
web_module.templates = templates


def authenticated_user(request: Request, db: Session) -> User:
    user = web_module.current_user(request, db)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Debes iniciar sesión.")
    return user


def require_role(user: User, *roles: UserRole) -> None:
    if user.role not in roles:
        raise HTTPException(status_code=403, detail="No tienes permiso para esta acción.")


def set_flash(request: Request, message: str, kind: str = "success") -> None:
    request.session["flash"] = {"message": message, "kind": kind}


def page_context(request: Request, user: User, **extra) -> dict:
    return {
        "user": user,
        "flash": request.session.pop("flash", None),
        **extra,
    }


@app.get("/usuarios", name="users_page")
def users_page(request: Request, db: Session = Depends(get_db)):
    user = authenticated_user(request, db)
    require_role(user, UserRole.ADMIN)
    users = db.scalars(select(User).order_by(User.role, User.last_name)).all()
    return templates.TemplateResponse(
        request, "users.html", page_context(request, user, users=users)
    )


@app.post("/usuarios")
def users_create(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    specialty: str = Form(""),
    student_number: str = Form(""),
    program: str = Form(""),
    db: Session = Depends(get_db),
):
    user = authenticated_user(request, db)
    require_role(user, UserRole.ADMIN)
    try:
        created = create_user(
            db,
            first_name,
            last_name,
            email,
            password,
            UserRole(role),
            specialty,
            student_number,
            program,
        )
        set_flash(request, f"Usuario {created.full_name} creado correctamente.")
    except (DomainError, ValueError) as exc:
        db.rollback()
        set_flash(request, str(exc), "error")
    return RedirectResponse("/usuarios", status_code=303)


@app.get("/cursos", name="courses_page")
def courses_page(request: Request, db: Session = Depends(get_db)):
    user = authenticated_user(request, db)
    query = select(Course).options(
        selectinload(Course.teacher),
        selectinload(Course.enrollments).selectinload(Enrollment.student),
    )
    if user.role == UserRole.TEACHER:
        query = query.where(Course.teacher_id == user.id)
    elif user.role == UserRole.STUDENT:
        query = query.join(Enrollment).where(Enrollment.student_id == user.id)
    courses = db.scalars(query.order_by(Course.name)).unique().all()
    teachers = db.scalars(
        select(User).where(User.role == UserRole.TEACHER).order_by(User.last_name)
    ).all()
    students = db.scalars(
        select(User).where(User.role == UserRole.STUDENT).order_by(User.last_name)
    ).all()
    return templates.TemplateResponse(
        request,
        "courses.html",
        page_context(
            request,
            user,
            courses=courses,
            teachers=teachers,
            students=students,
        ),
    )


@app.post("/cursos")
def courses_create(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    period: str = Form(...),
    description: str = Form(""),
    teacher_id: int = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticated_user(request, db)
    require_role(user, UserRole.ADMIN)
    try:
        course = create_course(db, code, name, period, description, teacher_id)
        set_flash(request, f"Curso {course.name} creado correctamente.")
    except DomainError as exc:
        db.rollback()
        set_flash(request, str(exc), "error")
    return RedirectResponse("/cursos", status_code=303)


@app.post("/cursos/{course_id}/matriculas")
def courses_enroll(
    course_id: int,
    request: Request,
    student_id: int = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticated_user(request, db)
    require_role(user, UserRole.ADMIN)
    try:
        enrollment = enroll_student(db, course_id, student_id)
        set_flash(
            request,
            f"{enrollment.student.full_name} fue matriculado correctamente.",
        )
    except DomainError as exc:
        db.rollback()
        set_flash(request, str(exc), "error")
    return RedirectResponse("/cursos", status_code=303)


@app.get("/tareas", name="tasks_page")
def tasks_page(request: Request, db: Session = Depends(get_db)):
    user = authenticated_user(request, db)
    query = select(Task).options(
        selectinload(Task.course),
        selectinload(Task.resources),
        selectinload(Task.submissions),
    )
    if user.role == UserRole.TEACHER:
        query = query.where(Task.teacher_id == user.id)
        courses = db.scalars(
            select(Course).where(Course.teacher_id == user.id).order_by(Course.name)
        ).all()
    elif user.role == UserRole.STUDENT:
        query = query.join(Course).join(Enrollment).where(
            Enrollment.student_id == user.id
        )
        courses = []
    else:
        courses = []
    tasks = db.scalars(query.order_by(Task.due_at.desc())).unique().all()
    submitted_task_ids = set(
        db.scalars(
            select(Submission.task_id).where(Submission.student_id == user.id)
        ).all()
    ) if user.role == UserRole.STUDENT else set()
    return templates.TemplateResponse(
        request,
        "tasks.html",
        page_context(
            request,
            user,
            tasks=tasks,
            courses=courses,
            submitted_task_ids=submitted_task_ids,
        ),
    )


@app.post("/tareas")
def tasks_create(
    request: Request,
    course_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    due_at: str = Form(...),
    weight: float = Form(...),
    resource: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    user = authenticated_user(request, db)
    require_role(user, UserRole.TEACHER)
    try:
        task = create_task(
            db, user, course_id, title, description, due_at, weight, resource
        )
        set_flash(request, f"Tarea «{task.title}» publicada correctamente.")
    except DomainError as exc:
        db.rollback()
        set_flash(request, str(exc), "error")
    return RedirectResponse("/tareas", status_code=303)


@app.post("/tareas/{task_id}/entregar")
def tasks_submit(
    task_id: int,
    request: Request,
    comment: str = Form(""),
    attachment: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = authenticated_user(request, db)
    require_role(user, UserRole.STUDENT)
    try:
        submission = submit_task(db, user, task_id, comment, attachment)
        set_flash(
            request,
            f"Entrega «{submission.original_name}» registrada correctamente.",
        )
    except DomainError as exc:
        db.rollback()
        set_flash(request, str(exc), "error")
    return RedirectResponse("/tareas", status_code=303)


@app.get("/entregas", name="submissions_page")
def submissions_page(request: Request, db: Session = Depends(get_db)):
    user = authenticated_user(request, db)
    query = select(Submission).options(
        selectinload(Submission.task).selectinload(Task.course),
        selectinload(Submission.student),
    )
    if user.role == UserRole.TEACHER:
        query = query.join(Task).where(Task.teacher_id == user.id)
    elif user.role == UserRole.STUDENT:
        query = query.where(Submission.student_id == user.id)
    submissions = db.scalars(
        query.order_by(Submission.submitted_at.desc())
    ).unique().all()
    return templates.TemplateResponse(
        request,
        "submissions.html",
        page_context(request, user, submissions=submissions),
    )


@app.post("/entregas/{submission_id}/calificar")
def submissions_grade(
    submission_id: int,
    request: Request,
    grade: float = Form(...),
    feedback: str = Form(""),
    db: Session = Depends(get_db),
):
    user = authenticated_user(request, db)
    require_role(user, UserRole.TEACHER)
    try:
        submission = grade_submission(db, user, submission_id, grade, feedback)
        set_flash(
            request,
            f"Entrega de {submission.student.full_name} calificada correctamente.",
        )
    except DomainError as exc:
        db.rollback()
        set_flash(request, str(exc), "error")
    return RedirectResponse("/entregas", status_code=303)


@app.get("/entregas/{submission_id}/archivo")
def submissions_download(
    submission_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = authenticated_user(request, db)
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    allowed = (
        user.role == UserRole.ADMIN
        or submission.student_id == user.id
        or submission.task.teacher_id == user.id
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="No tienes acceso al archivo.")
    path = Path(submission.storage_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    return FileResponse(path, filename=submission.original_name)


@app.get("/recursos/{resource_id}/archivo")
def resources_download(
    resource_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = authenticated_user(request, db)
    resource = db.get(TaskResource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Recurso no encontrado.")
    task = resource.task
    enrolled = db.get(Enrollment, (task.course_id, user.id)) is not None
    if user.role != UserRole.ADMIN and task.teacher_id != user.id and not enrolled:
        raise HTTPException(status_code=403, detail="No tienes acceso al recurso.")
    path = Path(resource.storage_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Recurso no encontrado.")
    return FileResponse(path, filename=resource.original_name)


@app.get("/notificaciones", name="notifications_page")
def notifications_page(request: Request, db: Session = Depends(get_db)):
    user = authenticated_user(request, db)
    notifications = db.scalars(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
    ).all()
    return templates.TemplateResponse(
        request,
        "notifications.html",
        page_context(request, user, notifications=notifications),
    )


@app.post("/notificaciones/leer")
def notifications_read(request: Request, db: Session = Depends(get_db)):
    from datetime import datetime, timezone

    user = authenticated_user(request, db)
    notifications = db.scalars(
        select(Notification).where(
            Notification.user_id == user.id,
            Notification.read_at.is_(None),
        )
    ).all()
    now = datetime.now(timezone.utc)
    for notification in notifications:
        notification.read_at = now
    db.commit()
    set_flash(request, "Notificaciones marcadas como leídas.")
    return RedirectResponse("/notificaciones", status_code=303)
