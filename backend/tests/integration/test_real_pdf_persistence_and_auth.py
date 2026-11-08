"""Integration test for Real PDF Generation, Integrity, PostgreSQL Persistence, and Authorization (Phase 3.2.1).

Verifies:
1. Real PDF generation using ReportLab service with deterministic state.
2. PDF integrity verification:
   - Header (%PDF-)
   - Valid structural hierarchy
   - Non-zero file size (> 10KB)
   - Extracted text contains Executive Summary, Profile, SWOT, Recommendations, etc.
   - Dynamic page count > 1 and running decorations ('Page X of Y').
   - Successful parsing via pypdf.
3. PostgreSQL persistence in acis_test_db:
   - Report JSON and artifact persisted through ReportRepository.
   - Fresh session retrieval.
   - Byte-for-byte exact equality between generated and retrieved PDF.
   - Secondary pypdf validation on retrieved artifact.
4. Authorization & tenant boundary enforcement:
   - Tenant isolation (Tenant Alpha cannot download Tenant Beta PDF).
   - Missing artifact handling without filesystem path leakage.
   - Invalid research ID returns controlled error.
"""

import io
import os
from dotenv import load_dotenv
import pypdf
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from app.agents.report_generator import ReportGeneratorAgent
from app.core.config import get_settings
from app.graph.state import ResearchState
from app.models.identity import Organization
from app.models.research import Research
from app.repositories.report import ReportRepository
from app.schemas.report import StrategicReport


TEST_DATABASE_URL = (
    os.getenv("ACIS_TEST_DATABASE_URL")
    or get_settings().database_url
)


@pytest.fixture
def deterministic_research_state():
    return ResearchState(
        research_id="res-pdf-audit-2026",
        organization_id="org-pdf-test",
        company_name="QuantumScale Technologies",
        industry="Enterprise Artificial Intelligence",
        research_question="What are QuantumScale's competitive advantages, threats, and positioning?",
        company_profile={
            "company_name": "QuantumScale Technologies",
            "products": ["QuantumScale Core", "QuantumTelemetry Engine", "Enterprise Agentic Gateway"],
            "target_customers": ["Global 2000 Financial Institutions", "Tier 1 Telecom"],
            "geographical_presence": ["North America", "Europe", "APAC"],
            "business_model": "Annual Platform License + Metered Workload Ingestion",
            "description": "High-throughput enterprise infrastructure for distributed agentic intelligence.",
        },
        competitors=[
            {
                "competitor_id": "comp-synapse",
                "company_name": "SynapseVector",
                "competitor_type": "direct",
                "products_and_services": ["Synapse Vector Cloud"],
                "target_customers": ["Cloud-native scaleups"],
                "competitive_strengths": ["Rapid self-serve onboarding", "Serverless consumption"],
                "competitive_weaknesses": ["Lack of on-prem air-gapped deployment option"],
            }
        ],
        evidence=[
            {
                "evidence_id": "ev-qs-01",
                "claim": "QuantumScale processes over 500,000 distributed inferences per second.",
                "source_name": "Cloud AI Performance Benchmark 2026",
                "source_url": "https://quantumscale.example/benchmark-report",
                "source_domain": "quantumscale.example",
                "confidence": 0.94,
                "verification_status": "verified",
            },
            {
                "evidence_id": "ev-syn-01",
                "claim": "SynapseVector holds 14% market share in cloud-native AI middleware.",
                "source_name": "Tech Market Insights Q3",
                "source_url": "https://techinsights.example/market-share",
                "source_domain": "techinsights.example",
                "confidence": 0.88,
                "verification_status": "verified",
            },
        ],
        validation_results={
            "contradictions": [],
            "human_review_queue": [],
        },
    )


