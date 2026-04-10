"""Rule-based priority detection for incoming messages."""

from __future__ import annotations

from dataclasses import dataclass

from packages.shared.constants import PRIORITY_COMMANDS, PRIORITY_KEYWORDS


@dataclass(slots=True)
class PriorityResult:
    """Priority detection result."""

    is_priority: bool
    matched_keywords: list[str]
    matched_command: str | None


class PriorityDetector:
    """Detect priority candidates by keywords and slash commands."""

    def check(self, text: str | None) -> PriorityResult:
        """Return whether the message should be treated as priority."""
        if not text:
            return PriorityResult(
                is_priority=False,
                matched_keywords=[],
                matched_command=None,
            )

        normalized = text.strip()
        lowered = normalized.lower()

        matched_command = self._check_commands(lowered)
        matched_keywords = self._check_keywords(lowered)
        is_priority = matched_command is not None or len(matched_keywords) > 0
        return PriorityResult(
            is_priority=is_priority,
            matched_keywords=matched_keywords,
            matched_command=matched_command,
        )

    def _check_commands(self, text: str) -> str | None:
        for command in PRIORITY_COMMANDS:
            if text.startswith(command):
                return command
        return None

    def _check_keywords(self, text: str) -> list[str]:
        matched: list[str] = []
        for keyword in PRIORITY_KEYWORDS:
            if keyword.lower() in text:
                matched.append(keyword)
        return matched
