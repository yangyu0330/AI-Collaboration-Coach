"""Unit tests for event state transition rules."""

from __future__ import annotations

import pytest

from packages.core.services.state_transition import (
    InvalidTransitionError,
    get_target_state,
    validate_transition,
)
from packages.shared.enums import EventState, ReviewActionType


def test_validate_transition_allows_review_happy_path() -> None:
    validate_transition(EventState.NEEDS_REVIEW.value, EventState.APPROVED.value)
    validate_transition(EventState.NEEDS_REVIEW.value, EventState.REJECTED.value)
    validate_transition(EventState.APPROVED.value, EventState.APPLIED.value)
    validate_transition(EventState.APPLIED.value, EventState.SUPERSEDED.value)


def test_validate_transition_blocks_invalid_path() -> None:
    with pytest.raises(InvalidTransitionError, match="상태 전이 불가"):
        validate_transition(EventState.REJECTED.value, EventState.APPROVED.value)

    with pytest.raises(InvalidTransitionError, match="상태 전이 불가"):
        validate_transition(EventState.APPLIED.value, EventState.REJECTED.value)


def test_validate_transition_blocks_unknown_states() -> None:
    with pytest.raises(InvalidTransitionError):
        validate_transition("unknown_state", EventState.APPROVED.value)


def test_get_target_state_mapping() -> None:
    assert get_target_state(ReviewActionType.APPROVE) == EventState.APPROVED
    assert get_target_state(ReviewActionType.REJECT) == EventState.REJECTED
    assert get_target_state(ReviewActionType.EDIT_AND_APPROVE) == EventState.APPROVED
    assert get_target_state(ReviewActionType.HOLD) is None
