"""ACIS Phase 3.2: Production PostgreSQL Integration, Evidence Persistence,
Tenant Isolation, and Report Storage Verification Suite.
"""

import asyncio
import os
import uuid
from typing import Any, Dict

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings
from app.core.database import db
from app.core.exceptions import DatabaseUnavailableError, NotFoundError, ValidationError
from app.models.identity import Organization
from app.models.research import Research
from app.repositories.report import ReportRepository
from app.repositories.research import ResearchRepository
from app.services.research_service import (
    get_evidence_reviews,
    review_evidence,
)

from dotenv import load_dotenv

load_dotenv()

TEST_DATABASE_URL = os.getenv("ACIS_TEST_DATABASE_URL") or ""
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="PostgreSQL tests require a dedicated ACIS_TEST_DATABASE_URL.",
)


def _uid(prefix: str = "test") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@pytest.fixture(autouse=True)
def clean_db_singleton():
    yield
    db._configured = False
    db._available = False
    db._session_factory = None


@pytest.fixture
async def pg_engine():
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def pg_session(pg_engine):
    async with AsyncSession(pg_engine) as session:
        await session.begin()
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture
async def seed_orgs(pg_engine):
    """Seed test organizations org-alpha and org-beta into PostgreSQL."""
    org_alpha_id = _uid("org-alpha")
    org_beta_id = _uid("org-beta")
    async with AsyncSession(pg_engine) as session:
        async with session.begin():
            session.add(Organization(organization_id=org_alpha_id, name="Alpha Corp"))
            session.add(Organization(organization_id=org_beta_id, name="Beta Global"))
    return org_alpha_id, org_beta_id


@pytest.mark.asyncio
async def test_evidence_review_persistence_and_machine_preservation_lifecycle(
    pg_engine, seed_orgs
):
    """Verify evidence reviews survive across fresh database sessions while

    preserving machine validation baselines and supporting all valid decisions.
    """
    org_alpha, _ = seed_orgs
    research_id = _uid("res-alpha")
    evidence_id = _uid("ev-101")

    # 1. Create a research record with machine validation telemetry in PostgreSQL
    initial_evidence = [
        {
            "evidence_id": evidence_id,
            "claim": "Alpha generated $50M in cloud telemetry ARR with 125% NRR.",
            "source_domain": "sec.gov",
            "source_url": "https://sec.gov/filings/alpha",
            "verification_status": "verified",
            "confidence": 0.94,
            "machine_verification_status": "verified",
            "machine_confidence": 0.94,
            "machine_explanation": "Direct audited SEC 10-K filing statement.",
        }
    ]

    async with AsyncSession(pg_engine) as session:
        async with session.begin():
            repo = ResearchRepository(session)
            await repo.create(
                research_id=research_id,
                organization_id=org_alpha,
                company_name="Alpha Corp",
                industry="Cloud Observability",
                research_question="ARR and retention benchmark?",
                status="completed",
                results={
                    "evidence": initial_evidence,
                    "validation_results": {"human_review_log": []},
                },
            )

    # 2. Test all valid decision types and verify persistence in PostgreSQL
    decisions = [
        "approved",
        "rejected",
        "flagged",
        "partially_verified",
        "unverified",
        "contradicted",
    ]

    for decision in decisions:
        # Connect global db singleton to the test engine for service calls
        db._configured = True
        db._available = True
        db._session_factory = lambda: AsyncSession(pg_engine)

        review_res = await review_evidence(
            research_id=research_id,
            evidence_id=evidence_id,
            organization_id=org_alpha,
            decision=decision,
            analyst_notes=f"Analyst notes for {decision}",
            reviewed_by="lead_analyst@enterprise.com",
            override_confidence=0.88,
        )

        assert review_res["status"] == "success"
        assert review_res["verification_status"] == decision
        assert review_res["machine_verification_status"] == "verified"
        assert review_res["machine_confidence"] == 0.94
        assert review_res["machine_explanation"] == "Direct audited SEC 10-K filing statement."

        # 3. Discard session, open a completely FRESH session directly from engine
        async with AsyncSession(pg_engine) as fresh_session:
            repo_fresh = ResearchRepository(fresh_session)
            persisted = await repo_fresh.get_by_id(research_id, org_alpha)
            assert persisted is not None

            # Verify persisted evidence item
            ev_list = persisted["results"].get("evidence", [])
            matched_ev = next(e for e in ev_list if e["evidence_id"] == evidence_id)

            # Verification: Human decision was applied
            assert matched_ev["verification_status"] == decision
            assert matched_ev["confidence"] == 0.88

            # Verification: Machine baseline was NEVER overwritten
            assert matched_ev["machine_verification_status"] == "verified"
            assert matched_ev["machine_confidence"] == 0.94
            assert matched_ev["machine_explanation"] == "Direct audited SEC 10-K filing statement."

            # Verification: Human review details recorded
            assert matched_ev["human_review"]["decision"] == decision
            assert matched_ev["human_review"]["reviewed_by"] == "lead_analyst@enterprise.com"
            assert f"for {decision}" in matched_ev["human_review"]["analyst_notes"]
            assert "reviewed_at" in matched_ev["human_review"]

    # 4. Verify invalid decision is rejected with ValidationError
    with pytest.raises(ValidationError) as exc_info:
        await review_evidence(
            research_id=research_id,
            evidence_id=evidence_id,
            organization_id=org_alpha,
            decision="invalid_unsupported_decision",
        )
    assert "Invalid decision" in str(exc_info.value)

    # 5. Verify review history audit log across fresh session
    audit_res = await get_evidence_reviews(
        research_id=research_id,
        organization_id=org_alpha,
        evidence_id=evidence_id,
    )
    assert audit_res["machine_verification_status"] == "verified"
    assert audit_res["machine_confidence"] == 0.94
    assert audit_res["machine_explanation"] == "Direct audited SEC 10-K filing statement."
    assert audit_res["current_verification_status"] == "contradicted"  # last decision
    assert len(audit_res["reviews"]) == len(decisions)


