"""Worker task namespace."""

from apps.worker.celery_app import celery_app
from apps.worker.tasks.analysis_tasks import (
    analyze_document_task,
    analyze_priority_message_task,
    analyze_session_task,
)
from apps.worker.tasks.session_tasks import close_idle_sessions_task


@celery_app.task(name="health_check_task")
def health_check_task() -> dict[str, str]:
    """Simple task used to validate worker startup."""
    return {"status": "ok", "worker": "celery"}


__all__ = [
    "health_check_task",
    "close_idle_sessions_task",
    "analyze_session_task",
    "analyze_document_task",
    "analyze_priority_message_task",
]
