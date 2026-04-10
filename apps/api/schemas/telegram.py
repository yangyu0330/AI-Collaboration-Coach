"""Pydantic schemas for Telegram webhook payloads."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TelegramUser(BaseModel):
    """Telegram sender snapshot from an update payload."""

    id: int
    is_bot: bool = False
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None


class TelegramChat(BaseModel):
    """Telegram chat metadata from a message payload."""

    id: int
    type: str  # private | group | supergroup | channel
    title: str | None = None
    username: str | None = None


class TelegramMessage(BaseModel):
    """Telegram message payload used for ingestion."""

    model_config = ConfigDict(populate_by_name=True)

    message_id: int
    from_: TelegramUser | None = Field(default=None, alias="from")
    chat: TelegramChat
    date: int  # Unix timestamp
    text: str | None = None
    reply_to_message: TelegramMessage | None = None

    caption: str | None = None

    photo: list[dict[str, Any]] | None = None
    document: dict[str, Any] | None = None
    sticker: dict[str, Any] | None = None
    voice: dict[str, Any] | None = None
    video: dict[str, Any] | None = None


class TelegramUpdate(BaseModel):
    """Telegram webhook update payload."""

    update_id: int
    message: TelegramMessage | None = None
    edited_message: TelegramMessage | None = None

    def get_message(self) -> TelegramMessage | None:
        """Return the present message variant (new or edited)."""
        return self.message or self.edited_message

    @property
    def is_edit(self) -> bool:
        """Return True when this update carries an edited message."""
        return self.edited_message is not None

