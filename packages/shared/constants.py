"""Project-wide shared constants."""

from __future__ import annotations

# Priority keywords from Phase 4 spec (§12.3).
PRIORITY_KEYWORDS_KR: list[str] = [
    "교수님",
    "마감",
    "배포",
    "오류",
    "확정",
    "결정",
    "변경",
    "긴급",
    "발표",
    "버그",
    "장애",
    "수정",
    "삭제",
    "추가",
    "필수",
]

PRIORITY_KEYWORDS_EN: list[str] = [
    "deadline",
    "deploy",
    "bug",
    "decision",
    "change",
    "urgent",
    "critical",
    "hotfix",
]

PRIORITY_KEYWORDS: set[str] = {
    *PRIORITY_KEYWORDS_KR,
    *PRIORITY_KEYWORDS_EN,
}

PRIORITY_COMMANDS: set[str] = {
    "/decision",
    "/change",
    "/issue",
    "/feedback",
    "/todo",
}

ANALYSIS_QUEUE = "analysis_queue"
PRIORITY_ANALYSIS_QUEUE = "priority_analysis_queue"
