"""Integration tests for the real Evidence Validation Agent node (evidence_validator)."""

import pytest

from app.graph.builder import build_graph
from app.graph.nodes.evidence_validator import evidence_validator
from app.graph.state import ResearchState
from app.models.company import CompanyProfile, EvidenceClaim
from app.models.identity import Organization
from app.models.research import Research
from app.repositories.evidence import EvidenceRepository
from app.repositories.research import ResearchRepository
from app.schemas.evidence import VerificationStatus
from tests.integration.test_sqlite_security import sqlite_security_environment


@pytest.mark.asyncio
async def test_evidence_validator_node_requires_research_question():
    state = ResearchState(
        research_id="res-fail",
        company_name="Acme",
        industry="Software",
        research_question="",  # missing
    )
    result = await evidence_validator(state)
    assert any(m["status"] == "failed" for m in result["execution_metadata"])
    assert len(result["errors"]) >= 1
    assert result["errors"][0]["node_name"] == "evidence_validator"


@pytest.mark.asyncio
async def test_evidence_validator_node_evaluates_evidence_and_produces_summary():
    state = ResearchState(
        research_id="res-node-1",
        organization_id="org-test",
        company_name="Acme Corp",
        industry="Enterprise Software",
        research_question="What are Acme's core products and pricing?",
        evidence=[
            {
                "evidence_id": "ev-node-p1",
                "claim": "Acme pricing starts at $49/month",
                "source_url": "https://reuters.com/acme-pricing",
                "source_domain": "reuters.com",
                "raw_snippet": "Acme pricing starts at $49/month for small teams.",
                "published_at": "2026-02-01T00:00:00Z",
            },
            {
                "evidence_id": "ev-node-p2",
                "claim": "Acme pricing starts at $99/month",
                "source_url": "https://bloomberg.com/acme-pricing",
                "source_domain": "bloomberg.com",
                "raw_snippet": "Acme pricing starts at $99/month for small teams.",
                "published_at": "2026-02-01T00:00:00Z",
            },
            {
                "evidence_id": "ev-node-doc",
                "claim": "Acme supports REST and GraphQL APIs",
                "source_url": "https://docs.acme.com/api-reference",
                "source_domain": "docs.acme.com",
                "raw_snippet": "Acme supports REST and GraphQL APIs for all developers.",
                "published_at": "2026-01-10T00:00:00Z",
            },
        ],
    )

    update = await evidence_validator(state)

    assert "evidence" in update
    assert "validation_results" in update
    assert "execution_metadata" in update

    val_res = update["validation_results"]
    assert val_res["total_claims"] == 3
    assert val_res["contradicted_count"] == 2
    assert val_res["verified_count"] == 1
    assert len(val_res["human_review_queue"]) >= 1

    # Check updated evidence list
    updated_ev = update["evidence"]
    assert len(updated_ev) == 3
    doc_ev = next(e for e in updated_ev if e["evidence_id"] == "ev-node-doc")
    assert doc_ev["verification_status"] == VerificationStatus.VERIFIED
    assert doc_ev["confidence"] >= 0.75

    metadata = update["execution_metadata"][0]
    assert metadata["node_name"] == "evidence_validator"
    assert metadata["status"] == "completed"
    assert metadata["mock"] is False


@pytest.mark.asyncio
async def test_evidence_validator_persists_to_sqlite(sqlite_security_environment):
    """Verify evidence validation updates persistent database records in SQLite."""
    factory = sqlite_security_environment["session_factory"]

    # 1. Seed database with organization, company, and evidence records
    async with factory() as session:
        session.add(Organization(organization_id="org-sec", name="Security Test Org"))
        await session.flush()

        comp_prof = CompanyProfile(
            company_id="comp-acme",
            organization_id="org-sec",
            company_name="Acme Corp",
            industry="Software",
        )
        session.add(comp_prof)
        await session.flush()

        claim_1 = EvidenceClaim(
            evidence_id="ev-db-1",
            company_profile_id=comp_prof.id,
            organization_id="org-sec",
            claim="Acme was founded in 2018",
            source_url="https://sec.gov/edgar/data/acme/10k",
            source_domain="sec.gov",
            evidence_type="regulatory_filing",
            confidence=0.5,
            verification_status="unverified",
            raw_snippet="Acme was founded in 2018 in Delaware.",
        )
        session.add(claim_1)
        await session.commit()

    # 2. Run evidence validator node
    state = ResearchState(
        research_id="res-db-test",
        organization_id="org-sec",
        company_name="Acme Corp",
        industry="Software",
        research_question="When was Acme founded?",
        evidence=[
            {
                "evidence_id": "ev-db-1",
                "claim": "Acme was founded in 2018",
                "source_url": "https://sec.gov/edgar/data/acme/10k",
                "source_domain": "sec.gov",
                "evidence_type": "regulatory_filing",
                "raw_snippet": "Acme was founded in 2018 in Delaware.",
                "published_at": "2026-01-01T00:00:00Z",
            }
        ],
    )

    update = await evidence_validator(state)
    assert update["execution_metadata"][0]["details"]["persistence_status"] == "completed"

    # 3. Verify record was updated in database
    async with factory() as session:
        evidence_repo = EvidenceRepository(session)
        updated_claim = await evidence_repo.get_by_id("ev-db-1", "org-sec")
        assert updated_claim is not None
        assert updated_claim["verification_status"] == VerificationStatus.VERIFIED
        assert updated_claim["confidence"] >= 0.75


