"""OpenAI LLM client wrapper with model routing and retry logic."""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any

import structlog
from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from apps.api.config import settings

logger = structlog.get_logger()


class LLMRole(StrEnum):
    """Role names used to route requests to the appropriate model."""

    CLASSIFIER = "classifier"
    EXTRACTOR = "extractor"
    COMPARATOR = "comparator"
    REVIEW_ASSISTANT = "review_assistant"
    WIKI_WRITER = "wiki_writer"
    COACH = "coach"


MODEL_ROUTING: dict[LLMRole, str] = {
    LLMRole.CLASSIFIER: "gpt-4.1-nano",
    LLMRole.EXTRACTOR: "gpt-4.1",
    LLMRole.COMPARATOR: "gpt-4.1",
    LLMRole.REVIEW_ASSISTANT: "gpt-4.1-nano",
    LLMRole.WIKI_WRITER: "gpt-4.1",
    LLMRole.COACH: "gpt-4.1-nano",
}


class LLMClient:
    """
    OpenAI API wrapper.

    Features:
    - Role-based model routing.
    - Structured Outputs via JSON schema.
    - Exponential-backoff retries for transient API failures.
    """

    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((APIConnectionError, RateLimitError, APITimeoutError)),
        reraise=True,
    )
    async def call(
        self,
        role: LLMRole,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, Any] | None = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """Call the model and return a parsed JSON dictionary."""
        model = MODEL_ROUTING[role]

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }

        if response_schema:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "response",
                    "strict": True,
                    "schema": response_schema,
                },
            }
        else:
            kwargs["response_format"] = {"type": "json_object"}

        logger.info("llm_call_start", role=role.value, model=model)
        response = await self.client.chat.completions.create(**kwargs)

        usage = response.usage
        if usage:
            logger.info(
                "llm_call_complete",
                role=role.value,
                model=model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
            )

        if not response.choices:
            raise ValueError("LLM returned no choices")

        content = response.choices[0].message.content
        if content is None:
            raise ValueError("LLM returned empty content")

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            logger.error("llm_invalid_json_response", role=role.value, model=model)
            raise ValueError("LLM returned non-JSON content") from exc


llm_client = LLMClient()
