"""Unit tests for review workflow service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from packages.core.services.review_service import ReviewService
from packages.core.services.state_transition import InvalidTransitionError
from packages.db.models.extracted_event import ExtractedEvent
from packages.db.models.review_action import ReviewAction
from packages.shared.enums import EventState, ReviewActionType, SourceKind


class _FakeResult:
    def __init__(
        self,
        *,
        scalar_value: object | None = None,
        scalar_one_or_none: object | None = None,
        scalars_all: list[object] | None = None,
    ) -> None:
        self._scalar_value = scalar_value
        self._scalar_one_or_none = scalar_one_or_none
        self._scalars_all = scalars_all or []

    def scalar(self) -> object | None:
        return self._scalar_value

    def scalar_one_or_none(self) -> object | None:
        return self._scalar_one_or_none

    def scalars(self) -> "_FakeResult":
        return self

    def all(self) -> list[object]:
        return self._scalars_all


class _FakeDB:
    def __init__(self, *, execute_results: list[_FakeResult] | None = None) -> None:
        self.execute_results = execute_results or []
        self.added: list[object] = []
        self.commit_count = 0
        self.refreshed: list[object] = []

    async def execute(self, _stmt) -> _FakeResult:
        if not self.execute_results:
            msg = "No queued execute result."
            raise AssertionError(msg)
        return self.execute_results.pop(0)

    def add(self, item: object) -> None:
        self.added.append(item)

    async def commit(self) -> None:
        self.commit_count += 1

    async def refresh(self, item: object) -> None:
        self.refreshed.append(item)


def _make_event(*, state: EventState = EventState.NEEDS_REVIEW) -> ExtractedEvent:
    now = datetime.now(UTC).replace(tzinfo=None)
    return ExtractedEvent(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        source_kind=SourceKind.SESSION.value,
        source_id=uuid.uuid4(),
        event_type="decision",
        state=state.value,
        topic="로그인",
        summary="로그인 방식을 OAuth로 선택",
        details={"before": "미정", "after": "OAuth"},
        confidence=0.91,
        fact_type="confirmed_fact",
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_get_pending_events_returns_events_and_total() -> None:
    event = _make_event()
    db = _FakeDB(
        execute_results=[
            _FakeResult(scalar_value=3),
            _FakeResult(scalars_all=[event]),
        ]
    )
    service = ReviewService(db=db)  # type: ignore[arg-type]

    events, total = await service.get_pending_events(
        project_id=event.project_id,
        limit=10,
        offset=0,
    )

    assert total == 3
    assert events == [event]


@pytest.mark.asyncio
async def test_process_review_approve_changes_state_and_logs_action() -> None:
    event = _make_event(state=EventState.NEEDS_REVIEW)
    db = _FakeDB(execute_results=[_FakeResult(scalar_one_or_none=event)])
    service = ReviewService(db=db)  # type: ignore[arg-type]

    updated_event, review_action, previous_state = await service.process_review(
        project_id=event.project_id,
        event_id=event.id,
        action=ReviewActionType.APPROVE,
        review_note="승인",
    )

    assert previous_state == EventState.NEEDS_REVIEW.value
    assert updated_event.state == EventState.APPROVED.value
    assert review_action.action == ReviewActionType.APPROVE.value
    assert db.commit_count == 1
    assert any(isinstance(item, ReviewAction) for item in db.added)


@pytest.mark.asyncio
async def test_process_review_hold_keeps_state_and_logs_action() -> None:
    event = _make_event(state=EventState.NEEDS_REVIEW)
    db = _FakeDB(execute_results=[_FakeResult(scalar_one_or_none=event)])
    service = ReviewService(db=db)  # type: ignore[arg-type]

    updated_event, review_action, previous_state = await service.process_review(
        project_id=event.project_id,
        event_id=event.id,
        action=ReviewActionType.HOLD,
        review_note="추가 검토 필요",
    )

    assert previous_state == EventState.NEEDS_REVIEW.value
    assert updated_event.state == EventState.NEEDS_REVIEW.value
    assert review_action.action == ReviewActionType.HOLD.value
    assert db.commit_count == 1


@pytest.mark.asyncio
async def test_process_review_edit_and_approve_applies_patch() -> None:
    event = _make_event(state=EventState.NEEDS_REVIEW)
    db = _FakeDB(execute_results=[_FakeResult(scalar_one_or_none=event)])
    service = ReviewService(db=db)  # type: ignore[arg-type]

    updated_event, review_action, _ = await service.process_review(
        project_id=event.project_id,
        event_id=event.id,
        action=ReviewActionType.EDIT_AND_APPROVE,
        patch={"summary": "수정된 요약", "confidence": 0.8},
    )

    assert updated_event.state == EventState.APPROVED.value
    assert updated_event.summary == "수정된 요약"
    assert updated_event.confidence == 0.8
    assert review_action.action == ReviewActionType.EDIT_AND_APPROVE.value


@pytest.mark.asyncio
async def test_process_review_edit_and_approve_rejects_unknown_patch_field() -> None:
    event = _make_event(state=EventState.NEEDS_REVIEW)
    db = _FakeDB(execute_results=[_FakeResult(scalar_one_or_none=event)])
    service = ReviewService(db=db)  # type: ignore[arg-type]

    with pytest.raises(ValueError) as exc_info:
        await service.process_review(
            project_id=event.project_id,
            event_id=event.id,
            action=ReviewActionType.EDIT_AND_APPROVE,
            patch={"summry": "오타 필드"},
        )

    assert "summry" in str(exc_info.value)
    assert event.state == EventState.NEEDS_REVIEW.value
    assert db.commit_count == 0
    assert db.added == []


@pytest.mark.asyncio
async def test_process_review_raises_when_invalid_transition() -> None:
    event = _make_event(state=EventState.APPLIED)
    db = _FakeDB(execute_results=[_FakeResult(scalar_one_or_none=event)])
    service = ReviewService(db=db)  # type: ignore[arg-type]

    with pytest.raises(InvalidTransitionError):
        await service.process_review(
            project_id=event.project_id,
            event_id=event.id,
            action=ReviewActionType.APPROVE,
        )


@pytest.mark.asyncio
async def test_process_review_raises_when_event_not_found() -> None:
    db = _FakeDB(execute_results=[_FakeResult(scalar_one_or_none=None)])
    service = ReviewService(db=db)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="이벤트를 찾을 수 없습니다"):
        await service.process_review(
            project_id=uuid.uuid4(),
            event_id=uuid.uuid4(),
            action=ReviewActionType.APPROVE,
        )
