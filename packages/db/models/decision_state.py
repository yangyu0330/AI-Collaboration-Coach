"""DecisionState model."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, TimestampMixin, UUIDMixin
from packages.shared.enums import CanonicalStatus


class DecisionState(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "decisions_state"
    __table_args__ = (
        UniqueConstraint("project_id", "decision_key", name="uq_decisions_state_project_decision_key"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    decision_key: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(200), default=None)
    decision_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=CanonicalStatus.ACTIVE.value, nullable=False
    )

    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("extracted_events.id", ondelete="SET NULL"), default=None
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    approved_at: Mapped[datetime | None] = mapped_column(default=None)
    applied_at: Mapped[datetime | None] = mapped_column(default=None)
    superseded_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("decisions_state.id", ondelete="SET NULL"), default=None
    )

    project = relationship("Project", back_populates="decisions")
    source_event = relationship("ExtractedEvent")
    approver = relationship("User")

    def __repr__(self) -> str:
        return f"<DecisionState(decision_key={self.decision_key!r}, status={self.status!r})>"

