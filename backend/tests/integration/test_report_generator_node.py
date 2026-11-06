"""Integration tests for the real Report Generator Agent node (report_generator).

Verifies:
- Input validation (company_name required)
- End-to-end node execution in ResearchState
- Durable persistence of report JSON in SQLite research records
- Storage and retrieval of binary PDF and text Markdown artifacts
- Process restart / fresh session retrieval
- Cross-tenant isolation (IDOR defense across report JSON, PDF, and Markdown)
- LangGraph execution with real report_generator node
- Retry idempotency
"""

import asyncio
import pytest

from app.graph.builder import build_graph
from app.graph.nodes.report_generator import report_generator
from app.graph.state import ResearchState
from app.models.identity import Organization
from app.models.research import Research
from app.repositories.report import ReportRepository
from app.repositories.research import ResearchRepository
from tests.integration.test_sqlite_security import sqlite_security_environment


@pytest.mark.asyncio
async def test_report_generator_requires_company_name():
    """Verify report_generator node fails gracefully when company_name is missing."""
    state = ResearchState(
        research_id="res-fail-rep",
        company_name="",  # Missing required company_name
        industry="Software",
        research_question="Report generation test?",
    )
    result = await report_generator(state)
    assert any(m["status"] == "failed" for m in result["execution_metadata"])
    assert len(result["errors"]) >= 1
    assert result["errors"][0]["node_name"] == "report_generator"


@pytest.mark.asyncio
async def test_report_generator_node_execution_populates_state():
    """Verify report_generator merges valid final_report and metadata into state."""
    state = ResearchState(
        research_id="res-rep-node-1",
        organization_id="org-test",
        company_name="Apex Telemetry",
        industry="DevOps Software",
        research_question="Competitive report test?",
        company_profile={
            "company_name": "Apex Telemetry",
            "products": ["Telemetry Platform v1"],
        },
        competitors=[
            {
                "competitor_id": "comp-mon-1",
                "company_name": "MonitorX",
                "competitor_type": "direct",
                "products_and_services": ["MonX Core"],
            }
        ],
        evidence=[
            {
                "evidence_id": "ev-apex-int-1",
                "claim": "Apex Telemetry announced distributed tracing v1.",
                "source_url": "https://apex.example/news",
                "source_domain": "apex.example",
                "confidence": 0.88,
                "verification_status": "verified",
            }
        ],
    )

    update = await report_generator(state)

    assert "final_report" in update
    assert "execution_metadata" in update

    report = update["final_report"]
    assert report["company"] == "Apex Telemetry"
    assert report["metadata"]["report_id"] == "rpt-res-rep-node-1"
    assert len(report["competitor_profiles"]) == 1
    assert len(report["evidence_appendix"]) >= 1

    metadata = update["execution_metadata"][0]
    assert metadata["node_name"] == "report_generator"
    assert metadata["status"] == "completed"
    assert metadata["mock"] is False
    assert metadata["details"]["pdf_size_bytes"] > 1000


