"""Pydantic schema package for API payloads."""

from apps.api.schemas.analysis import AnalysisTaskQueuedResponse
from apps.api.schemas.document import (
    DocumentCreate,
    DocumentListItem,
    DocumentListResponse,
    DocumentResponse,
)
from apps.api.schemas.review import (
    EventDetailResponse,
    EventSummaryResponse,
    PendingReviewsResponse,
    ReviewActionRequest,
    ReviewActionResponse,
)
from apps.api.schemas.telegram import TelegramChat, TelegramMessage, TelegramUpdate, TelegramUser

__all__ = [
    "AnalysisTaskQueuedResponse",
    "DocumentCreate",
    "DocumentResponse",
    "DocumentListItem",
    "DocumentListResponse",
    "ReviewActionRequest",
    "ReviewActionResponse",
    "EventDetailResponse",
    "EventSummaryResponse",
    "PendingReviewsResponse",
    "TelegramUser",
    "TelegramChat",
    "TelegramMessage",
    "TelegramUpdate",
]
