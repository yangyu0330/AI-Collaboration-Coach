"""Telegram webhook endpoints."""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import settings
from apps.api.dependencies import get_db
from apps.api.schemas.telegram import TelegramUpdate
from packages.core.services import MessageService
from packages.db.models.project import Project

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/telegram", tags=["telegram"])

DEFAULT_PROJECT_ID: uuid.UUID | None = None


async def _get_or_create_default_project(db: AsyncSession) -> uuid.UUID:
    """Use the first project, or create one for single-project ingestion."""
    global DEFAULT_PROJECT_ID
    if DEFAULT_PROJECT_ID is not None:
        return DEFAULT_PROJECT_ID

    result = await db.execute(select(Project).limit(1))
    project = result.scalar_one_or_none()

    if project is None:
        project = Project(name="기본 프로젝트", description="텔레그램 웹훅 수집용 기본 프로젝트")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        logger.info("default_project_created", project_id=str(project.id))

    DEFAULT_PROJECT_ID = project.id
    return DEFAULT_PROJECT_ID


def _verify_secret_token(
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> None:
    """Validate Telegram webhook secret token when configured."""
    if not settings.telegram_secret_token:
        return

    if x_telegram_bot_api_secret_token != settings.telegram_secret_token:
        logger.warning("webhook_secret_token_mismatch")
        raise HTTPException(status_code=403, detail="Invalid secret token")


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_verify_secret_token),
) -> dict[str, bool | str | None]:
    """
    Receive Telegram webhook updates.

    Always returns HTTP 200 to avoid repeated Telegram retries.
    """
    try:
        body = await request.json()
        update = TelegramUpdate.model_validate(body)
    except Exception as exc:
        logger.warning("webhook_parse_error", error=str(exc))
        return {"ok": False, "error": "Parse error"}

    project_id = await _get_or_create_default_project(db)
    service = MessageService(db=db, project_id=project_id)

    try:
        result = await service.process_update(update)
        return {
            "ok": True,
            "message_id": str(result.id) if result else None,
        }
    except Exception as exc:
        await db.rollback()
        logger.error("webhook_process_error", error=str(exc), update_id=update.update_id)
        return {"ok": False, "error": "Processing error"}

