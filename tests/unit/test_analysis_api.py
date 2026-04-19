"""Phase 5B analysis enqueue API tests."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


def test_enqueue_session_analysis_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    queued: dict[str, str] = {}

    class _FakeTask:
        @staticmethod
        def delay(target_id: str):
            queued["target_id"] = target_id
            return SimpleNamespace(id="task-session-1")

    monkeypatch.setattr("apps.worker.tasks.analysis_tasks.analyze_session_task", _FakeTask())
    client = TestClient(app)

    session_id = uuid.uuid4()
    response = client.post(f"/api/v1/analysis/sessions/{session_id}")

    assert response.status_code == 202
    body = response.json()
    assert body["ok"] is True
    assert body["task_name"] == "analyze_session"
    assert body["task_id"] == "task-session-1"
    assert body["target_id"] == str(session_id)
    assert queued["target_id"] == str(session_id)


def test_enqueue_document_analysis_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    queued: dict[str, str] = {}

    class _FakeTask:
        @staticmethod
        def delay(target_id: str):
            queued["target_id"] = target_id
            return SimpleNamespace(id="task-document-1")

    monkeypatch.setattr("apps.worker.tasks.analysis_tasks.analyze_document_task", _FakeTask())
    client = TestClient(app)

    document_id = uuid.uuid4()
    response = client.post(f"/api/v1/analysis/documents/{document_id}")

    assert response.status_code == 202
    body = response.json()
    assert body["ok"] is True
    assert body["task_name"] == "analyze_document"
    assert body["task_id"] == "task-document-1"
    assert body["target_id"] == str(document_id)
    assert queued["target_id"] == str(document_id)


def test_enqueue_priority_message_analysis_returns_503_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FailingTask:
        @staticmethod
        def delay(target_id: str):
            raise RuntimeError(f"queue down for {target_id}")

    monkeypatch.setattr(
        "apps.worker.tasks.analysis_tasks.analyze_priority_message_task",
        _FailingTask(),
    )
    client = TestClient(app)

    message_id = uuid.uuid4()
    response = client.post(f"/api/v1/analysis/priority-messages/{message_id}")

    assert response.status_code == 503
    assert response.json()["detail"] == "Failed to enqueue analysis task."
