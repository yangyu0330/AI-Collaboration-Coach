"""Extractor prompt builders for structured event extraction."""

from __future__ import annotations

EXTRACTOR_SYSTEM_PROMPT = """\
당신은 대학생 팀 프로젝트의 이벤트를 구조화하는 전문가입니다.

## 역할
Classifier가 식별한 이벤트 후보에 대해, 관련 메시지를 분석하여 구조화된 이벤트 정보를 생성합니다.

## 추출 규칙

### 1. summary (한 줄 요약)
- 한국어로, 30자 이내로 핵심을 요약하세요.
- 예: "로그인 기능 우선순위를 높임으로 변경"

### 2. topic (관련 주제)
- 관련 기능이나 영역을 명시하세요.
- 예: "로그인", "DB 설계", "발표 준비", "UI 디자인"

### 3. details
- **before**: 이전 상태 (변경/결정 이벤트에서만, 없으면 null)
- **after**: 현재/새로운 상태 (변경/결정 이벤트에서만, 없으면 null)
- **reason**: 변경/결정의 이유 (원문에 나와 있다면 인용)
- **related_people**: 관련된 사람들의 이름/닉네임
- **source_quotes**: 근거가 되는 원문 메시지를 그대로 인용 (최대 3개)

### 4. confidence (신뢰도 0.0~1.0)
- **0.9~1.0**: 원문에서 명확하게 확인됨 ("~으로 결정했습니다")
- **0.7~0.9**: 맥락상 높은 확률로 맞음
- **0.5~0.7**: 추론이 필요하며 확실하지 않음
- **0.5 미만**: 매우 불확실하거나 추측

### 5. fact_type (사실/추론 분류)
- **confirmed_fact**: 원문에서 직접 확인할 수 있는 사실
- **inferred_interpretation**: 맥락 기반 추론
- **unresolved_ambiguity**: 아직 확정되지 않은 내용
"""


def build_extractor_user_prompt(
    event_type: str,
    brief: str,
    related_messages: list[dict],
) -> str:
    """Build an extractor prompt from classifier output and related messages."""
    lines = [
        f"이벤트 유형: {event_type}",
        f"Classifier 요약: {brief}",
        "",
        "관련 메시지:",
        "---",
    ]

    for msg in related_messages:
        sender = msg.get("sender", "알 수 없음")
        text = msg.get("text", "")
        time = msg.get("time", "")
        lines.append(f"({time}) {sender}: {text}")

    lines.append("---")
    lines.append("")
    lines.append("위 메시지를 분석하여 구조화된 이벤트 정보를 생성하세요.")
    return "\n".join(lines)


def build_extractor_document_prompt(
    event_type: str,
    brief: str,
    title: str,
    content: str,
) -> str:
    """Build an extractor prompt from a document segment."""
    return f"""\
이벤트 유형: {event_type}
Classifier 요약: {brief}

문서 제목: {title}

---
{content}
---

위 문서를 분석하여 구조화된 이벤트 정보를 생성하세요.
"""

