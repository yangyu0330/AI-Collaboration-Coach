"""Business logic for review queue and review actions."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.services.state_transition import (
    InvalidTransitionError,
    get_target_state,
    validate_transition,
)
from packages.db.models.extracted_event import ExtractedEvent
from packages.db.models.review_action import ReviewAction
from packages.shared.enums import EventState, ReviewActionType

logger = structlog.get_logger()


class ReviewService:
    """Service for fetching pending events and processing review actions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_pending_events(
        self,
        project_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ExtractedEvent], int]:
        """Return pending review events with total count."""
        count_stmt = (
            select(func.count(ExtractedEvent.id))
            .where(ExtractedEvent.project_id == project_id)
            .where(ExtractedEvent.state == EventState.NEEDS_REVIEW.value)
        )
        total_result = await self.db.execute(count_stmt)
        total_count = int(total_result.scalar() or 0)

        stmt = (
            select(ExtractedEvent)
            .where(ExtractedEvent.project_id == project_id)
            .where(ExtractedEvent.state == EventState.NEEDS_REVIEW.value)
            .order_by(ExtractedEvent.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        events = list(result.scalars().all())

        logger.info(
            "pending_events_fetched",
            project_id=str(project_id),
            count=len(events),
            total=total_count,
        )
        return events, total_count

    async def get_event_detail(
        self,
        project_id: uuid.UUID,
        event_id: uuid.UUID,
        *,
        for_update: bool = False,
    ) -> ExtractedEvent | None:
        """Return one event if it belongs to the given project."""
        stmt = (
            select(ExtractedEvent)
            .where(ExtractedEvent.id == event_id)
            .where(ExtractedEvent.project_id == project_id)
        )
        if for_update:
            stmt = stmt.with_for_update()

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def process_review(
        self,
        project_id: uuid.UUID,
        event_id: uuid.UUID,
        action: ReviewActionType,
        reviewer_id: uuid.UUID | None = None,
        review_note: str | None = None,
        patch: dict[str, Any] | None = None,
    ) -> tuple[ExtractedEvent, ReviewAction, str]:
        """
        Process one review action and persist audit log.

        Returns:
            (updated_event, created_review_action, previous_state)
        """
        event = await self.get_event_detail(project_id, event_id, for_update=True)
        if event is None:
            raise ValueError(f"이벤트를 찾을 수 없습니다: project={project_id}, event={event_id}")

        previous_state = event.state
        target_state = get_target_state(action)

        if target_state is None:
            if event.state != EventState.NEEDS_REVIEW.value:
                raise InvalidTransitionError(event.state, "hold (상태 유지)")

            review_action = ReviewAction(
                event_id=event_id,
                reviewer_id=reviewer_id,
                action=action.value,
                review_note=review_note,
                patch=patch,
            )
            self.db.add(review_action)
            await self.db.commit()
            await self.db.refresh(review_action)
            logger.info(
                "review_hold",
                event_id=str(event_id),
                reviewer_id=str(reviewer_id) if reviewer_id else None,
            )
            return event, review_action, previous_state

        validate_transition(event.state, target_state.value)

        if action == ReviewActionType.EDIT_AND_APPROVE and patch:
            self._apply_patch(event, patch)

        event.state = target_state.value

        review_action = ReviewAction(
            event_id=event_id,
            reviewer_id=reviewer_id,
            action=action.value,
            review_note=review_note,
            patch=patch,
        )
        self.db.add(review_action)
        await self.db.commit()
        await self.db.refresh(event)
        await self.db.refresh(review_action)

        logger.info(
            "review_processed",
            event_id=str(event_id),
            action=action.value,
            previous_state=previous_state,
            new_state=event.state,
        )
        return event, review_action, previous_state

    async def get_review_history(self, event_id: uuid.UUID) -> list[ReviewAction]:
        """Return audit history for one event in chronological order."""
        stmt = (
            select(ReviewAction)
            .where(ReviewAction.event_id == event_id)
            .order_by(ReviewAction.reviewed_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def _apply_patch(event: ExtractedEvent, patch: dict[str, Any]) -> None:
        """Apply validated patch fields to an event."""
        from apps.api.schemas.review import PatchData

        try:
            validated = PatchData.model_validate(patch)
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc

        for key, value in validated.model_dump(exclude_unset=True).items():
            setattr(event, key, value)
            logger.debug("patch_applied_field", field=key)
