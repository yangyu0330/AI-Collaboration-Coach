"""Core enum types used across the project."""

from enum import StrEnum


class EventType(StrEnum):
    DECISION = "decision"
    REQUIREMENT_CHANGE = "requirement_change"
    TASK = "task"
    ISSUE = "issue"
    FEEDBACK = "feedback"
    QUESTION = "question"


class EventState(StrEnum):
    OBSERVED = "observed"
    EXTRACTED = "extracted"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    SUPERSEDED = "superseded"


class ReviewActionType(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    HOLD = "hold"
    EDIT_AND_APPROVE = "edit_and_approve"


class SourceType(StrEnum):
    MEETING = "meeting"
    PROFESSOR_FEEDBACK = "professor_feedback"
    MANUAL_NOTE = "manual_note"


class SessionStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    ANALYZED = "analyzed"


class SessionTriggerType(StrEnum):
    IDLE_TIMEOUT = "idle_timeout"
    MANUAL = "manual"
    PRIORITY = "priority"


class VisibilityStatus(StrEnum):
    VISIBLE = "visible"
    UNKNOWN = "unknown"
    SOFT_DELETED = "soft_deleted"


class SourceKind(StrEnum):
    MESSAGE = "message"
    DOCUMENT = "document"
    SESSION = "session"


class CanonicalStatus(StrEnum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    REMOVED = "removed"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


class Priority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class UserRole(StrEnum):
    LEADER = "leader"
    MEMBER = "member"
    OBSERVER = "observer"


class InterventionType(StrEnum):
    REVIEW_REQUEST = "review_request"
    DAILY_SUMMARY = "daily_summary"
    REMINDER = "reminder"


class FeedbackReflectionStatus(StrEnum):
    PENDING = "pending"
    REFLECTED = "reflected"
    NOT_APPLICABLE = "not_applicable"
    DEFERRED = "deferred"
