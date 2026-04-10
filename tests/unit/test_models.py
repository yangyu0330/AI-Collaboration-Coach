"""Phase 1 ORM smoke tests against the configured database."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.config import settings
from packages.db.models import Project, User


def _is_placeholder_database_url(url: str) -> bool:
    markers = ["[PROJECT-REF]", "[PASSWORD]", "placeholder/unused", "localhost:5432/postgres"]
    return any(marker in url for marker in markers)


pytestmark = pytest.mark.skipif(
    _is_placeholder_database_url(settings.database_url),
    reason="A real DATABASE_URL is required for integration-style model tests.",
)


@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_project(db_session: AsyncSession) -> None:
    project = Project(name=f"phase1-test-project-{uuid4().hex[:8]}", description="phase1 test")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    assert project.id is not None
    assert project.name.startswith("phase1-test-project-")

    await db_session.delete(project)
    await db_session.commit()


@pytest.mark.asyncio
async def test_create_user_with_project(db_session: AsyncSession) -> None:
    project = Project(name=f"phase1-test-user-project-{uuid4().hex[:8]}")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    user = User(
        project_id=project.id,
        telegram_id=int(str(uuid4().int)[:10]),
        username=f"phase1-user-{uuid4().hex[:6]}",
        first_name="Phase1",
        role="leader",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.project_id == project.id
    assert user.role == "leader"

    await db_session.delete(user)
    await db_session.delete(project)
    await db_session.commit()

