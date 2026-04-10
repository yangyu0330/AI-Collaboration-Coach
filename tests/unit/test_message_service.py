"""Phase 2 message ingestion tests."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.config import settings
from apps.api.schemas.telegram import TelegramUpdate
from packages.core.services.message_service import MessageService
from packages.db.models import Channel, Project, RawMessage, User


def _is_placeholder_database_url(url: str) -> bool:
    markers = ["[PROJECT-REF]", "[PASSWORD]", "placeholder/unused", "localhost:5432/postgres"]
    return any(marker in url for marker in markers)


pytestmark = pytest.mark.skipif(
    _is_placeholder_database_url(settings.database_url),
    reason="A real DATABASE_URL is required for message ingestion tests.",
)


@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


def _message_update_payload(*, text: str, message_id: int, date: int) -> dict:
    return {
        "update_id": 900000 + message_id,
        "message": {
            "message_id": message_id,
            "from": {
                "id": 111222333,
                "is_bot": False,
                "first_name": "Tester",
                "username": "phase2_tester",
            },
            "chat": {
                "id": -1001234567890,
                "type": "supergroup",
                "title": "phase2-room",
            },
            "date": date,
            "text": text,
        },
    }


@pytest.mark.asyncio
async def test_process_new_message_creates_user_channel_and_message(
    db_session: AsyncSession,
) -> None:
    project = Project(name=f"phase2-project-{uuid4().hex[:8]}")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    service = MessageService(db=db_session, project_id=project.id)
    update = TelegramUpdate.model_validate(
        _message_update_payload(text="hello from phase2", message_id=1, date=1712700000)
    )

    saved = await service.process_update(update)
    assert saved is not None
    assert saved.telegram_message_id == 1
    assert saved.text == "hello from phase2"
    assert saved.edited_at is None

    user_stmt = select(User).where(
        User.project_id == project.id,
        User.telegram_id == 111222333,
    )
    channel_stmt = select(Channel).where(
        Channel.project_id == project.id,
        Channel.telegram_chat_id == -1001234567890,
    )
    user = (await db_session.execute(user_stmt)).scalar_one_or_none()
    channel = (await db_session.execute(channel_stmt)).scalar_one_or_none()

    assert user is not None
    assert user.username == "phase2_tester"
    assert channel is not None
    assert channel.channel_name == "phase2-room"

    await db_session.delete(project)
    await db_session.commit()


@pytest.mark.asyncio
async def test_process_edited_message_updates_existing_row(db_session: AsyncSession) -> None:
    project = Project(name=f"phase2-edit-project-{uuid4().hex[:8]}")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    service = MessageService(db=db_session, project_id=project.id)
    original = TelegramUpdate.model_validate(
        _message_update_payload(text="before edit", message_id=77, date=1712700000)
    )
    saved = await service.process_update(original)
    assert saved is not None

    edited_payload = _message_update_payload(text="after edit", message_id=77, date=1712700060)
    edited_payload["edited_message"] = edited_payload.pop("message")
    edited = await service.process_update(TelegramUpdate.model_validate(edited_payload))

    assert edited is not None
    assert edited.id == saved.id
    assert edited.text == "after edit"
    assert edited.edited_at is not None

    count_stmt = select(func.count(RawMessage.id)).where(RawMessage.project_id == project.id)
    count = (await db_session.execute(count_stmt)).scalar_one()
    assert count == 1

    await db_session.delete(project)
    await db_session.commit()
