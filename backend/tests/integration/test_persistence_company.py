"""Integration tests for company profile and evidence persistence."""

import os

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings
from app.core.database import db
from app.models.company import CompanyProfile, EvidenceClaim
from app.repositories.company import CompanyRepository
from app.repositories.evidence import EvidenceRepository

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


@pytest.fixture
async def session():
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
async def company_repo(session):
    return CompanyRepository(session)


@pytest.fixture
async def evidence_repo(session):
    return EvidenceRepository(session)


@pytest.mark.asyncio
async def test_company_repository_create_and_get(company_repo):
    row = await company_repo.create(
        company_id="comp-test-1",
        organization_id="org-a",
        company_name="Acme Corp",
        industry="AI Software",
        profile={"description": "AI company", "products": ["Platform A"]},
        website="https://acme.example.com",
        source_references=["https://acme.example.com"],
    )
    assert row["company_id"] == "comp-test-1"
    assert row["organization_id"] == "org-a"
    assert row["profile"]["products"] == ["Platform A"]

    fetched = await company_repo.get_by_id("comp-test-1", "org-a")
    assert fetched is not None
    assert fetched["company_name"] == "Acme Corp"


@pytest.mark.asyncio
async def test_company_repository_org_isolation(company_repo):
    await company_repo.create(
        company_id="comp-org-iso",
        organization_id="org-a",
        company_name="Acme Corp",
        industry="AI",
    )
    # Different org cannot see it
    fetched = await company_repo.get_by_id("comp-org-iso", "org-b")
    assert fetched is None


@pytest.mark.asyncio
async def test_evidence_repository_create_and_list(evidence_repo, company_repo):
    # First create a company profile to get its ID
    profile_row = await company_repo.create(
        company_id="comp-evidence-1",
        organization_id="org-a",
        company_name="Acme Corp",
        industry="AI",
    )
    profile_id = profile_row["id"]

    ev_row = await evidence_repo.create(
        evidence_id="ev-claim-1",
        company_profile_id=profile_id,
        organization_id="org-a",
        claim="Acme Corp is headquartered in SF.",
        source_url="https://acme.example.com/about",
        source_title="About Acme",
        source_domain="acme.example.com",
        evidence_type="official_website",
        confidence=0.8,
        verification_status="verified",
        raw_snippet="Headquartered in San Francisco.",
    )
    assert ev_row["evidence_id"] == "ev-claim-1"
    assert ev_row["verification_status"] == "verified"

    claims = await evidence_repo.list_by_profile(profile_id, "org-a")
    assert len(claims) == 1
    assert claims[0]["claim"] == "Acme Corp is headquartered in SF."


@pytest.mark.asyncio
async def test_evidence_repository_org_isolation(evidence_repo, company_repo):
    profile_row = await company_repo.create(
        company_id="comp-ev-iso",
        organization_id="org-a",
        company_name="Acme Corp",
        industry="AI",
    )
    await evidence_repo.create(
        evidence_id="ev-iso-1",
        company_profile_id=profile_row["id"],
        organization_id="org-a",
        claim="claim",
        source_url="https://example.com",
        source_domain="example.com",
    )
    # Different org cannot see evidence
    claims = await evidence_repo.list_by_profile(profile_row["id"], "org-b")
    assert claims == []


@pytest.mark.asyncio
async def test_database_tables_exist():
    from sqlalchemy import text

    eng = create_async_engine(TEST_DATABASE_URL)
    async with eng.connect() as conn:
        r1 = await conn.execute(text("SELECT to_regclass('public.company_profiles')"))
        assert r1.scalar() == "company_profiles"
        r2 = await conn.execute(text("SELECT to_regclass('public.evidence_claims')"))
        assert r2.scalar() == "evidence_claims"
    await eng.dispose()


__all__ = []
