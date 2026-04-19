"""Document service for external text ingestion."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.schemas.document import DocumentCreate
from packages.db.models.project import Project
from packages.db.models.raw_document import RawDocument
from packages.shared.enums import SourceType

logger = structlog.get_logger()


class DocumentNotFoundError(Exception):
    """Raised when a document does not exist."""


class ProjectNotFoundError(Exception):
    """Raised when a project does not exist."""


class DocumentService:
    """Manage immutable raw documents (meeting notes, feedback, manual notes)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_document(self, data: DocumentCreate) -> RawDocument:
        """Create one raw document after project existence check."""
        project = await self.db.get(Project, data.project_id)
        if project is None:
            msg = f"Project not found: {data.project_id}"
            raise ProjectNotFoundError(msg)

        doc = RawDocument(
            project_id=data.project_id,
            source_type=data.source_type.value,
            title=data.title,
            content=data.content,
            created_by=data.created_by,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        try:
            from apps.worker.tasks.analysis_tasks import analyze_document_task

            analyze_document_task.delay(str(doc.id))
            logger.info("document_analysis_queued", document_id=str(doc.id))
        except Exception as exc:
            logger.error(
                "document_analysis_queue_failed",
                document_id=str(doc.id),
                error=str(exc),
            )

        logger.info(
            "document_created",
            document_id=str(doc.id),
            project_id=str(doc.project_id),
            source_type=doc.source_type,
            title=doc.title,
        )
        return doc

    async def get_document(self, document_id: uuid.UUID) -> RawDocument:
        """Fetch one document by id."""
        doc = await self.db.get(RawDocument, document_id)
        if doc is None:
            msg = f"Document not found: {document_id}"
            raise DocumentNotFoundError(msg)
        return doc

    async def list_documents(
        self,
        project_id: uuid.UUID,
        source_type: SourceType | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[RawDocument], int]:
        """List documents by project with optional source-type filter."""
        project = await self.db.get(Project, project_id)
        if project is None:
            msg = f"Project not found: {project_id}"
            raise ProjectNotFoundError(msg)

        filters = [RawDocument.project_id == project_id]
        if source_type is not None:
            filters.append(RawDocument.source_type == source_type.value)

        count_stmt = select(func.count(RawDocument.id)).where(*filters)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        list_stmt = (
            select(RawDocument)
            .where(*filters)
            .order_by(RawDocument.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(list_stmt)
        documents = list(result.scalars().all())
        return documents, total
