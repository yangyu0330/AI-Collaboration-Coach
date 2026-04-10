"""Session maintenance tasks for Celery Beat."""

from __future__ import annotations

import asyncio

import structlog

from apps.worker.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(name="close_idle_sessions")
def close_idle_sessions_task() -> dict[str, int]:
    """Close open sessions that exceeded idle threshold."""
    return asyncio.run(_close_idle_sessions_async())


async def _close_idle_sessions_async() -> dict[str, int]:
    import redis.asyncio as aioredis

    from apps.api.config import settings
    from packages.core.services.session_service import SessionService
    from packages.db.session import get_session_factory

    session_factory = get_session_factory()
    async with session_factory() as db:
        redis_client = aioredis.from_url(settings.redis_url)
        try:
            service = SessionService(
                db=db,
                redis_client=redis_client,
                idle_threshold_minutes=settings.session_idle_threshold_minutes,
            )
            closed_count = await service.close_idle_sessions()
            logger.info("close_idle_sessions_task_done", closed=closed_count)
            return {"closed": closed_count}
        finally:
            await redis_client.aclose()
