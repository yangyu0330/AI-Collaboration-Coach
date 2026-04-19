"""Phase 5A LLM infrastructure tests."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from packages.llm.client import LLMClient, LLMRole
from packages.llm.prompts.classifier import (
    MAX_CHARS_PER_MESSAGE,
    build_classifier_user_prompt,
)
from packages.llm.prompts.extractor import build_extractor_user_prompt
from packages.llm.schemas import CLASSIFIER_SCHEMA


@dataclass
class _FakeUsage:
    prompt_tokens: int = 12
    completion_tokens: int = 8
    total_tokens: int = 20


class _FakeCompletions:
    def __init__(self, payload: str) -> None:
        self.payload = payload
        self.calls: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return SimpleNamespace(
            usage=_FakeUsage(),
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.payload))],
        )


class _FakeOpenAI:
    def __init__(self, payload: str) -> None:
        self.completions = _FakeCompletions(payload)
        self.chat = SimpleNamespace(completions=self.completions)


@pytest.mark.asyncio
async def test_llm_client_routes_model_and_applies_json_schema() -> None:
    client = LLMClient()
    fake_openai = _FakeOpenAI(payload='{"events": [], "has_events": false}')
    client.client = fake_openai

    result = await client.call(
        role=LLMRole.CLASSIFIER,
        system_prompt="system",
        user_prompt="user",
        response_schema=CLASSIFIER_SCHEMA,
    )

    assert result == {"events": [], "has_events": False}
    assert len(fake_openai.completions.calls) == 1

    call = fake_openai.completions.calls[0]
    assert call["model"] == "gpt-4.1-nano"
    assert call["response_format"]["type"] == "json_schema"
    assert call["response_format"]["json_schema"]["strict"] is True


@pytest.mark.asyncio
async def test_llm_client_uses_json_object_without_schema() -> None:
    client = LLMClient()
    fake_openai = _FakeOpenAI(payload='{"ok": true}')
    client.client = fake_openai

    result = await client.call(
        role=LLMRole.EXTRACTOR,
        system_prompt="system",
        user_prompt="user",
    )

    assert result == {"ok": True}
    call = fake_openai.completions.calls[0]
    assert call["model"] == "gpt-4.1"
    assert call["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_llm_client_raises_when_content_is_not_json() -> None:
    client = LLMClient()
    fake_openai = _FakeOpenAI(payload="not-json")
    client.client = fake_openai

    with pytest.raises(ValueError, match="non-JSON"):
        await client.call(
            role=LLMRole.CLASSIFIER,
            system_prompt="system",
            user_prompt="user",
            response_schema=CLASSIFIER_SCHEMA,
        )


def test_classifier_prompt_truncates_long_inputs() -> None:
    long_text = "a" * (MAX_CHARS_PER_MESSAGE + 50)
    messages = [
        {"index": i, "sender": "tester", "text": long_text, "time": "14:30"}
        for i in range(101)
    ]

    prompt = build_classifier_user_prompt(messages)

    assert "(전체 101개 중 최근 100개만 표시)" in prompt
    assert "[0] (14:30) tester:" not in prompt
    assert "[100] (14:30) tester:" in prompt
    assert "a" * MAX_CHARS_PER_MESSAGE in prompt
    assert "a" * (MAX_CHARS_PER_MESSAGE + 1) not in prompt


def test_extractor_prompt_contains_event_context() -> None:
    prompt = build_extractor_user_prompt(
        event_type="decision",
        brief="로그인 OAuth 결정",
        related_messages=[
            {"sender": "김철수", "text": "OAuth로 하자", "time": "14:30"},
            {"sender": "이영희", "text": "좋아", "time": "14:31"},
        ],
    )

    assert "이벤트 유형: decision" in prompt
    assert "Classifier 요약: 로그인 OAuth 결정" in prompt
    assert "(14:30) 김철수: OAuth로 하자" in prompt
    assert "(14:31) 이영희: 좋아" in prompt