@pytest.mark.asyncio
async def test_evidence_validator_persists_full_validation_summary_and_human_review_queue(sqlite_security_environment):
    """Verify full validation summary and review queue are persisted and survive process restart."""
    factory = sqlite_security_environment["session_factory"]

    # 1. Seed organization and research run
    async with factory() as session:
        session.add(Organization(organization_id="org-persist", name="Persistence Test Org"))
        await session.flush()

        research = Research(
            research_id="res-persist-1",
            organization_id="org-persist",
            company_name="Acme Corp",
            industry="SaaS",
            research_question="What is Acme pricing?",
            status="started",
            review_status="started",
            results={},
            errors=[],
        )
        session.add(research)
        await session.commit()

    # 2. Run evidence validator node with contradictory evidence
    state = ResearchState(
        research_id="res-persist-1",
        organization_id="org-persist",
        company_name="Acme Corp",
        industry="SaaS",
        research_question="What is Acme pricing?",
        evidence=[
            {
                "evidence_id": "ev-p1",
                "claim": "Acme Starter costs $29/mo",
                "source_url": "https://reuters.com/acme",
                "source_domain": "reuters.com",
                "raw_snippet": "Acme charges $29/mo.",
                "published_at": "2026-02-01T00:00:00Z",
            },
            {
                "evidence_id": "ev-p2",
                "claim": "Acme Starter costs $89/mo",
                "source_url": "https://bloomberg.com/acme",
                "source_domain": "bloomberg.com",
                "raw_snippet": "Acme charges $89/mo.",
                "published_at": "2026-02-01T00:00:00Z",
            },
        ],
    )

    update = await evidence_validator(state)
    assert update["execution_metadata"][0]["details"]["persistence_status"] == "completed"

    # 3. Simulate process restart by querying through a completely fresh database session
    async with factory() as fresh_session:
        evidence_repo = EvidenceRepository(fresh_session)
        research_repo = ResearchRepository(fresh_session)

        # Retrieve validation summary via evidence repository
        summary = await evidence_repo.get_validation_summary("res-persist-1", "org-persist")
        assert summary is not None
        assert summary["total_claims"] == 2
        assert summary["contradicted_count"] == 2
        assert len(summary["contradictions"]) >= 1
        assert len(summary["human_review_queue"]) >= 1

        # Verify research review_status was set to requires_review
        res_row = await research_repo.get_by_id("res-persist-1", "org-persist")
        assert res_row["review_status"] == "requires_review"


@pytest.mark.asyncio
async def test_evidence_validator_cross_tenant_isolation_idor_protection(sqlite_security_environment):
    """Tenant isolation: Org B cannot retrieve Org A's validation summary."""
    factory = sqlite_security_environment["session_factory"]

    async with factory() as session:
        session.add(Organization(organization_id="org-a", name="Org A"))
        session.add(Organization(organization_id="org-b", name="Org B"))
        await session.flush()

        research_a = Research(
            research_id="res-org-a-1",
            organization_id="org-a",
            company_name="Acme A",
            industry="SaaS",
            research_question="Question A",
            status="started",
            review_status="started",
            results={},
            errors=[],
        )
        session.add(research_a)
        await session.commit()

    state_a = ResearchState(
        research_id="res-org-a-1",
        organization_id="org-a",
        company_name="Acme A",
        industry="SaaS",
        research_question="Question A",
        evidence=[
            {
                "evidence_id": "ev-a-1",
                "claim": "Acme A was founded in 2020",
                "source_url": "https://sec.gov/filing",
                "source_domain": "sec.gov",
                "raw_snippet": "Founded in 2020 in California.",
                "published_at": "2026-01-01T00:00:00Z",
            }
        ],
    )
    await evidence_validator(state_a)

    # Org B attempts to retrieve Org A's summary -> must return None
    async with factory() as fresh_session:
        evidence_repo = EvidenceRepository(fresh_session)
        summary_unauthorized = await evidence_repo.get_validation_summary("res-org-a-1", "org-b")
        assert summary_unauthorized is None

        # Org A accesses own summary -> succeeds
        summary_authorized = await evidence_repo.get_validation_summary("res-org-a-1", "org-a")
        assert summary_authorized is not None
        assert summary_authorized["verified_count"] == 1


@pytest.mark.asyncio
async def test_evidence_validator_retry_idempotency(sqlite_security_environment):
    """Retrying the validation node does not create duplicate entries or corrupt the review queue."""
    factory = sqlite_security_environment["session_factory"]

    async with factory() as session:
        session.add(Organization(organization_id="org-retry", name="Retry Org"))
        await session.flush()

        research = Research(
            research_id="res-retry-1",
            organization_id="org-retry",
            company_name="Beta Corp",
            industry="AI",
            research_question="Question Beta",
            status="started",
            review_status="started",
            results={},
            errors=[],
        )
        session.add(research)
        await session.commit()

    state = ResearchState(
        research_id="res-retry-1",
        organization_id="org-retry",
        company_name="Beta Corp",
        industry="AI",
        research_question="Question Beta",
        evidence=[
            {
                "evidence_id": "ev-r-1",
                "claim": "Beta Corp raised $10M Series A",
                "source_url": "https://techcrunch.com/beta",
                "source_domain": "techcrunch.com",
                "raw_snippet": "Beta Corp closed $10M Series A.",
                "published_at": "2026-01-15T00:00:00Z",
            }
        ],
    )

    # First run
    update_1 = await evidence_validator(state)
    assert update_1["validation_results"]["total_claims"] == 1

    # Second run (retry)
    update_2 = await evidence_validator(state)
    assert update_2["validation_results"]["total_claims"] == 1

    async with factory() as fresh_session:
        evidence_repo = EvidenceRepository(fresh_session)
        summary = await evidence_repo.get_validation_summary("res-retry-1", "org-retry")
        assert summary is not None
        assert summary["total_claims"] == 1
