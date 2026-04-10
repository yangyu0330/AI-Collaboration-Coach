"""RawDocument model."""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, TimestampMixin, UUIDMixin
from packages.shared.enums import SourceType


class RawDocument(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "raw_documents"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default=SourceType.MANUAL_NOTE.value)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        default=None,
    )

    project = relationship("Project", back_populates="raw_documents")
    uploader = relationship("User")

    def __repr__(self) -> str:
        return f"<RawDocument(id={self.id}, title={self.title!r})>"

