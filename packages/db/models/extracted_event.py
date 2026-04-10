"""ExtractedEvent model."""

import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, TimestampMixin, UUIDMixin
from packages.shared.enums import EventState


class ExtractedEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "extracted_events"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    source_kind: Mapped[str] = mapped_column(String(20), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(nullable=False)

    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    state: Mapped[str] = mapped_column(String(20), default=EventState.EXTRACTED.value, nullable=False)
    topic: Mapped[str | None] = mapped_column(String(200), default=None)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, default=None)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fact_type: Mapped[str | None] = mapped_column(String(40), default=None)

    project = relationship("Project", back_populates="extracted_events")
    review_actions = relationship("ReviewAction", back_populates="event", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<ExtractedEvent(id={self.id}, type={self.event_type!r}, "
            f"state={self.state!r}, conf={self.confidence})>"
        )

