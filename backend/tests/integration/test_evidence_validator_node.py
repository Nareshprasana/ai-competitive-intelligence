"""Integration tests for the real Evidence Validation Agent node (evidence_validator)."""

import pytest

from app.graph.builder import build_graph
from app.graph.nodes.evidence_validator import evidence_validator
from app.graph.state import ResearchState
from app.models.company import CompanyProfile, EvidenceClaim
from app.models.identity import Organization
from app.repositories.evidence import EvidenceRepository
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