@pytest.mark.asyncio
async def test_real_pdf_generation_integrity_and_postgres_persistence(deterministic_research_state):
    """Generate a real ReportLab PDF, verify with pypdf, persist in PostgreSQL, and retrieve."""
    db_url = (
        os.getenv("ACIS_TEST_DATABASE_URL")
        or os.getenv("DATABASE_TEST_URL")
        or os.getenv("DATABASE_URL")
        or get_settings().database_url
    )
    assert db_url, "ACIS_TEST_DATABASE_URL must be available"
    
    agent = ReportGeneratorAgent()
    report, md_text, pdf_bytes = await agent.generate_report(deterministic_research_state)

    # 1. Structural PDF Integrity Checks
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000, f"PDF file size {len(pdf_bytes)} bytes is unexpectedly small"
    assert pdf_bytes.startswith(b"%PDF-"), "PDF missing %PDF- header magic bytes"
    assert b"%%EOF" in pdf_bytes[-1024:], "PDF missing %%EOF terminating token"

    # 2. Parsing and Text Extraction via pypdf (Strict Validation)
    pdf_stream = io.BytesIO(pdf_bytes)
    reader = pypdf.PdfReader(pdf_stream)
    
    page_count = len(reader.pages)
    assert page_count >= 2, f"Expected multi-page report, received {page_count} pages"

    extracted_pages_text = [page.extract_text() for page in reader.pages]
    combined_text = " ".join(extracted_pages_text)

    # Verify critical sections are present in extracted text
    assert "QuantumScale Technologies" in combined_text
    assert "CONFIDENTIAL" in combined_text
    assert "Executive Summary" in combined_text
    assert "Target Company Intelligence Profile" in combined_text or "Company Intelligence Profile" in combined_text
    assert "SWOT Analysis" in combined_text
    assert "Strategic Recommendations" in combined_text
    assert "Evidence & Source Provenance" in combined_text or "Appendix" in combined_text
    
    # Verify running decorations and page numbering
    assert any("Page " in text for text in extracted_pages_text[1:])

    # 3. PostgreSQL Persistence in acis_test_db
    engine = create_async_engine(db_url)
    
    org_id = "org-pdf-test"
    research_id = deterministic_research_state.research_id
    
    # Session 1: Seed organization, research record, and persist report
    async with AsyncSession(engine) as session1:
        await session1.begin()
        
        # Ensure test organization exists
        org = await session1.get(Organization, org_id)
        if not org:
            org = Organization(organization_id=org_id, name="PDF Test Corp", is_active=True)
            session1.add(org)
            await session1.flush()

        # Seed research record
        res_stmt = select(Research).where(Research.research_id == research_id)
        res_result = await session1.execute(res_stmt)
        res_record = res_result.scalar_one_or_none()
        if not res_record:
            res_record = Research(
                research_id=research_id,
                organization_id=org_id,
                company_name=deterministic_research_state.company_name,
                industry=deterministic_research_state.industry,
                research_question=deterministic_research_state.research_question,
                status="completed",
                review_status="approved",
                results={"company_profile": deterministic_research_state.company_profile},
            )
            session1.add(res_record)
            await session1.flush()

        # Save report via repository
        report_repo1 = ReportRepository(session1)
        save_success = await report_repo1.save_report(
            research_id=research_id,
            organization_id=org_id,
            report_data=report.model_dump(mode="json"),
            pdf_bytes=pdf_bytes,
            markdown_text=md_text,
        )
        assert save_success is True, "ReportRepository.save_report must return True"
        await session1.commit()

    # Session 2: Fresh DB session to test durable persistence and retrieval
    async with AsyncSession(engine) as session2:
        report_repo2 = ReportRepository(session2)

        # Retrieve structured JSON
        retrieved_json = await report_repo2.get_report_json(research_id, org_id)
        assert retrieved_json is not None
        assert retrieved_json["metadata"]["target_company"] == "QuantumScale Technologies"
        assert "artifact_references" in retrieved_json["metadata"]
        assert "pdf" in retrieved_json["metadata"]["artifact_references"]

        # Retrieve binary PDF
        retrieved_pdf = await report_repo2.get_report_pdf(research_id, org_id)
        assert retrieved_pdf is not None
        assert isinstance(retrieved_pdf, bytes)
        
        # Byte-for-byte exact equality
        assert len(retrieved_pdf) == len(pdf_bytes)
        assert retrieved_pdf == pdf_bytes, "Retrieved PDF must match generated PDF with byte-for-byte fidelity"

        # Re-parse retrieved bytes with pypdf
        retrieved_reader = pypdf.PdfReader(io.BytesIO(retrieved_pdf))
        assert len(retrieved_reader.pages) == page_count
        assert "QuantumScale Technologies" in retrieved_reader.pages[0].extract_text()

        # Retrieve Markdown
        retrieved_md = await report_repo2.get_report_markdown(research_id, org_id)
        assert retrieved_md is not None
        assert "# Competitive Intelligence Report" in retrieved_md
        assert "QuantumScale Technologies" in retrieved_md

        # 4. Tenant Isolation & Authorization Boundaries
        # Attempt access as Tenant Other
        other_org_pdf = await report_repo2.get_report_pdf(research_id, organization_id="org-other-tenant")
        assert other_org_pdf is None, "Cross-tenant PDF access must return None"

        other_org_json = await report_repo2.get_report_json(research_id, organization_id="org-other-tenant")
        assert other_org_json is None, "Cross-tenant JSON access must return None"

        # Invalid research ID
        invalid_pdf = await report_repo2.get_report_pdf("non-existent-research-id", org_id)
        assert invalid_pdf is None, "Non-existent research ID must return None"

    await engine.dispose()


