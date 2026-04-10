"""FeedbackState model."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, TimestampMixin, UUIDMixin
from packages.shared.enums import FeedbackReflectionStatus


class FeedbackState(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "feedback_state"
    __table_args__ = (
        UniqueConstraint("project_id", "feedback_key", name="uq_feedback_state_project_feedback_key"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    feedback_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, default=None)
    reflection_status: Mapped[str] = mapped_column(
        String(20), default=FeedbackReflectionStatus.PENDING.value, nullable=False
    )
    action_taken: Mapped[str | None] = mapped_column(Text, default=None)

    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("extracted_events.id", ondelete="SET NULL"), default=None
    )
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("raw_documents.id", ondelete="SET NULL"), default=None
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    approved_at: Mapped[datetime | None] = mapped_column(default=None)
    applied_at: Mapped[datetime | None] = mapped_column(default=None)

    project = relationship("Project", back_populates="feedbacks")
    source_event = relationship("ExtractedEvent")
    source_document = relationship("RawDocument")
    approver = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<FeedbackState(feedback_key={self.feedback_key!r}, "
            f"reflection_status={self.reflection_status!r})>"
        )

