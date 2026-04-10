"""Pydantic schemas for document upload and retrieval."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from packages.shared.enums import SourceType


class DocumentCreate(BaseModel):
    """Document upload request schema."""

    project_id: uuid.UUID
    source_type: SourceType
    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., min_length=1)
    created_by: uuid.UUID | None = None

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, value: str) -> str:
        """Reject whitespace-only content."""
        if not value.strip():
            msg = "content cannot be blank."
            raise ValueError(msg)
        return value


class DocumentResponse(BaseModel):
    """Document API response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    source_type: SourceType
    title: str
    content: str
    created_by: uuid.UUID | None = None
    created_at: datetime


class DocumentListItem(BaseModel):
    """Document list item without body content."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    source_type: SourceType
    title: str
    created_by: uuid.UUID | None = None
    created_at: datetime


class DocumentListResponse(BaseModel):
    """Document list response."""

    documents: list[DocumentListItem]
    total: int
