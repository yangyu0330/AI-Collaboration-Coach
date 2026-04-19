"""Pydantic schemas for review queue and review actions."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from packages.shared.enums import ReviewActionType

ALLOWED_FACT_TYPES = {
    "confirmed_fact",
    "inferred_interpretation",
    "unresolved_ambiguity",
}


class ReviewActionRequest(BaseModel):
    """Review action request payload."""

    action: ReviewActionType = Field(
        ...,
        description="승인/반려/보류/수정 후 승인",
        examples=["approve"],
    )
    review_note: str | None = Field(
        default=None,
        description="검토 의견 (선택)",
        max_length=2000,
    )
    patch: dict[str, Any] | None = Field(
        default=None,
        description=(
            "수정 내용 (edit_and_approve 시 필수). "
            '예: {"summary": "수정된 요약", "details": {...}}'
        ),
    )

    @model_validator(mode="after")
    def validate_patch_required(self) -> "ReviewActionRequest":
        if self.action == ReviewActionType.EDIT_AND_APPROVE and not self.patch:
            msg = "edit_and_approve 액션 시 patch 필드는 필수입니다."
            raise ValueError(msg)
        return self


class PatchData(BaseModel):
    """Allowed patch fields for edit-and-approve action."""

    model_config = ConfigDict(extra="forbid")

    summary: str | None = Field(default=None, max_length=500)
    topic: str | None = Field(default=None, max_length=200)
    details: dict[str, Any] | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    fact_type: str | None = None

    @field_validator("fact_type")
    @classmethod
    def validate_fact_type(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_FACT_TYPES:
            msg = f"fact_type은 {ALLOWED_FACT_TYPES} 중 하나여야 합니다: {value!r}"
            raise ValueError(msg)
        return value


class EventDetailResponse(BaseModel):
    """Detailed review event payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    source_kind: str
    source_id: uuid.UUID
    event_type: str
    state: str
    topic: str | None
    summary: str
    details: dict[str, Any] | None
    confidence: float
    fact_type: str | None
    created_at: datetime | None


class EventSummaryResponse(BaseModel):
    """Review queue item payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    state: str
    topic: str | None
    summary: str
    confidence: float
    fact_type: str | None
    created_at: datetime | None


class ReviewActionResponse(BaseModel):
    """Review action response payload."""

    event_id: uuid.UUID
    action: str
    previous_state: str
    new_state: str
    review_action_id: uuid.UUID
    message: str


class PendingReviewsResponse(BaseModel):
    """Review queue response payload."""

    project_id: uuid.UUID
    total_count: int
    events: list[EventSummaryResponse]
