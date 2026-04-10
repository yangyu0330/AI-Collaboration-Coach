"""Document API endpoints for external text ingestion."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_db
from apps.api.schemas.document import (
    DocumentCreate,
    DocumentListItem,
    DocumentListResponse,
    DocumentResponse,
)
from packages.core.services.document_service import (
    DocumentNotFoundError,
    DocumentService,
    ProjectNotFoundError,
)
from packages.shared.enums import SourceType

router = APIRouter(prefix="/api/v1", tags=["documents"])


@router.post(
    "/sources/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    data: DocumentCreate,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Upload one external text document."""
    service = DocumentService(db)
    try:
        doc = await service.create_document(data)
        return DocumentResponse.model_validate(doc)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/projects/{project_id}/documents", response_model=DocumentListResponse)
async def list_documents(
    project_id: uuid.UUID,
    source_type: SourceType | None = Query(
        default=None,
        description="Filter by source type: meeting, professor_feedback, manual_note",
    ),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """List documents for one project."""
    service = DocumentService(db)
    try:
        documents, total = await service.list_documents(
            project_id=project_id,
            source_type=source_type,
            offset=offset,
            limit=limit,
        )
        return DocumentListResponse(
            documents=[DocumentListItem.model_validate(doc) for doc in documents],
            total=total,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/sources/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Fetch one document with full content."""
    service = DocumentService(db)
    try:
        doc = await service.get_document(document_id)
        return DocumentResponse.model_validate(doc)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
