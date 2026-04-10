"""Conversation sessionization service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.db.models.conversation_session import ConversationSession
from packages.db.models.raw_message import RawMessage
from packages.shared.constants import ANALYSIS_QUEUE, PRIORITY_ANALYSIS_QUEUE
from packages.shared.enums import SessionStatus, SessionTriggerType

logger = structlog.get_logger()


class SessionService:
    """Assign incoming messages to rolling conversation sessions."""

    def __init__(
        self,
        db: AsyncSession,
        redis_client=None,
        idle_threshold_minutes: int = 60,
    ):
        self.db = db
        self.redis = redis_client
        self.idle_threshold = timedelta(minutes=idle_threshold_minutes)

    async def assign_to_session(self, message: RawMessage) -> ConversationSession:
        """Assign one persisted raw message into an open session."""
        current_session = await self._get_open_session(message.channel_id)

        if current_session is None:
            return await self._create_session(message)

        last_message_time = await self._get_last_message_time(current_session.id)
        if last_message_time is None:
            await self._add_to_session(current_session, message)
            return current_session

        time_gap = message.sent_at - last_message_time
        if time_gap > self.idle_threshold:
            await self._close_session(
                current_session,
                trigger=SessionTriggerType.IDLE_TIMEOUT,
                end_at=last_message_time,
            )
            return await self._create_session(message)

        await self._add_to_session(current_session, message)
        return current_session

    async def close_idle_sessions(self, project_id: uuid.UUID | None = None) -> int:
        """Close open sessions whose last message crossed the idle threshold."""
        cutoff = self._now_utc_naive() - self.idle_threshold

        stmt = select(ConversationSession).where(
            ConversationSession.session_status == SessionStatus.OPEN.value,
        )
        if project_id is not None:
            stmt = stmt.where(ConversationSession.project_id == project_id)

        result = await self.db.execute(stmt)
        open_sessions = list(result.scalars().all())

        closed_count = 0
        for session in open_sessions:
            last_time = await self._get_last_message_time(session.id)
            if last_time is not None and last_time < cutoff:
                await self._close_session(
                    session,
                    trigger=SessionTriggerType.IDLE_TIMEOUT,
                    end_at=last_time,
                )
                closed_count += 1

        if closed_count:
            logger.info("idle_sessions_closed", count=closed_count)
        return closed_count

    async def _get_open_session(self, channel_id: uuid.UUID) -> ConversationSession | None:
        stmt = (
            select(ConversationSession)
            .where(
                and_(
                    ConversationSession.channel_id == channel_id,
                    ConversationSession.session_status == SessionStatus.OPEN.value,
                )
            )
            .order_by(ConversationSession.start_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_last_message_time(self, session_id: uuid.UUID) -> datetime | None:
        stmt = select(func.max(RawMessage.sent_at)).where(RawMessage.session_id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _create_session(self, message: RawMessage) -> ConversationSession:
        session = ConversationSession(
            project_id=message.project_id,
            channel_id=message.channel_id,
            start_at=message.sent_at,
            message_count=1,
            session_status=SessionStatus.OPEN.value,
        )
        self.db.add(session)
        await self.db.flush()

        message.session_id = session.id
        await self.db.commit()
        await self.db.refresh(session)

        logger.info(
            "session_created",
            session_id=str(session.id),
            channel_id=str(message.channel_id),
        )
        return session

    async def _add_to_session(self, session: ConversationSession, message: RawMessage) -> None:
        message.session_id = session.id
        session.message_count += 1
        await self.db.commit()

    async def _close_session(
        self,
        session: ConversationSession,
        trigger: SessionTriggerType,
        end_at: datetime | None = None,
    ) -> None:
        session.session_status = SessionStatus.CLOSED.value
        session.trigger_type = trigger.value
        session.end_at = end_at or self._now_utc_naive()
        await self.db.commit()

        await self._enqueue_for_analysis(session)
        logger.info(
            "session_closed",
            session_id=str(session.id),
            trigger=trigger.value,
            message_count=session.message_count,
        )

    async def _enqueue_for_analysis(self, session: ConversationSession) -> None:
        if self.redis is None:
            logger.warning("redis_not_available_for_session_enqueue", session_id=str(session.id))
            return

        await self.redis.lpush(ANALYSIS_QUEUE, str(session.id))
        logger.info("session_enqueued", session_id=str(session.id), queue=ANALYSIS_QUEUE)

    @staticmethod
    def _now_utc_naive() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)


async def enqueue_priority(redis_client, message_id: uuid.UUID) -> None:
    """Push a priority message id to the dedicated Redis queue."""
    if redis_client is None:
        return
    await redis_client.lpush(PRIORITY_ANALYSIS_QUEUE, str(message_id))
