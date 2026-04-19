"""Analysis tasks executed by Celery workers."""

from __future__ import annotations

import uuid

import structlog

from apps.worker.celery_app import celery_app

logger = structlog.get_logger()


async def _run_analysis(task_type: str, target_id: uuid.UUID) -> dict:
    """Run one analysis type against one UUID target."""
    from packages.core.services.analysis_service import AnalysisService
    from packages.db.session import get_session_factory

    session_factory = get_session_factory()
    async with session_factory() as db:
        service = AnalysisService(db=db)

        if task_type == "session":
            events = await service.analyze_session(target_id)
        elif task_type == "document":
            events = await service.analyze_document(target_id)
        elif task_type == "priority_message":
            events = await service.analyze_priority_message(target_id)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

        return {
            "target_id": str(target_id),
            "task_type": task_type,
            "events_extracted": len(events),
            "event_ids": [str(event.id) for event in events],
        }


@celery_app.task(
    name="analyze_session",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
async def analyze_session_task(self, session_id: str) -> dict:
    """Analyze one closed session."""
    try:
        result = await _run_analysis("session", uuid.UUID(session_id))
        logger.info("analyze_session_complete", **result)
        return result
    except Exception as exc:
        logger.error("analyze_session_failed", session_id=session_id, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(
    name="analyze_document",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
async def analyze_document_task(self, document_id: str) -> dict:
    """Analyze one uploaded document."""
    try:
        result = await _run_analysis("document", uuid.UUID(document_id))
        logger.info("analyze_document_complete", **result)
        return result
    except Exception as exc:
        logger.error("analyze_document_failed", document_id=document_id, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(
    name="analyze_priority_message",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
async def analyze_priority_message_task(self, message_id: str) -> dict:
    """Analyze one priority-marked message."""
    try:
        result = await _run_analysis("priority_message", uuid.UUID(message_id))
        logger.info("analyze_priority_message_complete", **result)
        return result
    except Exception as exc:
        logger.error("analyze_priority_message_failed", message_id=message_id, error=str(exc))
        raise self.retry(exc=exc)
