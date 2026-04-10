"""IssueState model."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, TimestampMixin, UUIDMixin
from packages.shared.enums import CanonicalStatus, Priority


class IssueState(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "issues_state"
    __table_args__ = (
        UniqueConstraint("project_id", "issue_key", name="uq_issues_state_project_issue_key"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    issue_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    severity: Mapped[str] = mapped_column(String(10), default=Priority.MEDIUM.value, nullable=False)
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
    resolved_at: Mapped[datetime | None] = mapped_column(default=None)

    project = relationship("Project", back_populates="issues")
    source_event = relationship("ExtractedEvent")
    approver = relationship("User")

    def __repr__(self) -> str:
        return f"<IssueState(issue_key={self.issue_key!r}, status={self.status!r})>"

