"""Event state transition rules used by review workflow."""

from __future__ import annotations

from packages.shared.enums import EventState, ReviewActionType

ALLOWED_TRANSITIONS: dict[EventState, set[EventState]] = {
    EventState.OBSERVED: {EventState.EXTRACTED},
    EventState.EXTRACTED: {EventState.NEEDS_REVIEW},
    EventState.NEEDS_REVIEW: {EventState.APPROVED, EventState.REJECTED},
    EventState.APPROVED: {EventState.APPLIED},
    EventState.APPLIED: {EventState.SUPERSEDED},
}

ACTION_TO_STATE: dict[ReviewActionType, EventState] = {
    ReviewActionType.APPROVE: EventState.APPROVED,
    ReviewActionType.REJECT: EventState.REJECTED,
    ReviewActionType.EDIT_AND_APPROVE: EventState.APPROVED,
}


class InvalidTransitionError(Exception):
    """Raised when event state transition is not allowed."""

    def __init__(self, current: str, target: str):
        self.current = current
        self.target = target
        try:
            allowed_states = ALLOWED_TRANSITIONS.get(EventState(current), set())
            allowed = sorted(state.value for state in allowed_states)
        except ValueError:
            allowed = []

        super().__init__(f"상태 전이 불가: {current!r} -> {target!r}. 허용 전이: {allowed}")


def validate_transition(current_state: str, target_state: str) -> None:
    """Validate event state transition."""
    try:
        current = EventState(current_state)
        target = EventState(target_state)
    except ValueError as exc:
        raise InvalidTransitionError(current_state, target_state) from exc

    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidTransitionError(current_state, target_state)


def get_target_state(action: ReviewActionType) -> EventState | None:
    """Resolve target state from a review action."""
    return ACTION_TO_STATE.get(action)
