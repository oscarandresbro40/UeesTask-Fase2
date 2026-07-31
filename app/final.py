from sqlalchemy import func, select
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.advanced import app
from app.models import Submission, Task, TaskStatus
from app.services import DomainError


def validate_academic_rules(session: Session, *_args) -> None:
    changed_tasks = [
        item for item in session.new.union(session.dirty) if isinstance(item, Task)
    ]
    for task in changed_tasks:
        existing_weight = session.scalar(
            select(func.coalesce(func.sum(Task.weight), 0)).where(
                Task.course_id == task.course_id,
                Task.id != (task.id or 0),
            )
        )
        if float(existing_weight or 0) + float(task.weight) > 100:
            raise DomainError(
                "La suma de ponderaciones del curso no puede superar 100%."
            )

    for submission in session.new:
        if isinstance(submission, Submission):
            task = submission.task or session.get(Task, submission.task_id)
            if task and task.status != TaskStatus.PUBLISHED:
                raise DomainError("La tarea está cerrada y no admite entregas.")


if not getattr(Session, "_ueestask_academic_rules", False):
    event.listen(Session, "before_flush", validate_academic_rules)
    Session._ueestask_academic_rules = True
