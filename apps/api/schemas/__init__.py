"""Pydantic schema package for API payloads."""

from apps.api.schemas.document import (
    DocumentCreate,
    DocumentListItem,
    DocumentListResponse,
    DocumentResponse,
)
from apps.api.schemas.telegram import TelegramChat, TelegramMessage, TelegramUpdate, TelegramUser

__all__ = [
    "DocumentCreate",
    "DocumentResponse",
    "DocumentListItem",
    "DocumentListResponse",
    "TelegramUser",
    "TelegramChat",
    "TelegramMessage",
    "TelegramUpdate",
]