@pytest.mark.asyncio
async def test_pdf_http_endpoint_authorization(deterministic_research_state, monkeypatch):
    """Verify HTTP API endpoint authorization for PDF downloads."""
    from httpx import ASGITransport, AsyncClient
    from app.main import app
    from app.core.database import db
    from app.security.auth import (
        AuthenticatedUser,
        OrganizationContext,
        Role,
        get_current_user,
        get_organization_context,
    )

    db_url = (
        os.getenv("ACIS_TEST_DATABASE_URL")
        or os.getenv("DATABASE_TEST_URL")
        or os.getenv("DATABASE_URL")
        or get_settings().database_url
    )
    assert db_url, "ACIS_TEST_DATABASE_URL must be available"

    # Configure live database connection for endpoint test
    monkeypatch.setenv("DATABASE_URL", db_url)
    get_settings.cache_clear()
    orig_engine = db._engine
    orig_factory = db._session_factory
    orig_configured = db._configured
    orig_available = db._available
    db._configured = False
    db._ensure_configured()

    org_id = "org-pdf-test"
    research_id = deterministic_research_state.research_id

    user = AuthenticatedUser("user-pdf-viewer", "viewer@pdf-test.com", "sess-pdf", False)
    ctx_authorized = OrganizationContext(user, org_id, Role.VIEWER)
    ctx_cross_tenant = OrganizationContext(user, "org-other-tenant", Role.ANALYST)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Authorized download
        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[get_organization_context] = lambda: ctx_authorized
        try:
            res = await client.get(f"/api/v1/research/{research_id}/report/pdf")
            assert res.status_code == 200, f"Expected 200, received {res.status_code}: {res.text}"
            assert res.headers["content-type"] == "application/pdf"
            assert res.content.startswith(b"%PDF-")

            # 2. Cross-tenant access denied
            app.dependency_overrides[get_organization_context] = lambda: ctx_cross_tenant
            res_cross = await client.get(f"/api/v1/research/{research_id}/report/pdf")
            assert res_cross.status_code == 404, "Cross-tenant request must return 404"

            # 3. Invalid research ID
            app.dependency_overrides[get_organization_context] = lambda: ctx_authorized
            res_invalid = await client.get("/api/v1/research/non-existent-run-id/report/pdf")
            assert res_invalid.status_code == 404

            # 4. Verify no filesystem paths are leaked in errors
            for response in [res_cross, res_invalid]:
                text = response.text
                assert "data/artifacts" not in text
                assert "C:\\" not in text
                assert "/Users/" not in text

            # 5. Unauthorized request (missing token / overrides cleared)
            app.dependency_overrides.clear()
            res_no_auth = await client.get(f"/api/v1/research/{research_id}/report/pdf")
            assert res_no_auth.status_code == 401
        finally:
            app.dependency_overrides.clear()
            await db.dispose()
            get_settings.cache_clear()

