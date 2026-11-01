"""Tests for PostgreSQL-backed research persistence (repository layer).

Requires DATABASE_URL to point at a live PostgreSQL instance
(the acis_db database configured for this phase). Tests run against the real
database; each test rolls back its own transaction so rows don't accumulate.
"""

import asyncio
import os
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings
from app.core.database import db
from app.repositories.research import ResearchRepository

# Ensure settings are re-read with DATABASE_URL from the environment.
get_settings.cache_clear()
db._configured = False
db._engine = None
db._session_factory = None
db._available = False
db._checkpointer = None

TEST_DATABASE_URL = os.getenv(
    "ACIS_TEST_DATABASE_URL",
    "postgresql+asyncpg://acis_app:acis_dev_password@127.0.0.1:5432/acis_db",
)


def _rid(prefix="res"):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@pytest.fixture
async def session():
    """Yield a SQLAlchemy async session with a rolled-back transaction."""
    eng = create_async_engine(TEST_DATABASE_URL)
    async with AsyncSession(eng) as session:
        await session.begin()
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()
    await eng.dispose()


@pytest.fixture
async def repo(session):
    return ResearchRepository(session)


@pytest.mark.asyncio
async def test_repository_create_and_get_by_id(repo):
    rid = _rid()
    row = await repo.create(
        research_id=rid,
        organization_id="org-a",
        company_name="Acme Corp",
        industry="AI Software",
        research_question="Pricing vs competitors?",
        status="completed",
        review_status="reviewed",
        results={"final_report": {"company": "Acme Corp"}},
        errors=[],
    )
    assert row["research_id"] == rid
    assert row["organization_id"] == "org-a"
    assert row["status"] == "completed"
    assert row["results"]["final_report"]["company"] == "Acme Corp"

    fetched = await repo.get_by_id(rid, "org-a")
    assert fetched is not None
    assert fetched["company_name"] == "Acme Corp"
    assert fetched["errors"] == []


@pytest.mark.asyncio
async def test_repository_get_by_id_wrong_organization_returns_none(repo):
    rid = _rid()
    await repo.create(
        research_id=rid,
        organization_id="org-a",
        company_name="Acme",
        industry="AI",
        research_question="What is the market position?",
        status="completed",
    )
    # Different organization must NOT see the record.
    fetched = await repo.get_by_id(rid, "org-b")
    assert fetched is None


@pytest.mark.asyncio
async def test_repository_update_status(repo):
    rid = _rid()
    await repo.create(
        research_id=rid,
        organization_id="org-a",
        company_name="Acme",
        industry="AI",
        research_question="What is the market position?",
        status="started",
    )
    updated = await repo.update_status(
        research_id=rid,
        organization_id="org-a",
        status="completed",
        review_status="reviewed",
        results={"final_report": {"company": "Acme"}},
        errors=[],
    )
    assert updated is not None
    assert updated["status"] == "completed"
    assert updated["review_status"] == "reviewed"

    fetched = await repo.get_by_id(rid, "org-a")
    assert fetched["status"] == "completed"
    assert fetched["errors"] == []


@pytest.mark.asyncio
async def test_repository_update_status_wrong_organization_returns_none(repo):
    rid = _rid()
    await repo.create(
        research_id=rid,
        organization_id="org-a",
        company_name="Acme",
        industry="AI",
        research_question="What is the market position?",
        status="completed",
    )
    updated = await repo.update_status(
        research_id=rid,
        organization_id="org-b",
        status="failed",
    )
    assert updated is None


@pytest.mark.asyncio
async def test_repository_list_by_organization(repo):
    rid1 = _rid()
    rid2 = _rid()
    await repo.create(
        research_id=rid1,
        organization_id="org-a",
        company_name="Acme",
        industry="AI",
        research_question="What is the market position?",
        status="completed",
    )
    await repo.create(
        research_id=rid2,
        organization_id="org-b",
        company_name="Globex",
        industry="Biotech",
        research_question="What is the market position?",
        status="failed",
    )

    org_a = await repo.list_by_organization("org-a")
    assert len(org_a) == 1
    assert org_a[0]["company_name"] == "Acme"

    org_b = await repo.list_by_organization("org-b")
    assert len(org_b) == 1
    assert org_b[0]["company_name"] == "Globex"


@pytest.mark.asyncio
async def test_repository_organization_has_record(repo):
    rid = _rid()
    await repo.create(
        research_id=rid,
        organization_id="org-a",
        company_name="Acme",
        industry="AI",
        research_question="What is the market position?",
        status="completed",
    )
    assert await repo.organization_has_record(rid, "org-a") is True
    assert await repo.organization_has_record(rid, "org-b") is False
    assert await repo.organization_has_record(_rid("nope"), "org-a") is False


@pytest.mark.asyncio
async def test_database_is_configured():
    """The test database is reachable and configured."""
    assert db.is_available is True
    health = await db.health_check()
    assert health["available"] is True
    assert health["configured"] is True


@pytest.mark.asyncio
async def test_alembic_table_exists():
    """The researches table exists (migration applied)."""
    from sqlalchemy import text

    eng = create_async_engine(TEST_DATABASE_URL)
    async with eng.connect() as conn:
        result = await conn.execute(text("SELECT to_regclass('public.researches')"))
        assert result.scalar() == "researches"
    await eng.dispose()
