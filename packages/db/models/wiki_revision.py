"""WikiRevision model."""

import uuid

from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, TimestampMixin, UUIDMixin


class WikiRevision(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "wiki_revisions"
    __table_args__ = (
        UniqueConstraint("wiki_page_id", "revision_number", name="uq_wiki_revisions_page_revision"),
    )

    wiki_page_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("wiki_pages.id", ondelete="CASCADE"), nullable=False
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content_md: Mapped[str | None] = mapped_column(Text, default=None)
    change_summary: Mapped[str | None] = mapped_column(Text, default=None)

    wiki_page = relationship("WikiPage", back_populates="revisions")

    def __repr__(self) -> str:
        return f"<WikiRevision(wiki_page_id={self.wiki_page_id}, revision_number={self.revision_number})>"

