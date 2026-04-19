"""Manual analysis task enqueue endpoints."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status

from apps.api.schemas.analysis import AnalysisTaskQueuedResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


def _enqueue(task: Any, task_name: str, target_id: uuid.UUID) -> AnalysisTaskQueuedResponse:
    """Dispatch one Celery task and normalize response payload."""
    try:
        async_result = task.delay(str(target_id))
    except Exception as exc:
        logger.error(
            "analysis_task_enqueue_failed",
            task_name=task_name,
            target_id=str(target_id),
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to enqueue analysis task.",
        ) from exc

    logger.info(
        "analysis_task_queued",
        task_name=task_name,
        target_id=str(target_id),
        task_id=getattr(async_result, "id", None),
    )
    return AnalysisTaskQueuedResponse(
        ok=True,
        task_name=task_name,
        task_id=getattr(async_result, "id", None),
        target_id=target_id,
    )


@router.post(
    "/sessions/{session_id}",
    response_model=AnalysisTaskQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def enqueue_session_analysis(session_id: uuid.UUID) -> AnalysisTaskQueuedResponse:
    """Enqueue analysis for one conversation session."""
    from apps.worker.tasks.analysis_tasks import analyze_session_task

    return _enqueue(analyze_session_task, "analyze_session", session_id)


@router.post(
    "/documents/{document_id}",
    response_model=AnalysisTaskQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def enqueue_document_analysis(document_id: uuid.UUID) -> AnalysisTaskQueuedResponse:
    """Enqueue analysis for one uploaded document."""
    from apps.worker.tasks.analysis_tasks import analyze_document_task

    return _enqueue(analyze_document_task, "analyze_document", document_id)


@router.post(
    "/priority-messages/{message_id}",
    response_model=AnalysisTaskQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def enqueue_priority_message_analysis(message_id: uuid.UUID) -> AnalysisTaskQueuedResponse:
    """Enqueue analysis for one priority-marked message."""
    from apps.worker.tasks.analysis_tasks import analyze_priority_message_task

    return _enqueue(analyze_priority_message_task, "analyze_priority_message", message_id)
