"""Integration tests for the Report API endpoints (Phase 2G).

Verifies:
- GET /api/v1/research/{research_id}/report (JSON report retrieval)
- GET /api/v1/research/{research_id}/report/pdf (PDF download, headers, attachment)
- GET /api/v1/research/{research_id}/report/markdown (Markdown format)
- Cross-tenant IDOR protection (404 on mismatched organization)
- Safe content-disposition and nosniff headers
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.identity import Organization
from app.models.research import Research
from app.repositories.report import ReportRepository
from app.security.auth import (
    AuthenticatedUser,
    OrganizationContext,
    Role,
    get_current_user,
    get_organization_context,
)
from tests.integration.test_sqlite_security import sqlite_security_environment


@pytest.fixture
def auth_context_alpha():
    user = AuthenticatedUser("user-alpha", "alpha@example.com", "sess-alpha", False)
    ctx = OrganizationContext(user, "org-alpha-rep", Role.ANALYST)

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_organization_context] = lambda: ctx
    yield ctx
    app.dependency_overrides.clear()


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


@pytest.mark.asyncio
async def test_report_api_endpoints_success(sqlite_security_environment, auth_context_alpha):
    """Verify JSON, PDF, and Markdown retrieval via API endpoints."""
    factory = sqlite_security_environment["session_factory"]

    # 1. Seed database with report and artifacts
    async with factory() as session:
        session.add(Organization(organization_id="org-alpha-rep", name="Alpha Rep Org"))
        research = Research(
            research_id="res-api-rep-1",
            organization_id="org-alpha-rep",
            company_name="CloudMatrix",
            industry="Cloud Computing",
            research_question="Market position?",
            status="completed",
            results={},
            errors=[],
        )
        session.add(research)
        await session.commit()

        # Save report using ReportRepository
        report_repo = ReportRepository(session)
        sample_report = {
            "metadata": {
                "report_id": "rpt-res-api-rep-1",
                "research_id": "res-api-rep-1",
                "organization_id": "org-alpha-rep",
                "target_company": "CloudMatrix",
            },
            "company": "CloudMatrix",
            "executive_summary": {"target_company_overview": "CloudMatrix is a high-performance cloud provider."},
        }
        sample_pdf = b"%PDF-1.4 Mock publication PDF content %%EOF"
        sample_md = "# Competitive Intelligence Report: CloudMatrix\n\nExecutive summary text."

        await report_repo.save_report(
            research_id="res-api-rep-1",
            organization_id="org-alpha-rep",
            report_data=sample_report,
            pdf_bytes=sample_pdf,
            markdown_text=sample_md,
        )
        await session.commit()

    async with await _client() as client:
        # 1. Test JSON Endpoint
        r_json = await client.get("/api/v1/research/res-api-rep-1/report")
        assert r_json.status_code == 200
        body = r_json.json()
        assert body["company"] == "CloudMatrix"
        assert body["metadata"]["report_id"] == "rpt-res-api-rep-1"

        # 2. Test PDF Download Endpoint
        r_pdf = await client.get("/api/v1/research/res-api-rep-1/report/pdf")
        assert r_pdf.status_code == 200
        assert r_pdf.headers["Content-Type"] == "application/pdf"
        assert 'attachment; filename="report-res-api-rep-1.pdf"' in r_pdf.headers["Content-Disposition"]
        assert r_pdf.headers.get("X-Content-Type-Options") == "nosniff"
        assert r_pdf.content.startswith(b"%PDF-")

        # 3. Test Markdown Endpoint
        r_md = await client.get("/api/v1/research/res-api-rep-1/report/markdown")
        assert r_md.status_code == 200
        assert "text/markdown" in r_md.headers["Content-Type"]
        assert "# Competitive Intelligence Report: CloudMatrix" in r_md.text


@pytest.mark.asyncio
async def test_report_api_cross_tenant_idor_protection(sqlite_security_environment):
    """Verify cross-tenant report access is denied (404 Not Found)."""
    factory = sqlite_security_environment["session_factory"]

    # Seed report belonging to org-alpha-rep
    async with factory() as session:
        session.add(Organization(organization_id="org-owner", name="Owner Org"))
        session.add(Organization(organization_id="org-attacker", name="Attacker Org"))
        research = Research(
            research_id="res-private-1",
            organization_id="org-owner",
            company_name="Private Dynamics",
            industry="AI",
            research_question="Top secret?",
            status="completed",
            results={"final_report": {"company": "Private Dynamics"}},
            errors=[],
        )
        session.add(research)
        await session.commit()

    # Authenticate as attacker from org-attacker
    attacker_user = AuthenticatedUser("attacker-user", "attacker@example.com", "sess-att", False)
    attacker_ctx = OrganizationContext(attacker_user, "org-attacker", Role.ANALYST)
    app.dependency_overrides[get_current_user] = lambda: attacker_user
    app.dependency_overrides[get_organization_context] = lambda: attacker_ctx

    try:
        async with await _client() as client:
            # Attempt to access owner's report
            r_json = await client.get("/api/v1/research/res-private-1/report")
            assert r_json.status_code == 404

            r_pdf = await client.get("/api/v1/research/res-private-1/report/pdf")
            assert r_pdf.status_code == 404

            r_md = await client.get("/api/v1/research/res-private-1/report/markdown")
            assert r_md.status_code == 404
    finally:
        app.dependency_overrides.clear()
