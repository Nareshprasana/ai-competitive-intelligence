"""Integration tests for the research API endpoints."""

from httpx import ASGITransport, AsyncClient

from app.main import app


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
