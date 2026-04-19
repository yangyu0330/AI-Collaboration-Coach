"""Phase 5B Celery analysis task tests."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from apps.worker.tasks.analysis_tasks import _run_analysis


class _FakeSessionContext:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeSessionFactory:
    def __call__(self) -> _FakeSessionContext:
        return _FakeSessionContext()


@pytest.mark.asyncio
async def test_run_analysis_dispatches_session(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}

    class _FakeAnalysisService:
        def __init__(self, db) -> None:
            calls["db"] = db

        async def analyze_session(self, target_id: uuid.UUID):
            calls["target_id"] = target_id
            return [SimpleNamespace(id=uuid.uuid4())]

        async def analyze_document(self, target_id: uuid.UUID):
            raise AssertionError(f"unexpected analyze_document call for {target_id}")

        async def analyze_priority_message(self, target_id: uuid.UUID):
            raise AssertionError(f"unexpected analyze_priority_message call for {target_id}")

    monkeypatch.setattr(
        "packages.db.session.get_session_factory",
        lambda: _FakeSessionFactory(),
    )
    monkeypatch.setattr(
        "packages.core.services.analysis_service.AnalysisService",
        _FakeAnalysisService,
    )

    target_id = uuid.uuid4()
    result = await _run_analysis("session", target_id)

    assert result["task_type"] == "session"
    assert result["target_id"] == str(target_id)
    assert result["events_extracted"] == 1
    assert len(result["event_ids"]) == 1
    assert calls["target_id"] == target_id


@pytest.mark.asyncio
async def test_run_analysis_raises_on_unknown_task_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeAnalysisService:
        def __init__(self, db) -> None:
            _ = db

        async def analyze_session(self, target_id: uuid.UUID):
            return []

        async def analyze_document(self, target_id: uuid.UUID):
            return []

        async def analyze_priority_message(self, target_id: uuid.UUID):
            return []

    monkeypatch.setattr(
        "packages.db.session.get_session_factory",
        lambda: _FakeSessionFactory(),
    )
    monkeypatch.setattr(
        "packages.core.services.analysis_service.AnalysisService",
        _FakeAnalysisService,
    )

    with pytest.raises(ValueError, match="Unknown task type"):
        await _run_analysis("unsupported", uuid.uuid4())
