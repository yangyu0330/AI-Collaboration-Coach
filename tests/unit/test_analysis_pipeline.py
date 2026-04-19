"""Phase 5B analysis pipeline unit tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from packages.core.services.analysis_service import AnalysisService
from packages.db.models.conversation_session import ConversationSession
from packages.db.models.raw_document import RawDocument
from packages.db.models.raw_message import RawMessage
from packages.db.models.user import User
from packages.shared.enums import EventState, SessionStatus, SourceKind, UserRole


class _FakeResult:
    def __init__(
        self,
        *,
        scalar_one_or_none: object | None = None,
        scalars_all: list[object] | None = None,
    ) -> None:
        self._scalar_one_or_none = scalar_one_or_none
        self._scalars_all = scalars_all or []

    def scalar_one_or_none(self) -> object | None:
        return self._scalar_one_or_none

    def scalars(self) -> "_FakeResult":
        return self

    def all(self) -> list[object]:
        return self._scalars_all


class _FakeDB:
    def __init__(
        self,
        *,
        get_map: dict[tuple[type[object], uuid.UUID], object] | None = None,
        execute_results: list[_FakeResult] | None = None,
    ) -> None:
        self.get_map = get_map or {}
        self.execute_results = execute_results or []
        self.added: list[object] = []
        self.flush_count = 0
        self.commit_count = 0
        self.refreshed: list[object] = []

    async def get(self, model: type[object], target_id: uuid.UUID) -> object | None:
        return self.get_map.get((model, target_id))

    async def execute(self, _stmt) -> _FakeResult:
        if not self.execute_results:
            msg = "No queued execute result."
            raise AssertionError(msg)
        return self.execute_results.pop(0)

    def add_all(self, items: list[object]) -> None:
        self.added.extend(items)

    async def flush(self) -> None:
        self.flush_count += 1

    async def commit(self) -> None:
        self.commit_count += 1

    async def refresh(self, item: object) -> None:
        self.refreshed.append(item)


@pytest.mark.asyncio
async def test_analyze_session_skips_general_and_marks_analyzed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_id = uuid.uuid4()
    channel_id = uuid.uuid4()
    session_id = uuid.uuid4()
    sender_id = uuid.uuid4()
    now = datetime.now(UTC).replace(tzinfo=None)

    session = ConversationSession(
        id=session_id,
        project_id=project_id,
        channel_id=channel_id,
        start_at=now,
        message_count=2,
        session_status=SessionStatus.CLOSED.value,
    )

    sender = User(
        id=sender_id,
        project_id=project_id,
        username="alpha",
        role=UserRole.MEMBER.value,
    )
    msg1 = RawMessage(
        id=uuid.uuid4(),
        project_id=project_id,
        channel_id=channel_id,
        session_id=session_id,
        sender_id=sender_id,
        text="로그인은 OAuth로 가자",
        sent_at=now,
    )
    msg2 = RawMessage(
        id=uuid.uuid4(),
        project_id=project_id,
        channel_id=channel_id,
        session_id=session_id,
        sender_id=sender_id,
        text="좋아, 오늘 안에 반영할게",
        sent_at=now,
    )
    msg1.sender = sender
    msg2.sender = sender

    db = _FakeDB(
        get_map={(ConversationSession, session_id): session},
        execute_results=[_FakeResult(scalars_all=[msg1, msg2])],
    )
    service = AnalysisService(db=db)  # type: ignore[arg-type]

    llm_call = AsyncMock(
        side_effect=[
            {
                "has_events": True,
                "events": [
                    {
                        "event_type": "general",
                        "related_message_indices": [0],
                        "brief": "일반 대화",
                    },
                    {
                        "event_type": "decision",
                        "related_message_indices": [0, 1],
                        "brief": "로그인 방식 확정",
                    },
                ],
            },
            {
                "event_type": "decision",
                "summary": "로그인 방식을 OAuth로 확정",
                "topic": "로그인",
                "details": {
                    "before": "미정",
                    "after": "OAuth",
                    "reason": "구현 속도",
                    "related_people": ["alpha"],
                    "source_quotes": ["로그인은 OAuth로 가자"],
                },
                "confidence": 0.95,
                "fact_type": "confirmed_fact",
            },
        ]
    )
    monkeypatch.setattr("packages.core.services.analysis_service.llm_client.call", llm_call)

    events = await service.analyze_session(session_id)

    assert len(events) == 1
    assert events[0].event_type == "decision"
    assert events[0].source_kind == SourceKind.SESSION.value
    assert events[0].state == EventState.NEEDS_REVIEW.value
    assert session.session_status == SessionStatus.ANALYZED.value
    assert db.flush_count == 1
    assert db.commit_count == 1
    assert len(db.added) == 1
    assert llm_call.await_count == 2


@pytest.mark.asyncio
async def test_analyze_document_is_idempotent_when_events_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_id = uuid.uuid4()
    document_id = uuid.uuid4()

    doc = RawDocument(
        id=document_id,
        project_id=project_id,
        source_type="meeting",
        title="Sprint Notes",
        content="결정 사항 정리",
    )

    db = _FakeDB(
        get_map={(RawDocument, document_id): doc},
        execute_results=[_FakeResult(scalar_one_or_none=uuid.uuid4())],
    )
    service = AnalysisService(db=db)  # type: ignore[arg-type]

    llm_call = AsyncMock()
    monkeypatch.setattr("packages.core.services.analysis_service.llm_client.call", llm_call)

    events = await service.analyze_document(document_id)

    assert events == []
    assert llm_call.await_count == 0
    assert db.commit_count == 0
