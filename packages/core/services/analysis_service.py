"""Analysis service: Classifier -> Extractor multi-step LLM pipeline."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.config import settings
from packages.db.models.conversation_session import ConversationSession
from packages.db.models.extracted_event import ExtractedEvent
from packages.db.models.raw_document import RawDocument
from packages.db.models.raw_message import RawMessage
from packages.llm.client import LLMRole, llm_client
from packages.llm.prompts.classifier import (
    CLASSIFIER_SYSTEM_PROMPT,
    build_classifier_document_prompt,
    build_classifier_user_prompt,
)
from packages.llm.prompts.extractor import (
    EXTRACTOR_SYSTEM_PROMPT,
    build_extractor_document_prompt,
    build_extractor_user_prompt,
)
from packages.llm.schemas import CLASSIFIER_SCHEMA, EXTRACTOR_SCHEMA
from packages.shared.enums import EventState, EventType, SessionStatus, SourceKind

logger = structlog.get_logger()

SUPPORTED_EVENT_TYPES: set[str] = {event_type.value for event_type in EventType}


class AnalysisService:
    """Classifier -> Extractor LLM analysis pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.confidence_threshold = settings.llm_confidence_threshold

    async def analyze_session(self, session_id: uuid.UUID) -> list[ExtractedEvent]:
        """Analyze one closed session and persist extracted events."""
        session = await self.db.get(ConversationSession, session_id)
        if session is None:
            logger.error("session_not_found", session_id=str(session_id))
            return []

        if session.session_status == SessionStatus.ANALYZED.value:
            logger.info("session_already_analyzed", session_id=str(session_id))
            return []

        stmt = (
            select(RawMessage)
            .where(RawMessage.session_id == session_id)
            .options(selectinload(RawMessage.sender))
            .order_by(RawMessage.sent_at)
        )
        result = await self.db.execute(stmt)
        messages = list(result.scalars().all())

        if not messages:
            logger.warning("session_has_no_messages", session_id=str(session_id))
            await self._mark_session_analyzed(session)
            return []

        message_dicts = self._messages_to_dicts(messages)
        classifier_result = await llm_client.call(
            role=LLMRole.CLASSIFIER,
            system_prompt=CLASSIFIER_SYSTEM_PROMPT,
            user_prompt=build_classifier_user_prompt(message_dicts),
            response_schema=CLASSIFIER_SCHEMA,
        )

        if not classifier_result.get("has_events", False):
            logger.info("session_no_events_found", session_id=str(session_id))
            await self._mark_session_analyzed(session)
            return []

        events: list[ExtractedEvent] = []
        for event_candidate in classifier_result.get("events", []):
            event_type = self._candidate_event_type(event_candidate)
            if event_type is None:
                continue

            brief = str(event_candidate.get("brief", ""))
            indices = event_candidate.get("related_message_indices", [])
            related_messages = self._pick_related_messages(message_dicts, indices)

            try:
                extractor_result = await llm_client.call(
                    role=LLMRole.EXTRACTOR,
                    system_prompt=EXTRACTOR_SYSTEM_PROMPT,
                    user_prompt=build_extractor_user_prompt(event_type, brief, related_messages),
                    response_schema=EXTRACTOR_SCHEMA,
                )
                event = self._create_event(
                    project_id=session.project_id,
                    source_kind=SourceKind.SESSION,
                    source_id=session_id,
                    data=extractor_result,
                )
                events.append(event)
            except Exception as exc:
                logger.error(
                    "session_extractor_failed",
                    session_id=str(session_id),
                    event_type=event_type,
                    error=str(exc),
                )

        if events:
            self.db.add_all(events)
            await self.db.flush()

        session.session_status = SessionStatus.ANALYZED.value
        await self.db.commit()

        for event in events:
            await self.db.refresh(event)

        logger.info(
            "session_analyzed",
            session_id=str(session_id),
            events_count=len(events),
        )
        return events

    async def analyze_document(self, document_id: uuid.UUID) -> list[ExtractedEvent]:
        """Analyze one uploaded document and persist extracted events."""
        document = await self.db.get(RawDocument, document_id)
        if document is None:
            logger.error("document_not_found", document_id=str(document_id))
            return []

        existing_stmt = (
            select(ExtractedEvent.id)
            .where(ExtractedEvent.source_kind == SourceKind.DOCUMENT.value)
            .where(ExtractedEvent.source_id == document_id)
            .limit(1)
        )
        existing_result = await self.db.execute(existing_stmt)
        if existing_result.scalar_one_or_none() is not None:
            logger.info("document_already_analyzed", document_id=str(document_id))
            return []

        classifier_result = await llm_client.call(
            role=LLMRole.CLASSIFIER,
            system_prompt=CLASSIFIER_SYSTEM_PROMPT,
            user_prompt=build_classifier_document_prompt(
                title=document.title,
                content=document.content,
                source_type=document.source_type,
            ),
            response_schema=CLASSIFIER_SCHEMA,
        )

        if not classifier_result.get("has_events", False):
            logger.info("document_no_events_found", document_id=str(document_id))
            return []

        events: list[ExtractedEvent] = []
        for event_candidate in classifier_result.get("events", []):
            event_type = self._candidate_event_type(event_candidate)
            if event_type is None:
                continue

            brief = str(event_candidate.get("brief", ""))
            try:
                extractor_result = await llm_client.call(
                    role=LLMRole.EXTRACTOR,
                    system_prompt=EXTRACTOR_SYSTEM_PROMPT,
                    user_prompt=build_extractor_document_prompt(
                        event_type=event_type,
                        brief=brief,
                        title=document.title,
                        content=document.content,
                    ),
                    response_schema=EXTRACTOR_SCHEMA,
                )
                event = self._create_event(
                    project_id=document.project_id,
                    source_kind=SourceKind.DOCUMENT,
                    source_id=document_id,
                    data=extractor_result,
                )
                events.append(event)
            except Exception as exc:
                logger.error(
                    "document_extractor_failed",
                    document_id=str(document_id),
                    event_type=event_type,
                    error=str(exc),
                )

        if events:
            self.db.add_all(events)
            await self.db.commit()
            for event in events:
                await self.db.refresh(event)

        logger.info(
            "document_analyzed",
            document_id=str(document_id),
            events_count=len(events),
        )
        return events

    async def analyze_priority_message(self, message_id: uuid.UUID) -> list[ExtractedEvent]:
        """Analyze one priority-marked message and persist extracted events."""
        existing_stmt = (
            select(ExtractedEvent.id)
            .where(ExtractedEvent.source_kind == SourceKind.MESSAGE.value)
            .where(ExtractedEvent.source_id == message_id)
            .limit(1)
        )
        existing_result = await self.db.execute(existing_stmt)
        if existing_result.scalar_one_or_none() is not None:
            logger.info("priority_message_already_analyzed", message_id=str(message_id))
            return []

        stmt = (
            select(RawMessage)
            .where(RawMessage.id == message_id)
            .options(selectinload(RawMessage.sender))
        )
        result = await self.db.execute(stmt)
        message = result.scalar_one_or_none()
        if message is None or not message.text:
            logger.warning("priority_message_missing_or_empty", message_id=str(message_id))
            return []

        message_dicts = self._messages_to_dicts([message])
        classifier_result = await llm_client.call(
            role=LLMRole.CLASSIFIER,
            system_prompt=CLASSIFIER_SYSTEM_PROMPT,
            user_prompt=build_classifier_user_prompt(message_dicts),
            response_schema=CLASSIFIER_SCHEMA,
        )

        if not classifier_result.get("has_events", False):
            logger.info("priority_message_no_events_found", message_id=str(message_id))
            return []

        events: list[ExtractedEvent] = []
        for event_candidate in classifier_result.get("events", []):
            event_type = self._candidate_event_type(event_candidate)
            if event_type is None:
                continue

            brief = str(event_candidate.get("brief", ""))
            try:
                extractor_result = await llm_client.call(
                    role=LLMRole.EXTRACTOR,
                    system_prompt=EXTRACTOR_SYSTEM_PROMPT,
                    user_prompt=build_extractor_user_prompt(event_type, brief, message_dicts),
                    response_schema=EXTRACTOR_SCHEMA,
                )
                event = self._create_event(
                    project_id=message.project_id,
                    source_kind=SourceKind.MESSAGE,
                    source_id=message_id,
                    data=extractor_result,
                )
                events.append(event)
            except Exception as exc:
                logger.error(
                    "priority_message_extractor_failed",
                    message_id=str(message_id),
                    event_type=event_type,
                    error=str(exc),
                )

        if events:
            self.db.add_all(events)
            await self.db.commit()
            for event in events:
                await self.db.refresh(event)

        logger.info(
            "priority_message_analyzed",
            message_id=str(message_id),
            events_count=len(events),
        )
        return events

    def _messages_to_dicts(self, messages: list[RawMessage]) -> list[dict]:
        """Convert RawMessage rows into prompt-ready dictionaries."""
        result: list[dict] = []
        for index, message in enumerate(messages):
            sender = "unknown"
            if message.sender is not None:
                sender = message.sender.username or message.sender.first_name or "unknown"
            result.append(
                {
                    "index": index,
                    "sender": sender,
                    "text": message.text or "(media message)",
                    "time": message.sent_at.strftime("%H:%M") if message.sent_at else "",
                }
            )
        return result

    def _pick_related_messages(self, all_messages: list[dict], indices: object) -> list[dict]:
        """Return classifier-selected related messages or fallback to the full context."""
        if not isinstance(indices, list):
            return all_messages

        related: list[dict] = []
        for raw_index in indices:
            if isinstance(raw_index, int) and 0 <= raw_index < len(all_messages):
                related.append(all_messages[raw_index])

        return related or all_messages

    @staticmethod
    def _candidate_event_type(event_candidate: object) -> str | None:
        """Validate classifier event type and exclude unsupported/general entries."""
        if not isinstance(event_candidate, dict):
            return None

        event_type = event_candidate.get("event_type")
        if not isinstance(event_type, str):
            return None

        if event_type == "general":
            return None

        if event_type not in SUPPORTED_EVENT_TYPES:
            logger.warning("unsupported_event_type_from_classifier", event_type=event_type)
            return None

        return event_type

    def _create_event(
        self,
        project_id: uuid.UUID,
        source_kind: SourceKind,
        source_id: uuid.UUID,
        data: dict,
    ) -> ExtractedEvent:
        """Build an ExtractedEvent row from one extractor response payload."""
        event_type = data.get("event_type")
        if not isinstance(event_type, str) or event_type not in SUPPORTED_EVENT_TYPES:
            raise ValueError(f"Unsupported event type from extractor: {event_type!r}")

        raw_confidence = data.get("confidence", 0.0)
        try:
            confidence = float(raw_confidence)
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))

        state = (
            EventState.NEEDS_REVIEW
            if confidence >= self.confidence_threshold
            else EventState.EXTRACTED
        )

        topic = data.get("topic")
        if topic is not None and not isinstance(topic, str):
            topic = str(topic)

        details = data.get("details")
        if details is not None and not isinstance(details, dict):
            details = None

        fact_type = data.get("fact_type")
        if fact_type is not None and not isinstance(fact_type, str):
            fact_type = str(fact_type)

        return ExtractedEvent(
            project_id=project_id,
            source_kind=source_kind.value,
            source_id=source_id,
            event_type=event_type,
            state=state.value,
            topic=topic,
            summary=str(data.get("summary", "")),
            details=details,
            confidence=confidence,
            fact_type=fact_type,
        )

    async def _mark_session_analyzed(self, session: ConversationSession) -> None:
        """Update one session row to analyzed status."""
        session.session_status = SessionStatus.ANALYZED.value
        await self.db.commit()
