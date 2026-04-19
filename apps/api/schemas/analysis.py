"""Schemas for analysis task enqueue API."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class AnalysisTaskQueuedResponse(BaseModel):
    """Task enqueue response payload."""

    ok: bool
    task_name: str
    task_id: str | None
    target_id: uuid.UUID
