"""Pydantic schema package for API payloads."""

from apps.api.schemas.telegram import TelegramChat, TelegramMessage, TelegramUpdate, TelegramUser

__all__ = [
    "TelegramUser",
    "TelegramChat",
    "TelegramMessage",
    "TelegramUpdate",
]

