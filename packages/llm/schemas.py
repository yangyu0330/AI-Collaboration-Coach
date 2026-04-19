"""JSON schemas for Structured Outputs responses."""

CLASSIFIER_EVENT_TYPES: list[str] = [
    "decision",
    "requirement_change",
    "task",
    "issue",
    "feedback",
    "question",
    "general",
]

EXTRACTOR_EVENT_TYPES: list[str] = [
    "decision",
    "requirement_change",
    "task",
    "issue",
    "feedback",
    "question",
]

FACT_TYPES: list[str] = [
    "confirmed_fact",
    "inferred_interpretation",
    "unresolved_ambiguity",
]


CLASSIFIER_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "event_type": {"type": "string", "enum": CLASSIFIER_EVENT_TYPES},
                    "related_message_indices": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "해당 이벤트와 관련된 메시지 인덱스 (0-based).",
                    },
                    "brief": {
                        "type": "string",
                        "description": "이벤트 한 줄 요약.",
                    },
                },
                "required": ["event_type", "related_message_indices", "brief"],
                "additionalProperties": False,
            },
        },
        "has_events": {
            "type": "boolean",
            "description": "이벤트 존재 여부.",
        },
    },
    "required": ["events", "has_events"],
    "additionalProperties": False,
}


EXTRACTOR_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "event_type": {"type": "string", "enum": EXTRACTOR_EVENT_TYPES},
        "summary": {
            "type": "string",
            "description": "핵심 내용 요약.",
        },
        "topic": {
            "type": "string",
            "description": "관련 주제/영역.",
        },
        "details": {
            "type": "object",
            "properties": {
                "before": {
                    "type": ["string", "null"],
                    "description": "변경 전 상태(없으면 null).",
                },
                "after": {
                    "type": ["string", "null"],
                    "description": "변경 후 상태(없으면 null).",
                },
                "reason": {
                    "type": ["string", "null"],
                    "description": "변경/결정 이유.",
                },
                "related_people": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "관련된 사람 목록.",
                },
                "source_quotes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "근거 원문 인용(최대 3개 권장).",
                },
            },
            "required": [
                "before",
                "after",
                "reason",
                "related_people",
                "source_quotes",
            ],
            "additionalProperties": False,
        },
        "confidence": {
            "type": "number",
            "description": "0.0 이상 1.0 이하 신뢰도 점수.",
        },
        "fact_type": {"type": "string", "enum": FACT_TYPES},
    },
    "required": [
        "event_type",
        "summary",
        "topic",
        "details",
        "confidence",
        "fact_type",
    ],
    "additionalProperties": False,
}

