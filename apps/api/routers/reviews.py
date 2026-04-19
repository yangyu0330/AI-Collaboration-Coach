"""Review queue API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_db
from apps.api.schemas.review import (
    EventDetailResponse,
    EventSummaryResponse,
    PendingReviewsResponse,
    ReviewActionRequest,
    ReviewActionResponse,
)
from packages.core.services.review_service import ReviewService
from packages.core.services.state_transition import InvalidTransitionError
from packages.shared.enums import ReviewActionType

router = APIRouter(prefix="/api/v1/projects/{project_id}/reviews", tags=["reviews"])


@router.get("/pending", response_model=PendingReviewsResponse)
async def get_pending_reviews(
    project_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=100, description="반환할 최대 건수"),
    offset: int = Query(default=0, ge=0, description="오프셋"),
    db: AsyncSession = Depends(get_db),
) -> PendingReviewsResponse:
    """List events in needs_review state for one project."""
    service = ReviewService(db=db)
    events, total_count = await service.get_pending_events(
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    return PendingReviewsResponse(
        project_id=project_id,
        total_count=total_count,
        events=[EventSummaryResponse.model_validate(event) for event in events],
    )


@router.get("/{event_id}", response_model=EventDetailResponse)
async def get_event_for_review(
    project_id: uuid.UUID,
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> EventDetailResponse:
    """Get one event detail for review."""
    service = ReviewService(db=db)
    event = await service.get_event_detail(project_id=project_id, event_id=event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"이벤트를 찾을 수 없습니다: {event_id}",
        )
    return EventDetailResponse.model_validate(event)


@router.post("/{event_id}", response_model=ReviewActionResponse)
async def submit_review_action(
    project_id: uuid.UUID,
    event_id: uuid.UUID,
    body: ReviewActionRequest,
    db: AsyncSession = Depends(get_db),
) -> ReviewActionResponse:
    """Apply review action to one event."""
    service = ReviewService(db=db)
    try:
        event, review_action, previous_state = await service.process_review(
            project_id=project_id,
            event_id=event_id,
            action=body.action,
            reviewer_id=None,  # TODO: wire auth user id in later phase.
            review_note=body.review_note,
            patch=body.patch,
        )
    except ValueError as exc:
        error_msg = str(exc)
        if "찾을 수 없습니다" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg,
        ) from exc
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ReviewActionResponse(
        event_id=event.id,
        action=body.action.value,
        previous_state=previous_state,
        new_state=event.state,
        review_action_id=review_action.id,
        message=_build_message(body.action, event.state),
    )


def _build_message(action: ReviewActionType | str, new_state: str) -> str:
    """Build human-readable review result message."""
    action_value = action.value if isinstance(action, ReviewActionType) else str(action)
    messages = {
        "approve": f"이벤트가 승인되었습니다. (상태: {new_state})",
        "reject": f"이벤트가 반려되었습니다. (상태: {new_state})",
        "hold": "이벤트가 보류 처리되었습니다. 상태는 변경되지 않았습니다.",
        "edit_and_approve": f"이벤트가 수정 후 승인되었습니다. (상태: {new_state})",
    }
    return messages.get(action_value, "리뷰 처리가 완료되었습니다.")