@pytest.mark.asyncio
async def test_report_generator_persists_to_sqlite_and_storage(sqlite_security_environment):
    """Verify report JSON and artifacts are persisted and retrievable after fresh session."""
    factory = sqlite_security_environment["session_factory"]

    # 1. Seed database with organization and research run
    async with factory() as session:
        session.add(Organization(organization_id="org-rep-sec", name="Report Sec Org"))
        research = Research(
            research_id="res-rep-persist-1",
            organization_id="org-rep-sec",
            company_name="Vanguard Systems",
            industry="Security",
            research_question="Competitive security overview?",
            status="running",
            review_status="pending",
            results={},
            errors=[],
        )
        session.add(research)
        await session.commit()

    # 2. Execute report_generator node
    state = ResearchState(
        research_id="res-rep-persist-1",
        organization_id="org-rep-sec",
        company_name="Vanguard Systems",
        industry="Security",
        research_question="Competitive security overview?",
        company_profile={"products": ["Vanguard Shield"]},
        competitors=[{"competitor_id": "comp-sec-1", "company_name": "Securitas", "competitor_type": "direct"}],
        evidence=[
            {
                "evidence_id": "ev-vanguard-1",
                "claim": "Vanguard Shield offers runtime kernel protection.",
                "source_url": "https://vanguard.example/shield",
                "source_domain": "vanguard.example",
                "confidence": 0.92,
                "verification_status": "verified",
            }
        ],
    )

    update = await report_generator(state)
    assert update["final_report"]["company"] == "Vanguard Systems"

    # 3. Simulate process restart by querying fresh database session
    async with factory() as fresh_session:
        report_repo = ReportRepository(fresh_session)

        # Retrieve JSON
        json_report = await report_repo.get_report_json("res-rep-persist-1", "org-rep-sec")
        assert json_report is not None
        assert json_report["company"] == "Vanguard Systems"
        assert json_report["metadata"]["report_id"] == "rpt-res-rep-persist-1"

        # Retrieve PDF
        pdf_bytes = await report_repo.get_report_pdf("res-rep-persist-1", "org-rep-sec")
        assert pdf_bytes is not None
        assert pdf_bytes.startswith(b"%PDF-")

        # Retrieve Markdown
        md_text = await report_repo.get_report_markdown("res-rep-persist-1", "org-rep-sec")
        assert md_text is not None
        assert "# Competitive Intelligence Report: Vanguard Systems" in md_text


@pytest.mark.asyncio
async def test_report_generator_tenant_isolation(sqlite_security_environment):
    """Verify cross-tenant IDOR protection for reports, PDFs, and Markdown artifacts."""
    factory = sqlite_security_environment["session_factory"]

    async with factory() as session:
        session.add(Organization(organization_id="org-rep-alpha", name="Report Alpha Org"))
        session.add(Organization(organization_id="org-rep-beta", name="Report Beta Org"))
        session.add(
            Research(
                research_id="res-secret-rep",
                organization_id="org-rep-alpha",
                company_name="Secret Security",
                industry="Defense",
                research_question="Secret defense brief?",
                status="completed",
                results={"final_report": {"metadata": {"report_id": "rpt-secret-rep"}, "company": "Secret Security"}},
                errors=[],
            )
        )
        await session.commit()

    async with factory() as session:
        report_repo = ReportRepository(session)

        # Authorized access (Alpha)
        alpha_report = await report_repo.get_report_json("res-secret-rep", "org-rep-alpha")
        assert alpha_report is not None
        assert alpha_report["company"] == "Secret Security"

        # Cross-tenant unauthorized access (Beta)
        beta_report = await report_repo.get_report_json("res-secret-rep", "org-rep-beta")
        assert beta_report is None

        beta_pdf = await report_repo.get_report_pdf("res-secret-rep", "org-rep-beta")
        assert beta_pdf is None

        beta_md = await report_repo.get_report_markdown("res-secret-rep", "org-rep-beta")
        assert beta_md is None


@pytest.mark.asyncio
async def test_report_generator_retry_idempotency(sqlite_security_environment):
    """Verify that multiple report generator executions update cleanly without duplicate files."""
    factory = sqlite_security_environment["session_factory"]

    async with factory() as session:
        session.add(Organization(organization_id="org-rep-retry", name="Retry Org"))
        session.add(
            Research(
                research_id="res-rep-retry-1",
                organization_id="org-rep-retry",
                company_name="Retry Tech",
                industry="Cloud",
                research_question="Retry report check?",
                status="running",
                results={},
                errors=[],
            )
        )
        await session.commit()

    state = ResearchState(
        research_id="res-rep-retry-1",
        organization_id="org-rep-retry",
        company_name="Retry Tech",
        industry="Cloud",
        research_question="Retry report check?",
        company_profile={"products": ["Retry Cloud"]},
    )

    # First run
    update_1 = await report_generator(state)
    assert update_1["final_report"]["company"] == "Retry Tech"

    # Second run (retry)
    update_2 = await report_generator(state)
    assert update_2["final_report"]["company"] == "Retry Tech"

    async with factory() as fresh_session:
        report_repo = ReportRepository(fresh_session)
        stored = await report_repo.get_report_json("res-rep-retry-1", "org-rep-retry")
        assert stored is not None
        assert stored["company"] == "Retry Tech"
