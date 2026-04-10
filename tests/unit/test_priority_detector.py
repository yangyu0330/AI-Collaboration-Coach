"""Phase 4 priority detector tests."""

from packages.core.services.priority_detector import PriorityDetector


def test_detects_priority_keyword_in_korean_text() -> None:
    detector = PriorityDetector()
    result = detector.check("교수님이 마감 일정을 앞당기라고 하셨어요.")

    assert result.is_priority is True
    assert "교수님" in result.matched_keywords
    assert result.matched_command is None


def test_detects_priority_slash_command() -> None:
    detector = PriorityDetector()
    result = detector.check("/decision 로그인 방식을 OAuth로 확정")

    assert result.is_priority is True
    assert result.matched_command == "/decision"


def test_non_priority_text_returns_false() -> None:
    detector = PriorityDetector()
    result = detector.check("오늘 점심 뭐 먹을지 정하자.")

    assert result.is_priority is False
    assert result.matched_keywords == []
    assert result.matched_command is None