@pytest.mark.asyncio
async def test_postgres_tenant_isolation(pg_engine, seed_orgs):
    """Verify strict tenant isolation in PostgreSQL across research, evidence,

    and review history queries.
    """
    org_alpha, org_beta = seed_orgs
    res_alpha = _uid("res-alpha")
    res_beta = _uid("res-beta")
    ev_alpha = _uid("ev-alpha")
    ev_beta = _uid("ev-beta")

    # 1. Create Alpha and Beta research in PostgreSQL
    async with AsyncSession(pg_engine) as session:
        async with session.begin():
            repo = ResearchRepository(session)
            await repo.create(
                research_id=res_alpha,
                organization_id=org_alpha,
                company_name="Alpha Confidential",
                industry="FinTech",
                research_question="Alpha question?",
                status="completed",
                results={"evidence": [{"evidence_id": ev_alpha, "claim": "Alpha claim"}]},
            )
            await repo.create(
                research_id=res_beta,
                organization_id=org_beta,
                company_name="Beta Confidential",
                industry="HealthTech",
                research_question="Beta question?",
                status="completed",
                results={"evidence": [{"evidence_id": ev_beta, "claim": "Beta claim"}]},
            )

    async with AsyncSession(pg_engine) as session:
        repo = ResearchRepository(session)

        # 2. Alpha can access its own research
        alpha_data = await repo.get_by_id(res_alpha, org_alpha)
        assert alpha_data is not None
        assert alpha_data["company_name"] == "Alpha Confidential"

        # 3. Beta CANNOT read Alpha's research (returns None)
        cross_read = await repo.get_by_id(res_alpha, org_beta)
        assert cross_read is None

        # 4. Alpha CANNOT read Beta's research (returns None)
        cross_read_rev = await repo.get_by_id(res_beta, org_alpha)
        assert cross_read_rev is None

        # 5. Beta CANNOT update Alpha's research status
        cross_update = await repo.update_status(
            research_id=res_alpha,
            organization_id=org_beta,
            status="failed",
            results={},
        )
        assert cross_update is None

    # 6. Service layer: Beta attempting to fetch Alpha evidence reviews raises NotFoundError
    db._configured = True
    db._available = True
    db._session_factory = lambda: AsyncSession(pg_engine)

    with pytest.raises(NotFoundError):
        await get_evidence_reviews(
            research_id=res_alpha,
            organization_id=org_beta,
        )

    # 7. Beta attempting to review Alpha's evidence raises NotFoundError
    with pytest.raises(NotFoundError):
        await review_evidence(
            research_id=res_alpha,
            evidence_id=ev_alpha,
            organization_id=org_beta,
            decision="approved",
        )


