from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import get_db
from app.models import (
    Course,
    Enrollment,
    Notification,
    Submission,
    SubmissionStatus,
    Task,
    User,
    UserRole,
)
from app.security import verify_password


app = FastAPI(
    title="UeesTask",
    description="Sistema web para la gestión académica de tareas.",
    version="0.2.0",
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="lax",
    https_only=False,
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    return db.get(User, user_id) if user_id else None


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    if current_user(request, db):
        return RedirectResponse("/panel", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).where(func.lower(User.email) == email.strip().lower()))
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Correo o contraseña incorrectos."},
            status_code=401,
        )
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse("/panel", status_code=303)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/panel", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/", status_code=303)

    context: dict = {
        "user": user,
        "stats": [],
        "courses": [],
        "tasks": [],
    }
    if user.role == UserRole.ADMIN:
        context["stats"] = [
            ("Usuarios", db.scalar(select(func.count(User.id))) or 0),
            ("Cursos", db.scalar(select(func.count(Course.id))) or 0),
            ("Tareas", db.scalar(select(func.count(Task.id))) or 0),
            ("Entregas", db.scalar(select(func.count(Submission.id))) or 0),
        ]
        context["courses"] = db.scalars(select(Course).order_by(Course.name)).all()
    elif user.role == UserRole.TEACHER:
        context["courses"] = db.scalars(
            select(Course).where(Course.teacher_id == user.id).order_by(Course.name)
        ).all()
        context["tasks"] = db.scalars(
            select(Task).where(Task.teacher_id == user.id).order_by(Task.due_at)
        ).all()
        context["stats"] = [
            ("Mis cursos", len(context["courses"])),
            ("Tareas publicadas", len(context["tasks"])),
            (
                "Entregas recibidas",
                db.scalar(
                    select(func.count(Submission.id))
                    .join(Task)
                    .where(Task.teacher_id == user.id)
                )
                or 0,
            ),
            (
                "Por calificar",
                db.scalar(
                    select(func.count(Submission.id))
                    .join(Task)
                    .where(
                        Task.teacher_id == user.id,
                        Submission.status == SubmissionStatus.SUBMITTED,
                    )
                )
                or 0,
            ),
        ]
    else:
        context["courses"] = db.scalars(
            select(Course)
            .join(Enrollment)
            .where(Enrollment.student_id == user.id)
            .order_by(Course.name)
        ).all()
        context["tasks"] = db.scalars(
            select(Task)
            .join(Course)
            .join(Enrollment)
            .where(Enrollment.student_id == user.id)
            .order_by(Task.due_at)
        ).all()
        context["stats"] = [
            ("Mis cursos", len(context["courses"])),
            ("Tareas disponibles", len(context["tasks"])),
            (
                "Entregas realizadas",
                db.scalar(
                    select(func.count(Submission.id)).where(
                        Submission.student_id == user.id
                    )
                )
                or 0,
            ),
            (
                "Notificaciones",
                db.scalar(
                    select(func.count(Notification.id)).where(
                        Notification.user_id == user.id,
                        Notification.read_at.is_(None),
                    )
                )
                or 0,
            ),
        ]
    return templates.TemplateResponse(request, "dashboard.html", context)


@app.get("/salud")
def health() -> dict[str, str]:
    return {"estado": "ok", "aplicacion": "UeesTask", "version": app.version}
