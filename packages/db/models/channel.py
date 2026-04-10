"""Channel model."""

import uuid

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, TimestampMixin, UUIDMixin


class Channel(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "channels"
    __table_args__ = (
        UniqueConstraint("project_id", "telegram_chat_id", name="uq_channels_project_telegram_chat"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, default=None)
    channel_name: Mapped[str] = mapped_column(String(200), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(20), default="telegram", nullable=False)

    project = relationship("Project", back_populates="channels")
    raw_messages = relationship("RawMessage", back_populates="channel", lazy="selectin")
    conversation_sessions = relationship(
        "ConversationSession", back_populates="channel", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Channel(id={self.id}, name={self.channel_name!r})>"

