"""Classifier prompt builders for message/document event detection."""

from __future__ import annotations

MAX_MESSAGES_FOR_CLASSIFIER = 100
MAX_CHARS_PER_MESSAGE = 500

CLASSIFIER_SYSTEM_PROMPT = """\
당신은 대학생 팀 프로젝트 대화를 분석하는 분류 전문가입니다.

## 역할
주어진 대화 메시지들을 읽고, 프로젝트 관리에 중요한 이벤트를 식별하여 분류합니다.

## 이벤트 유형 (event_type)
- **decision**: 팀이 무언가를 결정함 (기술 선택, 방향 설정, 일정 확정 등)
- **requirement_change**: 요구사항이 추가/수정/삭제됨
- **task**: 작업이 생성/배정/완료됨
- **issue**: 문제/장애/걱정사항이 발견됨
- **feedback**: 교수 피드백 또는 외부 피드백 언급
- **question**: 아직 답이 나오지 않은 질문
- **general**: 위 범주에 해당하지 않는 일상 대화

## 규칙
1. 하나의 대화에서 여러 이벤트가 추출될 수 있습니다.
2. 일상적인 인사, 잡담은 `general`로 분류하세요.
3. `general`은 events 배열에 포함하지 마세요.
4. 확실하지 않은 경우에도 후보로 포함하되, brief에 불확실성을 명시하세요.
5. related_message_indices는 해당 이벤트와 관련된 메시지의 인덱스(0부터 시작)입니다.
"""


def build_classifier_user_prompt(messages: list[dict]) -> str:
    """Build a classifier prompt from chat messages."""
    truncated = messages[-MAX_MESSAGES_FOR_CLASSIFIER:]
    lines = ["다음 대화에서 프로젝트 관리에 중요한 이벤트를 식별하세요.\n"]

    if len(messages) > MAX_MESSAGES_FOR_CLASSIFIER:
        lines.append(
            f"(전체 {len(messages)}개 중 최근 {MAX_MESSAGES_FOR_CLASSIFIER}개만 표시)\n"
        )

    lines.append("---")
    for msg in truncated:
        sender = msg.get("sender", "알 수 없음")
        text = msg.get("text", "")[:MAX_CHARS_PER_MESSAGE]
        time = msg.get("time", "")
        idx = msg.get("index", 0)
        lines.append(f"[{idx}] ({time}) {sender}: {text}")

    lines.append("---")
    return "\n".join(lines)


def build_classifier_document_prompt(title: str, content: str, source_type: str) -> str:
    """Build a classifier prompt from one external document."""
    return f"""\
다음 {source_type} 문서에서 프로젝트 관리에 중요한 이벤트를 식별하세요.

제목: {title}
출처 유형: {source_type}

---
{content}
---
"""

