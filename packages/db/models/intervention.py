"""Intervention model."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, UUIDMixin, utc_now_naive
from packages.shared.enums import InterventionType


class Intervention(Base, UUIDMixin):
    __tablename__ = "interventions"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    intervention_type: Mapped[str] = mapped_column(
        String(30), default=InterventionType.REVIEW_REQUEST.value, nullable=False
    )
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    target_chat_id: Mapped[int | None] = mapped_column(BigInteger, default=None)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(default=utc_now_naive, nullable=False)
    delivered: Mapped[bool] = mapped_column(default=False, nullable=False)
    related_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("extracted_events.id", ondelete="SET NULL"), default=None
    )

    project = relationship("Project", back_populates="interventions")
    target_user = relationship("User")
    related_event = relationship("ExtractedEvent")

    def __repr__(self) -> str:
        return f"<Intervention(type={self.intervention_type!r}, delivered={self.delivered})>"
