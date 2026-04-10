# Phase 1: DB 스키마 & ORM 모델 — 구체화된 계획서

> **상위 문서**: [implementation_plan.md](file:///c:/Users/andyw/Desktop/Like_a_Lion_myproject/implementation_plan.md)
> **기반 스키마**: [AI_협업_코치_프로젝트_상세설명서_v2.md §15](file:///c:/Users/andyw/Desktop/Like_a_Lion_myproject/AI_%ED%98%91%EC%97%85_%EC%BD%94%EC%B9%98_%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8_%EC%83%81%EC%84%B8%EC%84%A4%EB%AA%85%EC%84%9C_v2.md)
> **작성일**: 2026-04-10
> **예상 난이도**: ⭐⭐⭐
> **예상 소요 시간**: 3~4시간
> **선행 완료**: Phase 0 ✅

---

## 🎯 이 Phase의 목표

Phase 1이 끝나면 다음이 완성되어야 합니다:

1. ✅ 16개 테이블에 대한 SQLAlchemy ORM 모델이 정의됨
2. ✅ 모든 Enum 타입이 `packages/shared/enums.py`에 정의됨
3. ✅ Alembic이 설정되고, 초기 마이그레이션이 생성됨
4. ✅ `alembic upgrade head`로 Supabase에 테이블이 생성됨
5. ✅ 기본 CRUD 단위 테스트가 통과함

---

## 📐 ER 다이어그램

```mermaid
erDiagram
    projects ||--o{ channels : has
    projects ||--o{ users : has_members
    projects ||--o{ raw_messages : contains
    projects ||--o{ raw_documents : contains
    projects ||--o{ conversation_sessions : has
    projects ||--o{ extracted_events : has
    projects ||--o{ requirements_state : maintains
    projects ||--o{ decisions_state : maintains
    projects ||--o{ tasks_state : maintains
    projects ||--o{ issues_state : maintains
    projects ||--o{ feedback_state : maintains
    projects ||--o{ wiki_pages : generates

    channels ||--o{ raw_messages : receives
    channels ||--o{ conversation_sessions : groups

    users ||--o{ raw_messages : sends
    users ||--o{ raw_documents : uploads
    users ||--o{ review_actions : performs

    conversation_sessions ||--o{ raw_messages : contains

    extracted_events ||--o{ review_actions : reviewed_by
    extracted_events ||--o{ requirements_state : derives
    extracted_events ||--o{ decisions_state : derives

    projects {
        UUID id PK
        VARCHAR name
        TEXT description
        TIMESTAMP created_at
    }

    users {
        UUID id PK
        UUID project_id FK
        BIGINT telegram_id
        VARCHAR username
        VARCHAR role
    }

    channels {
        UUID id PK
        UUID project_id FK
        BIGINT telegram_chat_id
        VARCHAR channel_name
    }

    raw_messages {
        UUID id PK
        UUID project_id FK
        UUID channel_id FK
        UUID sender_id FK
        UUID session_id FK
        BIGINT telegram_message_id
        TEXT text
        TIMESTAMP sent_at
    }

    raw_documents {
        UUID id PK
        UUID project_id FK
        UUID created_by FK
        VARCHAR source_type
        VARCHAR title
        TEXT content
    }

    conversation_sessions {
        UUID id PK
        UUID project_id FK
        UUID channel_id FK
        VARCHAR session_status
        INT message_count
    }

    extracted_events {
        UUID id PK
        UUID project_id FK
        VARCHAR event_type
        VARCHAR state
        TEXT summary
        JSONB details
        FLOAT confidence
    }

    review_actions {
        UUID id PK
        UUID event_id FK
        UUID reviewer_id FK
        VARCHAR action
        TEXT review_note
    }

    requirements_state {
        UUID id PK
        UUID project_id FK
        VARCHAR item_key
        VARCHAR title
        VARCHAR status
    }

    decisions_state {
        UUID id PK
        UUID project_id FK
        VARCHAR decision_key
        VARCHAR status
    }

    tasks_state {
        UUID id PK
        UUID project_id FK
        VARCHAR task_key
        VARCHAR status
    }

    issues_state {
        UUID id PK
        UUID project_id FK
        VARCHAR issue_key
        VARCHAR status
    }

    feedback_state {
        UUID id PK
        UUID project_id FK
        VARCHAR feedback_key
        VARCHAR reflection_status
    }

    wiki_pages {
        UUID id PK
        UUID project_id FK
        VARCHAR slug
        TEXT content_md
    }

    wiki_revisions {
        UUID id PK
        UUID wiki_page_id FK
        TEXT content_md
        INT revision_number
    }

    interventions {
        UUID id PK
        UUID project_id FK
        VARCHAR intervention_type
        TEXT message
    }
```

---

## 📋 작업 목록 (총 9단계)

---

### Step 1-1. Enum 보완 (`packages/shared/enums.py`)

현재 Phase 0에서 `EventType`, `EventState`, `ReviewActionType` 3개가 정의되어 있습니다.
나머지 필요한 Enum을 추가합니다.

```python
"""Core enum types used across the project."""

from enum import StrEnum


# --- 기존 (Phase 0에서 생성됨) ---

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


# --- 추가 (Phase 1에서 신규) ---

class SourceType(StrEnum):
    """외부 문서 출처 유형"""
    MEETING = "meeting"
    PROFESSOR_FEEDBACK = "professor_feedback"
    MANUAL_NOTE = "manual_note"


class SessionStatus(StrEnum):
    """대화 세션 상태"""
    OPEN = "open"
    CLOSED = "closed"
    ANALYZED = "analyzed"


class SessionTriggerType(StrEnum):
    """세션 종료 트리거 유형"""
    IDLE_TIMEOUT = "idle_timeout"
    MANUAL = "manual"
    PRIORITY = "priority"


class VisibilityStatus(StrEnum):
    """메시지 가시성 상태 (삭제 관리)"""
    VISIBLE = "visible"
    UNKNOWN = "unknown"
    SOFT_DELETED = "soft_deleted"


class SourceKind(StrEnum):
    """이벤트 원본 종류"""
    MESSAGE = "message"
    DOCUMENT = "document"
    SESSION = "session"


class CanonicalStatus(StrEnum):
    """정본 상태 테이블의 공통 상태"""
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    REMOVED = "removed"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


class Priority(StrEnum):
    """우선순위"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class UserRole(StrEnum):
    """팀원 역할"""
    LEADER = "leader"       # 팀장 (검토 권한)
    MEMBER = "member"       # 일반 팀원
    OBSERVER = "observer"   # 관찰자


class InterventionType(StrEnum):
    """개입/알림 유형 (§20.1)"""
    REVIEW_REQUEST = "review_request"
    DAILY_SUMMARY = "daily_summary"
    REMINDER = "reminder"


class FeedbackReflectionStatus(StrEnum):
    """교수 피드백 반영 상태"""
    PENDING = "pending"
    REFLECTED = "reflected"
    NOT_APPLICABLE = "not_applicable"
    DEFERRED = "deferred"
```

---

### Step 1-2. Raw Source Layer — `Project` 모델

#### `packages/db/models/project.py`

```python
"""Project model — 프로젝트 기본 정보."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, UUIDMixin, TimestampMixin


class Project(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default=None)

    # Relationships (lazy 로딩, 필요 시 selectinload로 즉시 로딩)
    channels = relationship("Channel", back_populates="project", lazy="selectin")
    members = relationship("User", back_populates="project", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}')>"
```

---

### Step 1-3. Raw Source Layer — `User`, `Channel` 모델

#### `packages/db/models/user.py`

```python
"""User model — 사용자/팀원 정보."""

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    project_id: Mapped["uuid.UUID"] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, default=None)
    username: Mapped[str | None] = mapped_column(String(100), default=None)
    first_name: Mapped[str | None] = mapped_column(String(100), default=None)
    last_name: Mapped[str | None] = mapped_column(String(100), default=None)
    role: Mapped[str] = mapped_column(
        String(20), default="member"  # UserRole enum 값
    )

    # Relationships
    project = relationship("Project", back_populates="members")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
```

> [!NOTE]
> `import uuid`는 타입 힌트에서만 사용하므로 `from __future__ import annotations`로 처리하거나
> 문자열 어노테이션 `"uuid.UUID"`를 사용합니다.

#### `packages/db/models/channel.py`

```python
"""Channel model — 데이터 출처 채널 (텔레그램 그룹)."""

import uuid
from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, UUIDMixin, TimestampMixin


class Channel(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "channels"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, default=None)
    channel_name: Mapped[str] = mapped_column(String(200), nullable=False)
    channel_type: Mapped[str] = mapped_column(
        String(20), default="telegram"  # 확장 가능: slack, discord 등
    )

    # Relationships
    project = relationship("Project", back_populates="channels")

    def __repr__(self) -> str:
        return f"<Channel(id={self.id}, name='{self.channel_name}')>"
```

---

### Step 1-4. Raw Source Layer — `RawMessage`, `RawDocument` 모델

#### `packages/db/models/raw_message.py`

```python
"""RawMessage model — 텔레그램 원문 메시지 (§15.3 raw_messages)."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, UUIDMixin, TimestampMixin


class RawMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "raw_messages"

    # 소속 정보
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )
    sender_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversation_sessions.id", ondelete="SET NULL"), default=None
    )

    # 텔레그램 원본 정보
    telegram_message_id: Mapped[int | None] = mapped_column(BigInteger, default=None)
    text: Mapped[str | None] = mapped_column(Text, default=None)
    message_type: Mapped[str] = mapped_column(
        String(20), default="text"  # text, photo, document, sticker 등
    )

    # 답장 관계
    reply_to_message_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("raw_messages.id", ondelete="SET NULL"), default=None
    )

    # 시간
    sent_at: Mapped[datetime] = mapped_column(nullable=False)
    edited_at: Mapped[datetime | None] = mapped_column(default=None)

    # 삭제 관리 (Bot API 한계 → visibility로 관리)
    visibility_status: Mapped[str] = mapped_column(
        String(20), default="visible"  # VisibilityStatus enum
    )

    # 추가 메타데이터 (파일 정보, 미디어 등)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, default=None)

    # 우선 처리 대상 표시 (Phase 4에서 사용)
    is_priority: Mapped[bool] = mapped_column(default=False)

    # Relationships
    project = relationship("Project")
    channel = relationship("Channel")
    sender = relationship("User")
    session = relationship("ConversationSession", back_populates="messages")
    reply_to = relationship("RawMessage", remote_side="RawMessage.id")

    def __repr__(self) -> str:
        preview = (self.text or "")[:30]
        return f"<RawMessage(id={self.id}, preview='{preview}...')>"
```

> [!IMPORTANT]
> `metadata`는 Python/SQLAlchemy 예약어와 충돌할 수 있으므로
> Python 속성명은 `metadata_`, DB 컬럼명은 `metadata`로 매핑합니다.

#### `packages/db/models/raw_document.py`

```python
"""RawDocument model — 회의록/교수 피드백 원문 (§15.3 raw_documents)."""

import uuid
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, UUIDMixin, TimestampMixin


class RawDocument(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "raw_documents"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(
        String(30), nullable=False  # SourceType enum
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 업로드 사용자
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )

    # Relationships
    project = relationship("Project")
    uploader = relationship("User")

    def __repr__(self) -> str:
        return f"<RawDocument(id={self.id}, title='{self.title}')>"
```

---

### Step 1-5. Event Proposal Layer — `ConversationSession`, `ExtractedEvent` 모델

#### `packages/db/models/conversation_session.py`

```python
"""ConversationSession model — 대화 세션 (§15.3 conversation_sessions)."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, UUIDMixin, TimestampMixin


class ConversationSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "conversation_sessions"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )

    # 세션 시간 범위
    start_at: Mapped[datetime] = mapped_column(nullable=False)
    end_at: Mapped[datetime | None] = mapped_column(default=None)

    # 세션 통계
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    # 상태
    session_status: Mapped[str] = mapped_column(
        String(20), default="open"  # SessionStatus enum
    )
    trigger_type: Mapped[str | None] = mapped_column(
        String(20), default=None  # SessionTriggerType enum
    )

    # Relationships
    project = relationship("Project")
    channel = relationship("Channel")
    messages = relationship("RawMessage", back_populates="session", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ConversationSession(id={self.id}, status='{self.session_status}', msgs={self.message_count})>"
```

#### `packages/db/models/extracted_event.py`

```python
"""ExtractedEvent model — AI 추출 이벤트 후보 (§15.3 extracted_events)."""

import uuid
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, UUIDMixin, TimestampMixin


class ExtractedEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "extracted_events"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    # 원본 출처 (message / document / session)
    source_kind: Mapped[str] = mapped_column(String(20), nullable=False)  # SourceKind enum
    source_id: Mapped[uuid.UUID] = mapped_column(nullable=False)          # 원본의 ID (다형 FK)

    # 이벤트 핵심 정보
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)   # EventType enum
    state: Mapped[str] = mapped_column(
        String(20), default="extracted"  # EventState enum
    )
    topic: Mapped[str | None] = mapped_column(String(200), default=None)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    # 구조화 상세 정보 (§15.3 details JSONB)
    # {
    #   "before": "변경 전",
    #   "after": "변경 후",
    #   "reason": "변경 이유",
    #   "related_people": ["관련 인물"],
    #   "source_quotes": ["근거 원문"]
    # }
    details: Mapped[dict | None] = mapped_column(JSONB, default=None)

    # AI 신뢰도 (0.0 ~ 1.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # 사실/추론 분리 (§19.3)
    fact_type: Mapped[str | None] = mapped_column(
        String(30), default=None
        # "confirmed_fact" | "inferred_interpretation" | "unresolved_ambiguity"
    )

    # Relationships
    project = relationship("Project")
    review_actions = relationship("ReviewAction", back_populates="event", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ExtractedEvent(id={self.id}, type='{self.event_type}', state='{self.state}', conf={self.confidence})>"
```

> [!NOTE]
> `source_id`는 다형 FK(Polymorphic FK)입니다.
> `source_kind`가 `message`이면 `raw_messages.id`, `document`이면 `raw_documents.id`,
> `session`이면 `conversation_sessions.id`를 가리킵니다.
> DB 레벨 FK 제약조건 대신 애플리케이션 레벨에서 관리합니다.

---

### Step 1-6. Review / Audit Layer — `ReviewAction` 모델

#### `packages/db/models/review_action.py`

```python
"""ReviewAction model — 승인/반려 이력 (§15.3 review_actions)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, UUIDMixin


class ReviewAction(Base, UUIDMixin):
    __tablename__ = "review_actions"

    # 대상 이벤트
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("extracted_events.id", ondelete="CASCADE"), nullable=False
    )

    # 검토자 (팀장)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )

    # 액션
    action: Mapped[str] = mapped_column(String(30), nullable=False)  # ReviewActionType enum

    # 검토 의견
    review_note: Mapped[str | None] = mapped_column(Text, default=None)

    # 수정 내용 (edit_and_approve 시)
    patch: Mapped[dict | None] = mapped_column(JSONB, default=None)

    # 검토 시각
    reviewed_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    event = relationship("ExtractedEvent", back_populates="review_actions")
    reviewer = relationship("User")

    def __repr__(self) -> str:
        return f"<ReviewAction(id={self.id}, action='{self.action}', event={self.event_id})>"
```

---

### Step 1-7. Canonical State Layer — 5개 정본 테이블

이 5개 모델은 구조가 유사합니다. 공통 패턴:
- `project_id` FK
- `item_key` / `decision_key` 등 고유 식별자
- `status` 상태 필드
- `source_event_id` 근거 이벤트
- `approved_by`, `approved_at` 승인 정보
- `superseded_by` 대체 관계

#### `packages/db/models/requirement_state.py`

```python
"""RequirementState model — 현재 요구사항 정본 (§15.3 requirements_state)."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, UUIDMixin, TimestampMixin


class RequirementState(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "requirements_state"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    item_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    current_value: Mapped[str | None] = mapped_column(Text, default=None)
    priority: Mapped[str] = mapped_column(String(10), default="medium")  # Priority enum
    status: Mapped[str] = mapped_column(String(20), default="active")    # CanonicalStatus enum

    # 근거 & 승인
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("extracted_events.id", ondelete="SET NULL"), default=None
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    approved_at: Mapped[datetime | None] = mapped_column(default=None)
    applied_at: Mapped[datetime | None] = mapped_column(default=None)
    superseded_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("requirements_state.id", ondelete="SET NULL"), default=None
    )

    # Relationships
    project = relationship("Project")
    source_event = relationship("ExtractedEvent")
    approver = relationship("User")

    def __repr__(self) -> str:
        return f"<RequirementState(key='{self.item_key}', status='{self.status}')>"
```

#### `packages/db/models/decision_state.py`

```python
"""DecisionState model — 현재 유효한 결정사항 정본 (§15.3 decisions_state)."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, UUIDMixin, TimestampMixin


class DecisionState(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "decisions_state"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    decision_key: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(200), default=None)
    decision_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active/superseded/withdrawn

    # 근거 & 승인
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("extracted_events.id", ondelete="SET NULL"), default=None
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    approved_at: Mapped[datetime | None] = mapped_column(default=None)
    applied_at: Mapped[datetime | None] = mapped_column(default=None)
    superseded_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("decisions_state.id", ondelete="SET NULL"), default=None
    )

    # Relationships
    project = relationship("Project")
    source_event = relationship("ExtractedEvent")
    approver = relationship("User")

    def __repr__(self) -> str:
        return f"<DecisionState(key='{self.decision_key}', status='{self.status}')>"
```

#### `packages/db/models/task_state.py`

```python
"""TaskState model — 현재 작업 상태 정본."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, UUIDMixin, TimestampMixin


class TaskState(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tasks_state"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    task_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    priority: Mapped[str] = mapped_column(String(10), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="active")  # active/completed/on_hold/removed

    # 근거 & 승인
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("extracted_events.id", ondelete="SET NULL"), default=None
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    approved_at: Mapped[datetime | None] = mapped_column(default=None)
    applied_at: Mapped[datetime | None] = mapped_column(default=None)

    # Relationships
    project = relationship("Project")
    source_event = relationship("ExtractedEvent")
    assignee = relationship("User", foreign_keys=[assignee_id])
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self) -> str:
        return f"<TaskState(key='{self.task_key}', status='{self.status}')>"
```

#### `packages/db/models/issue_state.py`

```python
"""IssueState model — 현재 이슈 상태 정본."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, UUIDMixin, TimestampMixin


class IssueState(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "issues_state"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    issue_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    severity: Mapped[str] = mapped_column(String(10), default="medium")  # high/medium/low
    status: Mapped[str] = mapped_column(String(20), default="active")    # active/resolved/on_hold/removed

    # 근거 & 승인
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("extracted_events.id", ondelete="SET NULL"), default=None
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    approved_at: Mapped[datetime | None] = mapped_column(default=None)
    applied_at: Mapped[datetime | None] = mapped_column(default=None)
    resolved_at: Mapped[datetime | None] = mapped_column(default=None)

    # Relationships
    project = relationship("Project")
    source_event = relationship("ExtractedEvent")
    approver = relationship("User")

    def __repr__(self) -> str:
        return f"<IssueState(key='{self.issue_key}', status='{self.status}')>"
```

#### `packages/db/models/feedback_state.py`

```python
"""FeedbackState model — 교수 피드백 정본/반영 상태."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, UUIDMixin, TimestampMixin


class FeedbackState(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "feedback_state"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    feedback_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, default=None)
    reflection_status: Mapped[str] = mapped_column(
        String(20), default="pending"  # FeedbackReflectionStatus enum
    )
    action_taken: Mapped[str | None] = mapped_column(Text, default=None)  # 반영 시 취한 조치

    # 근거 & 승인
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("extracted_events.id", ondelete="SET NULL"), default=None
    )
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("raw_documents.id", ondelete="SET NULL"), default=None
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    approved_at: Mapped[datetime | None] = mapped_column(default=None)
    applied_at: Mapped[datetime | None] = mapped_column(default=None)

    # Relationships
    project = relationship("Project")
    source_event = relationship("ExtractedEvent")
    source_document = relationship("RawDocument")
    approver = relationship("User")

    def __repr__(self) -> str:
        return f"<FeedbackState(key='{self.feedback_key}', reflection='{self.reflection_status}')>"
```

---

### Step 1-8. Presentation & Intervention Layer

#### `packages/db/models/wiki_page.py`

```python
"""WikiPage model — 자동 생성 위키 문서 (§15.3 wiki_pages)."""

import uuid
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, UUIDMixin, TimestampMixin


class WikiPage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "wiki_pages"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content_md: Mapped[str | None] = mapped_column(Text, default=None)
    derived_from: Mapped[dict | None] = mapped_column(JSONB, default=None)

    # Relationships
    project = relationship("Project")
    revisions = relationship("WikiRevision", back_populates="wiki_page", lazy="selectin")

    def __repr__(self) -> str:
        return f"<WikiPage(slug='{self.slug}', title='{self.title}')>"
```

#### `packages/db/models/wiki_revision.py`

```python
"""WikiRevision model — 위키 변경 이력."""

import uuid
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, UUIDMixin, TimestampMixin


class WikiRevision(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "wiki_revisions"

    wiki_page_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("wiki_pages.id", ondelete="CASCADE"), nullable=False
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content_md: Mapped[str | None] = mapped_column(Text, default=None)
    change_summary: Mapped[str | None] = mapped_column(Text, default=None)

    # Relationships
    wiki_page = relationship("WikiPage", back_populates="revisions")

    def __repr__(self) -> str:
        return f"<WikiRevision(page={self.wiki_page_id}, rev={self.revision_number})>"
```

#### `packages/db/models/intervention.py`

```python
"""Intervention model — 알림/개입 내역 (§20.1)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base, UUIDMixin


class Intervention(Base, UUIDMixin):
    __tablename__ = "interventions"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    intervention_type: Mapped[str] = mapped_column(
        String(30), nullable=False  # InterventionType enum
    )
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    target_chat_id: Mapped[int | None] = mapped_column(BigInteger, default=None)

    message: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    delivered: Mapped[bool] = mapped_column(default=False)

    # 관련 이벤트 (선택적)
    related_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("extracted_events.id", ondelete="SET NULL"), default=None
    )

    # Relationships
    project = relationship("Project")
    target_user = relationship("User")
    related_event = relationship("ExtractedEvent")

    def __repr__(self) -> str:
        return f"<Intervention(type='{self.intervention_type}', delivered={self.delivered})>"
```

---

### Step 1-9. 모델 등록 & Alembic 설정

#### `packages/db/models/__init__.py` — 모든 모델 import

```python
"""
전체 ORM 모델 등록.
Alembic이 모든 모델을 인식하려면 여기서 import해야 합니다.
"""

from packages.db.base import Base

# Raw Source Layer
from packages.db.models.project import Project
from packages.db.models.user import User
from packages.db.models.channel import Channel
from packages.db.models.raw_message import RawMessage
from packages.db.models.raw_document import RawDocument

# Event Proposal Layer
from packages.db.models.conversation_session import ConversationSession
from packages.db.models.extracted_event import ExtractedEvent

# Review / Audit Layer
from packages.db.models.review_action import ReviewAction

# Canonical State Layer
from packages.db.models.requirement_state import RequirementState
from packages.db.models.decision_state import DecisionState
from packages.db.models.task_state import TaskState
from packages.db.models.issue_state import IssueState
from packages.db.models.feedback_state import FeedbackState

# Presentation Layer
from packages.db.models.wiki_page import WikiPage
from packages.db.models.wiki_revision import WikiRevision

# Intervention Layer
from packages.db.models.intervention import Intervention

__all__ = [
    "Base",
    "Project", "User", "Channel", "RawMessage", "RawDocument",
    "ConversationSession", "ExtractedEvent",
    "ReviewAction",
    "RequirementState", "DecisionState", "TaskState", "IssueState", "FeedbackState",
    "WikiPage", "WikiRevision",
    "Intervention",
]
```

#### Alembic 초기 설정

```bash
# 프로젝트 루트에서 실행
cd c:\Users\andyw\Desktop\Like_a_Lion_myproject
alembic init alembic
```

#### `alembic.ini` 수정 (핵심 변경 사항)

```ini
# sqlalchemy.url은 alembic/env.py에서 동적으로 설정하므로 주석 처리
# sqlalchemy.url = driver://user:pass@localhost/dbname
```

#### `alembic/env.py` 수정 (핵심 부분만)

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# Settings에서 DB URL 가져오기
from apps.api.config import settings

# 모든 모델 import (메타데이터 등록)
from packages.db.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """오프라인 모드 (SQL 생성만)"""
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """온라인 모드 (async 엔진 사용)"""
    connectable = create_async_engine(settings.database_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

#### 초기 마이그레이션 실행

```bash
# 마이그레이션 파일 생성
alembic revision --autogenerate -m "initial_schema"

# Supabase에 테이블 생성
alembic upgrade head
```

---

## ✅ 검증 체크리스트

### 1단계: 모델 import 확인
```bash
python -c "from packages.db.models import *; print(f'✅ {len(__all__)}개 모델 로드 성공')"
```
→ `✅ 17개 모델 로드 성공` (Base 포함)

### 2단계: Alembic 마이그레이션
```bash
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
```
→ 16개 테이블이 Supabase에 생성됨

### 3단계: Supabase 대시보드에서 확인
Supabase 대시보드 → Table Editor에서 16개 테이블 확인:
- `projects`, `users`, `channels`
- `raw_messages`, `raw_documents`
- `conversation_sessions`, `extracted_events`
- `review_actions`
- `requirements_state`, `decisions_state`, `tasks_state`, `issues_state`, `feedback_state`
- `wiki_pages`, `wiki_revisions`
- `interventions`

### 4단계: 기본 CRUD 테스트
```bash
pytest tests/unit/test_models.py -v
```

#### `tests/unit/test_models.py` (테스트 코드)

```python
"""Phase 1: ORM 모델 기본 CRUD 테스트."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from apps.api.config import settings
from packages.db.models import Base, Project, User


@pytest.fixture
async def db_session():
    """테스트용 DB 세션 (실제 Supabase 연결)"""
    engine = create_async_engine(settings.database_url, echo=True)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_project(db_session: AsyncSession):
    """프로젝트 생성 테스트"""
    project = Project(name="테스트 프로젝트", description="Phase 1 테스트")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    assert project.id is not None
    assert project.name == "테스트 프로젝트"
    assert project.created_at is not None

    # 정리
    await db_session.delete(project)
    await db_session.commit()


@pytest.mark.asyncio
async def test_create_user_with_project(db_session: AsyncSession):
    """프로젝트에 속한 유저 생성 테스트"""
    project = Project(name="유저 테스트 프로젝트")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    user = User(
        project_id=project.id,
        telegram_id=123456789,
        username="testuser",
        first_name="테스트",
        role="leader",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.project_id == project.id
    assert user.role == "leader"

    # 정리
    await db_session.delete(user)
    await db_session.delete(project)
    await db_session.commit()
```

---

## 📄 이 Phase의 최종 산출물 목록

| # | 파일 | 설명 |
|:---:|------|------|
| 1 | `packages/shared/enums.py` | 전체 Enum 정의 (12개 Enum) |
| 2 | `packages/db/models/project.py` | Project 모델 |
| 3 | `packages/db/models/user.py` | User 모델 |
| 4 | `packages/db/models/channel.py` | Channel 모델 |
| 5 | `packages/db/models/raw_message.py` | RawMessage 모델 |
| 6 | `packages/db/models/raw_document.py` | RawDocument 모델 |
| 7 | `packages/db/models/conversation_session.py` | ConversationSession 모델 |
| 8 | `packages/db/models/extracted_event.py` | ExtractedEvent 모델 |
| 9 | `packages/db/models/review_action.py` | ReviewAction 모델 |
| 10 | `packages/db/models/requirement_state.py` | RequirementState 모델 |
| 11 | `packages/db/models/decision_state.py` | DecisionState 모델 |
| 12 | `packages/db/models/task_state.py` | TaskState 모델 |
| 13 | `packages/db/models/issue_state.py` | IssueState 모델 |
| 14 | `packages/db/models/feedback_state.py` | FeedbackState 모델 |
| 15 | `packages/db/models/wiki_page.py` | WikiPage 모델 |
| 16 | `packages/db/models/wiki_revision.py` | WikiRevision 모델 |
| 17 | `packages/db/models/intervention.py` | Intervention 모델 |
| 18 | `packages/db/models/__init__.py` | 전체 모델 등록 |
| 19 | `alembic/env.py` | Alembic async 설정 |
| 20 | `alembic/versions/xxxx_initial_schema.py` | 초기 마이그레이션 |
| 21 | `tests/unit/test_models.py` | 기본 CRUD 테스트 |

**총 21개 파일** (신규 16개 + 수정 5개)

---

## ⏭️ 다음 Phase 연결

Phase 1 완료 후 **Phase 2 (텔레그램 봇 & 메시지 수집)** 과 **Phase 3 (외부 텍스트 입력)** 을 병렬로 진행할 수 있습니다.
두 Phase 모두 Phase 1의 DB 모델에만 의존합니다.
