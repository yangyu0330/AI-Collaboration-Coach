"""Phase 4 sessionization tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.config import settings
from packages.core.services.session_service import SessionService
from packages.db.models import Channel, ConversationSession, Project, RawMessage
from packages.shared.enums import SessionStatus, SessionTriggerType


def _is_placeholder_database_url(url: str) -> bool:
    markers = ["[PROJECT-REF]", "[PASSWORD]", "placeholder/unused", "localhost:5432/postgres"]
    return any(marker in url for marker in markers)


pytestmark = pytest.mark.skipif(
    _is_placeholder_database_url(settings.database_url),
    reason="A real DATABASE_URL is required for sessionization tests.",
)


class FakeRedis:
    def __init__(self):
        self.pushes: list[tuple[str, str]] = []

    async def lpush(self, key: str, value: str) -> int:
        self.pushes.append((key, value))
        return len(self.pushes)


@pytest.fixture
def queued_session_ids(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    queued: list[str] = []

    class _FakeAnalyzeSessionTask:
        @staticmethod
        def delay(session_id: str) -> None:
            queued.append(session_id)

    monkeypatch.setattr(
        "apps.worker.tasks.analysis_tasks.analyze_session_task",
        _FakeAnalyzeSessionTask(),
    )
    return queued


@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def project_and_channel(db_session: AsyncSession) -> tuple[Project, Channel]:
    project = Project(name=f"phase4-project-{uuid4().hex[:8]}")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    channel = Channel(
        project_id=project.id,
        telegram_chat_id=-1000000000000 + int(uuid4().int % 999999),
        channel_name="phase4-room",
        channel_type="telegram",
    )
    db_session.add(channel)
    await db_session.commit()
    await db_session.refresh(channel)

    return project, channel


async def _create_message(
    db_session: AsyncSession,
    *,
    project_id,
    channel_id,
    sent_at: datetime,
    text: str,
) -> RawMessage:
    msg = RawMessage(
        project_id=project_id,
        channel_id=channel_id,
        text=text,
        sent_at=sent_at,
        message_type="text",
    )
    db_session.add(msg)
    await db_session.commit()
    await db_session.refresh(msg)
    return msg


@pytest.mark.asyncio
async def test_assign_reuses_open_session_within_threshold(
    db_session: AsyncSession,
    project_and_channel: tuple[Project, Channel],
) -> None:
    project, channel = project_and_channel
    redis = FakeRedis()
    service = SessionService(db=db_session, redis_client=redis, idle_threshold_minutes=60)

    t0 = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=10)
    msg1 = await _create_message(
        db_session,
        project_id=project.id,
        channel_id=channel.id,
        sent_at=t0,
        text="첫 메시지",
    )
    session1 = await service.assign_to_session(msg1)

    msg2 = await _create_message(
        db_session,
        project_id=project.id,
        channel_id=channel.id,
        sent_at=t0 + timedelta(minutes=20),
        text="두 번째 메시지",
    )
    session2 = await service.assign_to_session(msg2)

    refreshed = await db_session.get(ConversationSession, session1.id)
    assert refreshed is not None
    assert session1.id == session2.id
    assert msg1.session_id == session1.id
    assert msg2.session_id == session1.id
    assert refreshed.message_count == 2
    assert refreshed.session_status == SessionStatus.OPEN.value
    assert redis.pushes == []

    await db_session.delete(project)
    await db_session.commit()


@pytest.mark.asyncio
async def test_assign_closes_old_session_after_idle_gap_and_enqueues(
    db_session: AsyncSession,
    project_and_channel: tuple[Project, Channel],
    queued_session_ids: list[str],
) -> None:
    project, channel = project_and_channel
    redis = FakeRedis()
    service = SessionService(db=db_session, redis_client=redis, idle_threshold_minutes=60)

    t0 = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=3)
    msg1 = await _create_message(
        db_session,
        project_id=project.id,
        channel_id=channel.id,
        sent_at=t0,
        text="오래된 메시지",
    )
    old_session = await service.assign_to_session(msg1)

    msg2 = await _create_message(
        db_session,
        project_id=project.id,
        channel_id=channel.id,
        sent_at=t0 + timedelta(minutes=61),
        text="새 세션 메시지",
    )
    new_session = await service.assign_to_session(msg2)

    closed = await db_session.get(ConversationSession, old_session.id)
    assert closed is not None
    assert closed.session_status == SessionStatus.CLOSED.value
    assert closed.trigger_type == SessionTriggerType.IDLE_TIMEOUT.value
    assert new_session.id != old_session.id
    assert msg2.session_id == new_session.id
    assert queued_session_ids == [str(old_session.id)]
    assert redis.pushes == []

    await db_session.delete(project)
    await db_session.commit()


@pytest.mark.asyncio
async def test_close_idle_sessions_closes_matching_open_sessions(
    db_session: AsyncSession,
    project_and_channel: tuple[Project, Channel],
    queued_session_ids: list[str],
) -> None:
    project, channel = project_and_channel
    redis = FakeRedis()
    service = SessionService(db=db_session, redis_client=redis, idle_threshold_minutes=60)

    old_time = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=2)
    msg = await _create_message(
        db_session,
        project_id=project.id,
        channel_id=channel.id,
        sent_at=old_time,
        text="idle check 메시지",
    )
    session = await service.assign_to_session(msg)

    closed_count = await service.close_idle_sessions(project_id=project.id)
    refreshed = await db_session.get(ConversationSession, session.id)

    assert closed_count == 1
    assert refreshed is not None
    assert refreshed.session_status == SessionStatus.CLOSED.value
    assert refreshed.trigger_type == SessionTriggerType.IDLE_TIMEOUT.value
    assert queued_session_ids == [str(session.id)]
    assert redis.pushes == []

    await db_session.delete(project)
    await db_session.commit()