@pytest.mark.asyncio
async def test_report_persistence_and_fresh_session_retrieval(pg_engine, seed_orgs):
    """Verify 14-section report persistence in PostgreSQL with PDF/Markdown

    retrieval across fresh sessions and tenant boundary enforcement.
    """
    org_alpha, org_beta = seed_orgs
    research_id = _uid("res-report")

    report_payload = {
        "title": "Comprehensive Strategic Intelligence: Apex Global",
        "company": "Apex Global",
        "metadata": {
            "report_id": f"rpt-{research_id}",
            "generated_at": "2026-11-06T12:00:00Z",
        },
        "sections": {
            "executive_summary": "Apex Global dominates enterprise telemetry.",
            "company_profile": "Global streaming observability platform.",
            "actionable_recommendations": "Expand EU sovereign cloud operations.",
        },
        "overall_confidence": 0.95,
    }
    pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\ntrailer<</Size 2/Root 1 0 R>>\n%%EOF"
    md_text = "# Strategic Report: Apex Global\n\n## 1. Executive Summary\nApex Global dominates."

    # 1. Create base research record in PostgreSQL
    async with AsyncSession(pg_engine) as session:
        async with session.begin():
            repo = ResearchRepository(session)
            await repo.create(
                research_id=research_id,
                organization_id=org_alpha,
                company_name="Apex Global",
                industry="Cloud Observability",
                research_question="Strategic position?",
                status="completed",
                results={},
            )

    # 2. Persist report JSON and binary artifacts via ReportRepository
    async with AsyncSession(pg_engine) as session:
        report_repo = ReportRepository(session)
        success = await report_repo.save_report(
            research_id=research_id,
            organization_id=org_alpha,
            report_data=report_payload,
            pdf_bytes=pdf_bytes,
            markdown_text=md_text,
        )
        assert success is True
        await session.commit()

    # 3. Discard session and open a fresh session to verify durable retrieval
    async with AsyncSession(pg_engine) as fresh_session:
        fresh_repo = ReportRepository(fresh_session)

        # Retrieve JSON
        retrieved_json = await fresh_repo.get_report_json(research_id, org_alpha)
        assert retrieved_json is not None
        assert retrieved_json["title"] == report_payload["title"]
        assert retrieved_json["overall_confidence"] == 0.95
        assert retrieved_json["sections"]["executive_summary"] == report_payload["sections"]["executive_summary"]

        # Retrieve PDF
        retrieved_pdf = await fresh_repo.get_report_pdf(research_id, org_alpha)
        assert retrieved_pdf is not None
        assert retrieved_pdf.startswith(b"%PDF-1.4")

        # Retrieve Markdown
        retrieved_md = await fresh_repo.get_report_markdown(research_id, org_alpha)
        assert retrieved_md is not None
        assert "Apex Global dominates" in retrieved_md

        # 4. Cross-tenant retrieval check: Org Beta querying Alpha's report
        beta_json = await fresh_repo.get_report_json(research_id, org_beta)
        assert beta_json is None

        beta_pdf = await fresh_repo.get_report_pdf(research_id, org_beta)
        assert beta_pdf is None

        beta_md = await fresh_repo.get_report_markdown(research_id, org_beta)
        assert beta_md is None

        # 5. Missing report check
        missing = await fresh_repo.get_report_json("non-existent-id", org_alpha)
        assert missing is None


@pytest.mark.asyncio
async def test_database_outage_fails_closed_in_production(monkeypatch):
    """Verify that when database is unavailable in production, fallback is

    strictly blocked and the system fails closed with 503 instead of silent data loss.
    """
    from fastapi import HTTPException
    from app.api.v1.endpoints.reports import get_report_json_endpoint
    from app.security.auth import AuthenticatedUser, OrganizationContext, Role

    user = AuthenticatedUser(
        user_id="user-123",
        email="owner@prod.com",
        session_id="session-123",
        is_platform_admin=False,
    )
    context = OrganizationContext(
        user=user,
        organization_id="org-prod",
        role=Role.OWNER,
    )

    # Simulate production environment and database unavailable
    settings = get_settings()
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(db, "_configured", True)
    monkeypatch.setattr(db, "_available", False)

    # 1. Report endpoint must raise 503 Service Unavailable, NEVER fallback
    with pytest.raises(HTTPException) as exc_info:
        await get_report_json_endpoint(context=context, research_id="res-any")

    assert exc_info.value.status_code == 503
    assert "Database persistence is required" in exc_info.value.detail

    # 2. Research service persistence must raise DatabaseUnavailableError in production
    from app.schemas.research import ResearchResult
    res_obj = ResearchResult(
        research_id="res-prod-999",
        organization_id="org-prod",
        company_name="Prod Corp",
        industry="SaaS",
        research_question="Market?",
        status="completed",
    )

    from app.services.research_service import _persist_result
    with pytest.raises(DatabaseUnavailableError):
        await _persist_result(res_obj)

    # 3. Evidence review must raise DatabaseUnavailableError in production
    with pytest.raises(DatabaseUnavailableError):
        await review_evidence(
            research_id="res-prod-999",
            evidence_id="ev-prod-1",
            organization_id="org-prod",
            decision="approved",
        )
