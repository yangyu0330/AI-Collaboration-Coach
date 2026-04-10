"""ConversationSession model."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, TimestampMixin, UUIDMixin
from packages.shared.enums import SessionStatus


class ConversationSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "conversation_sessions"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )

    start_at: Mapped[datetime] = mapped_column(nullable=False)
    end_at: Mapped[datetime | None] = mapped_column(default=None)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    session_status: Mapped[str] = mapped_column(
        String(20), default=SessionStatus.OPEN.value, nullable=False
    )
    trigger_type: Mapped[str | None] = mapped_column(String(20), default=None)

    project = relationship("Project", back_populates="conversation_sessions")
    channel = relationship("Channel", back_populates="conversation_sessions")
    messages = relationship("RawMessage", back_populates="session", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ConversationSession(id={self.id}, status={self.session_status!r})>"

