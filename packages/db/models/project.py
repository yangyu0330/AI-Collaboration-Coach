"""Project model."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, TimestampMixin, UUIDMixin


class Project(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default=None)

    channels = relationship("Channel", back_populates="project", lazy="selectin")
    members = relationship("User", back_populates="project", lazy="selectin")
    raw_messages = relationship("RawMessage", back_populates="project", lazy="selectin")
    raw_documents = relationship("RawDocument", back_populates="project", lazy="selectin")
    conversation_sessions = relationship(
        "ConversationSession", back_populates="project", lazy="selectin"
    )
    extracted_events = relationship("ExtractedEvent", back_populates="project", lazy="selectin")
    requirements = relationship("RequirementState", back_populates="project", lazy="selectin")
    decisions = relationship("DecisionState", back_populates="project", lazy="selectin")
    tasks = relationship("TaskState", back_populates="project", lazy="selectin")
    issues = relationship("IssueState", back_populates="project", lazy="selectin")
    feedbacks = relationship("FeedbackState", back_populates="project", lazy="selectin")
    wiki_pages = relationship("WikiPage", back_populates="project", lazy="selectin")
    interventions = relationship("Intervention", back_populates="project", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name!r})>"
