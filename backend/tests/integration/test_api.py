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
        ev_items = results.get("validated_evidence", {}).get("evidence_items", [])
        if ev_items:
            ev_id = ev_items[0]["evidence_id"]
            review_resp = await client.post(
                f"/api/v1/research/{rid}/evidence/{ev_id}/review",
                json={
                    "status": "rejected",
                    "notes": "Rejected by senior reviewer due to stale data source",
                },
            )
            assert review_resp.status_code == 200
            review_data = review_resp.json()
            assert review_data["evidence_id"] == ev_id
            assert review_data["status"] == "rejected"
            assert "senior reviewer" in review_data["notes"]
            assert review_data["reviewed_by"] == "test-user"
