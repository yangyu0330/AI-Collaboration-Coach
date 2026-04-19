"""Phase 3 document ingestion tests."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.config import settings
from apps.api.schemas.document import DocumentCreate
from packages.core.services.document_service import (
    DocumentNotFoundError,
    DocumentService,
    ProjectNotFoundError,
)
from packages.db.models import Project
from packages.shared.enums import SourceType


def _is_placeholder_database_url(url: str) -> bool:
    markers = ["[PROJECT-REF]", "[PASSWORD]", "placeholder/unused", "localhost:5432/postgres"]
    return any(marker in url for marker in markers)


pytestmark = pytest.mark.skipif(
    _is_placeholder_database_url(settings.database_url),
    reason="A real DATABASE_URL is required for document ingestion tests.",
)


@pytest.fixture
def queued_document_ids(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    queued: list[str] = []

    class _FakeAnalyzeDocumentTask:
        @staticmethod
        def delay(document_id: str) -> None:
            queued.append(document_id)

    monkeypatch.setattr(
        "apps.worker.tasks.analysis_tasks.analyze_document_task",
        _FakeAnalyzeDocumentTask(),
    )
    return queued


@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_document_and_fetch_by_id(
    db_session: AsyncSession,
    queued_document_ids: list[str],
) -> None:
    project = Project(name=f"phase3-project-{uuid4().hex[:8]}")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    service = DocumentService(db=db_session)
    created = await service.create_document(
        DocumentCreate(
            project_id=project.id,
            source_type=SourceType.MEETING,
            title="Sprint sync notes",
            content="1) Prioritize auth flow\n2) Move hosting to Supabase",
        )
    )

    fetched = await service.get_document(created.id)
    assert fetched.id == created.id
    assert fetched.project_id == project.id
    assert fetched.source_type == SourceType.MEETING.value
    assert fetched.title == "Sprint sync notes"
    assert fetched.content.startswith("1) Prioritize")
    assert queued_document_ids == [str(created.id)]

    await db_session.delete(project)
    await db_session.commit()


@pytest.mark.asyncio
async def test_list_documents_with_source_type_filter(
    db_session: AsyncSession,
    queued_document_ids: list[str],
) -> None:
    project = Project(name=f"phase3-list-{uuid4().hex[:8]}")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    service = DocumentService(db=db_session)
    payloads = [
        DocumentCreate(
            project_id=project.id,
            source_type=SourceType.MEETING,
            title="meeting-a",
            content="notes a",
        ),
        DocumentCreate(
            project_id=project.id,
            source_type=SourceType.PROFESSOR_FEEDBACK,
            title="feedback-a",
            content="feedback notes",
        ),
        DocumentCreate(
            project_id=project.id,
            source_type=SourceType.MEETING,
            title="meeting-b",
            content="notes b",
        ),
    ]
    for payload in payloads:
        await service.create_document(payload)

    all_docs, all_total = await service.list_documents(project_id=project.id)
    assert all_total == 3
    assert len(all_docs) == 3

    meeting_docs, meeting_total = await service.list_documents(
        project_id=project.id,
        source_type=SourceType.MEETING,
    )
    assert meeting_total == 2
    assert len(meeting_docs) == 2
    assert all(doc.source_type == SourceType.MEETING.value for doc in meeting_docs)
    assert len(queued_document_ids) == 3

    await db_session.delete(project)
    await db_session.commit()


@pytest.mark.asyncio
async def test_create_document_rejects_unknown_project(
    db_session: AsyncSession,
    queued_document_ids: list[str],
) -> None:
    service = DocumentService(db=db_session)
    with pytest.raises(ProjectNotFoundError):
        await service.create_document(
            DocumentCreate(
                project_id=uuid4(),
                source_type=SourceType.MANUAL_NOTE,
                title="orphan",
                content="orphan content",
            )
        )
    assert queued_document_ids == []


@pytest.mark.asyncio
async def test_get_document_raises_when_missing(db_session: AsyncSession) -> None:
    service = DocumentService(db=db_session)
    with pytest.raises(DocumentNotFoundError):
        await service.get_document(uuid4())


def test_document_create_rejects_blank_content() -> None:
    with pytest.raises(ValidationError):
        DocumentCreate(
            project_id=uuid4(),
            source_type=SourceType.MANUAL_NOTE,
            title="blank-content",
            content="   ",
        )
