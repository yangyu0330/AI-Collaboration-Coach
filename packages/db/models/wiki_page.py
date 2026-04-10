"""WikiPage model."""

import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, TimestampMixin, UUIDMixin


class WikiPage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "wiki_pages"
    __table_args__ = (UniqueConstraint("project_id", "slug", name="uq_wiki_pages_project_slug"),)

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content_md: Mapped[str | None] = mapped_column(Text, default=None)
    derived_from: Mapped[dict | None] = mapped_column(JSONB, default=None)

    project = relationship("Project", back_populates="wiki_pages")
    revisions = relationship("WikiRevision", back_populates="wiki_page", lazy="selectin")

    def __repr__(self) -> str:
        return f"<WikiPage(slug={self.slug!r}, title={self.title!r})>"

