"""Integration tests for the research API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.security.auth import (
    AuthenticatedUser,
    OrganizationContext,
    Role,
    get_current_user,
    get_organization_context,
)


@pytest.fixture(autouse=True)
def authenticated_test_context():
    async def current_user():
        return AuthenticatedUser("test-user", "test@example.com", "test-session", False)

    async def organization_context():
        return OrganizationContext(
            AuthenticatedUser("test-user", "test@example.com", "test-session", False),
            "org-dev",
            Role.ANALYST,
        )

    app.dependency_overrides[get_current_user] = current_user
    app.dependency_overrides[get_organization_context] = organization_context
    yield
    app.dependency_overrides.clear()


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


async def test_health_endpoint():
    async with await _client() as client:
        r = await client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "ai-competitive-intelligence"
    # Database must be reported honestly as unavailable (no PG configured).
    assert body["database"]["available"] is False
    assert body["database"]["configured"] is False
    # LLM must not be reported as configured (no key -> no credits consumed).
    assert body["llm"]["configured"] is False
    assert body["llm"]["provider"] == "openrouter"


async def test_submit_research_returns_id_and_results():
    async with await _client() as client:
        r = await client.post(
            "/api/v1/research",
            json={
                "company_name": "Acme Corp",
                "industry": "AI Software",
                "research_question": "Pricing vs competitors?",
            },
        )
    assert r.status_code == 201, r.text
    body = r.json()
    assert "research_id" in body
    assert body["status"] == "completed"
    assert body["results"] is not None
    assert body["results"]["final_report"] is not None
    assert body["results"]["errors"] == []
    return body["research_id"]


async def test_get_research_by_id():
    async with await _client() as client:
        post = await client.post(
            "/api/v1/research",
            json={
                "company_name": "Globex",
                "industry": "Biotech",
                "research_question": "Market share trends?",
            },
        )
        assert post.status_code == 201
        rid = post.json()["research_id"]
        r = await client.get(f"/api/v1/research/{rid}")
    assert r.status_code == 200
    body = r.json()
    assert body["research_id"] == rid
    assert body["status"] == "completed"
    assert body["results"]["company_name"] == "Globex"


async def test_request_validation_rejects_invalid_input():
    async with await _client() as client:
        # Missing required fields.
        r = await client.post("/api/v1/research", json={"industry": "x"})
        assert r.status_code == 422
        # Empty company name.
        r = await client.post(
            "/api/v1/research",
            json={"company_name": "   ", "industry": "x", "research_question": "q" * 10},
        )
        assert r.status_code == 422
        # Question too short.
        r = await client.post(
            "/api/v1/research",
            json={"company_name": "c", "industry": "i", "research_question": "ab"},
        )
        assert r.status_code == 422


async def test_get_research_not_found():
    async with await _client() as client:
        r = await client.get("/api/v1/research/no-such-id")
    assert r.status_code == 404


async def test_list_research_empty_and_populated():
    async with await _client() as client:
        r = await client.get("/api/v1/research")
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)

        post = await client.post(
            "/api/v1/research",
            json={
                "company_name": "ListTest Co",
                "industry": "Cloud",
                "research_question": "What is their competitive strategy?",
            },
        )
        assert post.status_code == 201
        created_id = post.json()["research_id"]

        r2 = await client.get("/api/v1/research")
        assert r2.status_code == 200
        ids = [item["research_id"] for item in r2.json()]
        assert created_id in ids


async def test_review_evidence_endpoint():
    async with await _client() as client:
        post = await client.post(
            "/api/v1/research",
            json={
                "company_name": "EvidenceReview Co",
                "industry": "FinTech",
                "research_question": "Evidence review testing?",
            },
        )
        assert post.status_code == 201
        rid = post.json()["research_id"]

        get_res = await client.get(f"/api/v1/research/{rid}")
        results = get_res.json()["results"]
        ev_items = results.get("evidence", [])
        if ev_items:
            ev_id = ev_items[0]["evidence_id"]
            orig_status = ev_items[0].get("verification_status")
            orig_conf = ev_items[0].get("confidence")

            # 1. Submit human approval
            review_resp = await client.post(
                f"/api/v1/research/{rid}/evidence/{ev_id}/review",
                json={
                    "decision": "approved",
                    "analyst_notes": "Audited and confirmed by Lead Analyst.",
                    "override_confidence": 0.98,
                },
            )
            assert review_resp.status_code == 200
            review_data = review_resp.json()
            assert review_data["evidence_id"] == ev_id
            assert review_data["verification_status"] == "approved"
            assert review_data["machine_verification_status"] == orig_status
            assert review_data["machine_confidence"] == orig_conf
            assert review_data["human_review"]["decision"] == "approved"
            assert review_data["human_review"]["reviewed_by"] == "test@example.com"

            # 2. Retrieve review audit history for this evidence item
            audit_resp = await client.get(
                f"/api/v1/research/{rid}/evidence/{ev_id}/reviews"
            )
            assert audit_resp.status_code == 200
            audit_data = audit_resp.json()
            assert audit_data["evidence_id"] == ev_id
            assert audit_data["machine_verification_status"] == orig_status
            assert len(audit_data["reviews"]) >= 1
            assert audit_data["reviews"][-1]["decision"] == "approved"

            # 3. Retrieve all review logs for research run
            all_audit = await client.get(
                f"/api/v1/research/{rid}/evidence/reviews"
            )
            assert all_audit.status_code == 200
            assert all_audit.json()["review_count"] >= 1


async def test_report_endpoints_fallback_and_artifacts():
    async with await _client() as client:
        post = await client.post(
            "/api/v1/research",
            json={
                "company_name": "ReportArtifacts Co",
                "industry": "Enterprise Security",
                "research_question": "Report artifact validation?",
            },
        )
        assert post.status_code == 201
        rid = post.json()["research_id"]

        # Structured Report JSON
        r_json = await client.get(f"/api/v1/research/{rid}/report")
        assert r_json.status_code == 200
        data = r_json.json()
        assert "company" in data or "sections" in data or "metadata" in data

        # PDF Artifact Download
        r_pdf = await client.get(f"/api/v1/research/{rid}/report/pdf")
        assert r_pdf.status_code == 200
        assert r_pdf.headers["content-type"] == "application/pdf"
        assert "attachment;" in r_pdf.headers["content-disposition"]
        assert r_pdf.content.startswith(b"%PDF-")

        # Markdown Export
        r_md = await client.get(f"/api/v1/research/{rid}/report/markdown")
        assert r_md.status_code == 200
        assert "text/markdown" in r_md.headers["content-type"]
        assert "Competitive Intelligence Report" in r_md.text
