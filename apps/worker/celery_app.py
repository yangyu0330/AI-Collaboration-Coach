"""Celery app configuration."""

from celery import Celery

from apps.api.config import settings

celery_app = Celery(
    "ai_collab_coach",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "close_idle_sessions": {"queue": "session"},
        "apps.worker.tasks.session_tasks.*": {"queue": "session"},
        "apps.worker.tasks.analysis_tasks.*": {"queue": "analysis"},
        "apps.worker.tasks.notification_tasks.*": {"queue": "notification"},
    },
    beat_schedule={
        "close-idle-sessions-every-minute": {
            "task": "close_idle_sessions",
            "schedule": 60.0,
        },
    },
)

celery_app.autodiscover_tasks(["apps.worker.tasks"])
