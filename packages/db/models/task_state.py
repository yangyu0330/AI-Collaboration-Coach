"""TaskState model."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, TimestampMixin, UUIDMixin
from packages.shared.enums import CanonicalStatus, Priority


class TaskState(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tasks_state"
    __table_args__ = (
        UniqueConstraint("project_id", "task_key", name="uq_tasks_state_project_task_key"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    task_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    priority: Mapped[str] = mapped_column(String(10), default=Priority.MEDIUM.value, nullable=False)
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

    project = relationship("Project", back_populates="tasks")
    source_event = relationship("ExtractedEvent")
    assignee = relationship("User", foreign_keys=[assignee_id])
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self) -> str:
        return f"<TaskState(task_key={self.task_key!r}, status={self.status!r})>"

