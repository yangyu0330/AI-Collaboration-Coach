"""ReviewAction model."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, UUIDMixin, utc_now_naive
from packages.shared.enums import ReviewActionType


class ReviewAction(Base, UUIDMixin):
    __tablename__ = "review_actions"

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("extracted_events.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    action: Mapped[str] = mapped_column(
        String(30), default=ReviewActionType.APPROVE.value, nullable=False
    )
    review_note: Mapped[str | None] = mapped_column(Text, default=None)
    patch: Mapped[dict | None] = mapped_column(JSONB, default=None)
    reviewed_at: Mapped[datetime] = mapped_column(
        default=utc_now_naive, nullable=False
    )

    event = relationship("ExtractedEvent", back_populates="review_actions")
    reviewer = relationship("User")

    def __repr__(self) -> str:
        return f"<ReviewAction(id={self.id}, action={self.action!r})>"
