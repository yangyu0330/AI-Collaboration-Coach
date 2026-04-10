"""Telegram message ingestion service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.schemas.telegram import TelegramChat, TelegramMessage, TelegramUpdate, TelegramUser
from packages.db.models.channel import Channel
from packages.db.models.raw_message import RawMessage
from packages.db.models.user import User
from packages.shared.enums import UserRole, VisibilityStatus

logger = structlog.get_logger()


class MessageService:
    """Store incoming Telegram updates in project-scoped tables."""

    def __init__(self, db: AsyncSession, project_id: uuid.UUID):
        self.db = db
        self.project_id = project_id

    async def process_update(self, update: TelegramUpdate) -> RawMessage | None:
        """Process one Telegram update and return the persisted message row."""
        message = update.get_message()
        if message is None:
            logger.warning("update_has_no_message", update_id=update.update_id)
            return None

        if update.is_edit:
            return await self._handle_edit(message)
        return await self._handle_new_message(message)

    async def _handle_new_message(
        self,
        message: TelegramMessage,
        *,
        is_edit_fallback: bool = False,
    ) -> RawMessage:
        sender = None
        if message.from_:
            sender = await self._upsert_user(message.from_)

        channel = await self._upsert_channel(message.chat)
        reply_to_message_id = None

        if message.reply_to_message:
            reply_to_message_id = await self._find_message_by_telegram_id(
                chat_id=message.chat.id,
                telegram_message_id=message.reply_to_message.message_id,
            )

        now = self._to_utc_naive(message.date)
        raw_message = RawMessage(
            project_id=self.project_id,
            channel_id=channel.id,
            sender_id=sender.id if sender else None,
            telegram_message_id=message.message_id,
            text=self._extract_text(message),
            message_type=self._detect_message_type(message),
            reply_to_message_id=reply_to_message_id,
            sent_at=now,
            edited_at=now if is_edit_fallback else None,
            visibility_status=VisibilityStatus.VISIBLE.value,
            metadata_=self._extract_metadata(message),
        )
        self.db.add(raw_message)
        await self.db.commit()
        await self.db.refresh(raw_message)

        logger.info(
            "message_saved",
            project_id=str(self.project_id),
            message_id=str(raw_message.id),
            telegram_message_id=message.message_id,
            chat_id=message.chat.id,
            message_type=raw_message.message_type,
            is_edit_fallback=is_edit_fallback,
        )
        return raw_message

    async def _handle_edit(self, message: TelegramMessage) -> RawMessage:
        stmt = select(RawMessage).where(
            RawMessage.project_id == self.project_id,
            RawMessage.channel_id.in_(
                select(Channel.id).where(
                    Channel.project_id == self.project_id,
                    Channel.telegram_chat_id == message.chat.id,
                )
            ),
            RawMessage.telegram_message_id == message.message_id,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            logger.warning(
                "edit_for_unknown_message",
                project_id=str(self.project_id),
                telegram_message_id=message.message_id,
                chat_id=message.chat.id,
            )
            return await self._handle_new_message(message, is_edit_fallback=True)

        if message.from_:
            sender = await self._upsert_user(message.from_)
            existing.sender_id = sender.id

        existing.text = self._extract_text(message)
        existing.message_type = self._detect_message_type(message)
        existing.metadata_ = self._extract_metadata(message)
        existing.edited_at = self._to_utc_naive(message.date)
        await self.db.commit()
        await self.db.refresh(existing)

        logger.info(
            "message_edited",
            project_id=str(self.project_id),
            message_id=str(existing.id),
            telegram_message_id=message.message_id,
        )
        return existing

    async def _upsert_user(self, tg_user: TelegramUser) -> User:
        stmt = select(User).where(
            User.project_id == self.project_id,
            User.telegram_id == tg_user.id,
        )
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                project_id=self.project_id,
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                role=UserRole.MEMBER.value,
            )
            self.db.add(user)
            await self.db.flush()
            logger.info(
                "user_created",
                project_id=str(self.project_id),
                user_id=str(user.id),
                telegram_id=tg_user.id,
            )
            return user

        changed = False
        if tg_user.username is not None and user.username != tg_user.username:
            user.username = tg_user.username
            changed = True
        if tg_user.first_name is not None and user.first_name != tg_user.first_name:
            user.first_name = tg_user.first_name
            changed = True
        if tg_user.last_name is not None and user.last_name != tg_user.last_name:
            user.last_name = tg_user.last_name
            changed = True

        if changed:
            await self.db.flush()

        return user

    async def _upsert_channel(self, tg_chat: TelegramChat) -> Channel:
        stmt = select(Channel).where(
            Channel.project_id == self.project_id,
            Channel.telegram_chat_id == tg_chat.id,
        )
        result = await self.db.execute(stmt)
        channel = result.scalar_one_or_none()

        if channel is None:
            channel = Channel(
                project_id=self.project_id,
                telegram_chat_id=tg_chat.id,
                channel_name=tg_chat.title or tg_chat.username or f"chat_{tg_chat.id}",
                channel_type="telegram",
            )
            self.db.add(channel)
            await self.db.flush()
            logger.info(
                "channel_created",
                project_id=str(self.project_id),
                channel_id=str(channel.id),
                chat_id=tg_chat.id,
            )
            return channel

        new_name = tg_chat.title or tg_chat.username
        if new_name and channel.channel_name != new_name:
            channel.channel_name = new_name
            await self.db.flush()

        return channel

    async def _find_message_by_telegram_id(
        self,
        chat_id: int,
        telegram_message_id: int,
    ) -> uuid.UUID | None:
        stmt = select(RawMessage.id).where(
            RawMessage.project_id == self.project_id,
            RawMessage.channel_id.in_(
                select(Channel.id).where(
                    Channel.project_id == self.project_id,
                    Channel.telegram_chat_id == chat_id,
                )
            ),
            RawMessage.telegram_message_id == telegram_message_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _to_utc_naive(unix_ts: int) -> datetime:
        return datetime.fromtimestamp(unix_ts, tz=UTC).replace(tzinfo=None)

    @staticmethod
    def _extract_text(message: TelegramMessage) -> str | None:
        return message.text or message.caption

    @staticmethod
    def _detect_message_type(message: TelegramMessage) -> str:
        if message.photo:
            return "photo"
        if message.document:
            return "document"
        if message.sticker:
            return "sticker"
        if message.voice:
            return "voice"
        if message.video:
            return "video"
        return "text"

    @staticmethod
    def _extract_metadata(message: TelegramMessage) -> dict[str, Any] | None:
        metadata: dict[str, Any] = {}
        if message.photo:
            metadata["photo_count"] = len(message.photo)
        if message.document:
            metadata["document"] = message.document
        if message.sticker:
            metadata["sticker"] = message.sticker
        if message.voice:
            metadata["voice"] = message.voice
        if message.video:
            metadata["video"] = message.video
        return metadata or None

