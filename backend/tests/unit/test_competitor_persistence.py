"""Integration tests for competitor persistence."""

import os

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.exceptions import ResearchError
from app.core.config import get_settings
from app.core.database import db
from app.models.competitor import Competitor, CompetitorEvidence
from app.models.research import Research
from app.repositories.competitor import (
    CompetitorEvidenceRepository,
    CompetitorRepository,
)

get_settings.cache_clear()
db._configured = False
db._engine = None
db._session_factory = None
db._available = False
db._checkpointer = None

TEST_DATABASE_URL = os.getenv("ACIS_TEST_DATABASE_URL") or ""
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="PostgreSQL tests require a dedicated ACIS_TEST_DATABASE_URL.",
)


@pytest.fixture
async def session():
    eng = create_async_engine(TEST_DATABASE_URL)
    async with AsyncSession(eng) as session:
        await session.begin()
        session.add_all(
            [
                Research(
                    research_id=research_id,
                    organization_id="org-a",
                    company_name="Test company",
                    industry="Technology",
                    research_question="Research competitors",
                    status="completed",
                )
                for research_id in (
                    "res-test-1",
                    "res-org-iso",
                    "res-scope-1",
                    "res-ev-1",
                    "res-ev-iso",
                    "res-dup-1",
                )
            ]
        )
        await session.flush()
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()
    await eng.dispose()


@pytest.fixture
async def competitor_repo(session):
    return CompetitorRepository(session)


@pytest.fixture
async def evidence_repo(session):
    return CompetitorEvidenceRepository(session)


@pytest.mark.asyncio
async def test_competitor_repository_create_and_get(competitor_repo):
    row = await competitor_repo.create(
        competitor_id="comp-test-1",
        research_id="res-test-1",
        organization_id="org-a",
        company_name="Competitor A",
        competitor_type="direct",
        company_description="AI competitor.",
        profile={"description": "AI competitor.", "products": ["Platform A"]},
        website="https://competa.example.com",
        qualification_score=0.8,
        confidence=0.8,
        verification_status="verified",
        source_references=["https://competa.example.com"],
    )
    assert row["competitor_id"] == "comp-test-1"
    assert row["organization_id"] == "org-a"
    assert row["company_name"] == "Competitor A"
    assert row["competitor_type"] == "direct"
    assert row["qualification_score"] == 0.8

    fetched = await competitor_repo.get_by_id("comp-test-1", "org-a")
    assert fetched is not None
    assert fetched["company_name"] == "Competitor A"


@pytest.mark.asyncio
async def test_competitor_repository_org_isolation(competitor_repo):
    await competitor_repo.create(
        competitor_id="comp-org-iso",
        research_id="res-org-iso",
        organization_id="org-a",
        company_name="Competitor A",
        competitor_type="direct",
        qualification_score=0.5,
        confidence=0.5,
        verification_status="unverified",
    )
    fetched = await competitor_repo.get_by_id("comp-org-iso", "org-b")
    assert fetched is None


@pytest.mark.asyncio
async def test_competitor_lookup_is_scoped_by_research_and_organization(
    competitor_repo,
):
    await competitor_repo.create(
        competitor_id="comp-scope-1",
        research_id="res-scope-1",
        organization_id="org-a",
        company_name="Scoped Company",
        website="https://scoped.example.com",
        competitor_type="direct",
        qualification_score=0.7,
        confidence=0.7,
        verification_status="unverified",
    )
    assert await competitor_repo.get_by_company(
        "res-scope-1", "org-a", "SCOPED COMPANY"
    )
    assert (
        await competitor_repo.get_by_company(
            "res-scope-1", "org-b", "Scoped Company"
        )
        is None
    )
    assert (
        await competitor_repo.get_by_company(
            "res-scope-2", "org-a", "Scoped Company"
        )
        is None
    )


@pytest.mark.asyncio
async def test_competitor_evidence_repository(competitor_repo, evidence_repo):
    profile_row = await competitor_repo.create(
        competitor_id="comp-ev-1",
        research_id="res-ev-1",
        organization_id="org-a",
        company_name="Competitor A",
        competitor_type="direct",
        qualification_score=0.8,
        confidence=0.8,
        verification_status="verified",
    )
    profile_id = profile_row["id"]

    ev_row = await evidence_repo.create(
        evidence_id="comp-ev-claim-1",
        competitor_id=profile_row["competitor_id"],
        organization_id="org-a",
        research_id="res-ev-1",
        claim="Competitor A sells AI platform.",
        source_url="https://competa.example.com",
        source_title="Competitor A",
        source_domain="competa.example.com",
        evidence_type="official_website",
        confidence=0.9,
        verification_status="verified",
        raw_snippet="AI platform.",
    )
    assert ev_row["evidence_id"] == "comp-ev-claim-1"
    assert ev_row["verification_status"] == "verified"

    claims = await evidence_repo.list_by_competitor(
        profile_row["competitor_id"], "org-a"
    )
    assert len(claims) == 1
    assert claims[0]["claim"] == "Competitor A sells AI platform."


@pytest.mark.asyncio
async def test_competitor_evidence_org_isolation(competitor_repo, evidence_repo):
    profile_row = await competitor_repo.create(
        competitor_id="comp-ev-iso",
        research_id="res-ev-iso",
        organization_id="org-a",
        company_name="Competitor A",
        competitor_type="direct",
        qualification_score=0.5,
        confidence=0.5,
        verification_status="unverified",
    )
    await evidence_repo.create(
        evidence_id="comp-ev-iso-1",
        competitor_id=profile_row["competitor_id"],
        organization_id="org-a",
        research_id="res-ev-iso",
        claim="claim",
        source_url="https://example.com",
        source_domain="example.com",
    )
    claims = await evidence_repo.list_by_competitor(
        profile_row["competitor_id"], "org-b"
    )
    assert claims == []


@pytest.mark.asyncio
async def test_competitor_duplicate_prevention(competitor_repo):
    """Test that duplicate competitor records are prevented by unique constraint."""
    await competitor_repo.create(
        competitor_id="comp-dup-2",
        research_id="res-dup-1",
        organization_id="org-a",
        company_name="duplicate-co",
        competitor_type="direct",
        qualification_score=0.5,
        confidence=0.5,
        verification_status="unverified",
    )
    # Creating the same competitor_id should fail (unique constraint)
    with pytest.raises(ResearchError):
        await competitor_repo.create(
            competitor_id="comp-dup-1",
            research_id="res-dup-1",
            organization_id="org-a",
            company_name="Duplicate Co",
            competitor_type="direct",
            qualification_score=0.5,
            confidence=0.5,
            verification_status="unverified",
        )


@pytest.mark.asyncio
async def test_competitor_tables_exist():
    from sqlalchemy import text

    eng = create_async_engine(TEST_DATABASE_URL)
    async with eng.connect() as conn:
        r1 = await conn.execute(text("SELECT to_regclass('public.competitors')"))
        assert r1.scalar() == "competitors"
        r2 = await conn.execute(text("SELECT to_regclass('public.competitor_evidence')"))
        assert r2.scalar() == "competitor_evidence"
    await eng.dispose()


__all__ = []
