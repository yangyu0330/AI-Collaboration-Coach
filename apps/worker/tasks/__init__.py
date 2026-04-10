"""Worker task namespace."""

from apps.worker.celery_app import celery_app


@celery_app.task(name="health_check_task")
def health_check_task() -> dict[str, str]:
    """Simple task used to validate worker startup."""
    return {"status": "ok", "worker": "celery"}

