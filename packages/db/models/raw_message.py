"""RawMessage model."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, TimestampMixin, UUIDMixin
from packages.shared.enums import VisibilityStatus


class RawMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "raw_messages"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )
    sender_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        default=None,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversation_sessions.id", ondelete="SET NULL"),
        default=None,
    )

    telegram_message_id: Mapped[int | None] = mapped_column(BigInteger, default=None)
    text: Mapped[str | None] = mapped_column(Text, default=None)
    message_type: Mapped[str] = mapped_column(String(20), default="text", nullable=False)

    reply_to_message_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("raw_messages.id", ondelete="SET NULL"),
        default=None,
    )

    sent_at: Mapped[datetime] = mapped_column(nullable=False)
    edited_at: Mapped[datetime | None] = mapped_column(default=None)

    visibility_status: Mapped[str] = mapped_column(
        String(20),
        default=VisibilityStatus.VISIBLE.value,
        nullable=False,
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, default=None)
    is_priority: Mapped[bool] = mapped_column(default=False, nullable=False)

    project = relationship("Project", back_populates="raw_messages")
    channel = relationship("Channel", back_populates="raw_messages")
    sender = relationship("User")
    session = relationship("ConversationSession", back_populates="messages")
    reply_to = relationship("RawMessage", remote_side="RawMessage.id")

    def __repr__(self) -> str:
        preview = (self.text or "")[:30]
        return f"<RawMessage(id={self.id}, preview={preview!r})>"

