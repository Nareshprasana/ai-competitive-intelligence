"""Integration tests for PostgreSQL-backed research API.

Requires DATABASE_URL to point at a live PostgreSQL instance. Creates a fresh
FastAPI app with the database configured so research records persist across
requests (survive a simulated backend restart).
"""

import asyncio
import os

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure the database is configured before creating the app.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://acis_app:acis_dev_password@127.0.0.1:5432/acis_db",
)


def _make_app():
    from app.core.config import get_settings
    from app.core.database import db
    from app.main import create_app

    # Force re-configuration of settings and the database manager with the
    # test URL (get_settings is lru_cached).
    get_settings.cache_clear()
    db._configured = False
    db._engine = None
    db._session_factory = None
    db._available = False
    db._checkpointer = None
    return create_app()


@pytest.fixture
async def client():
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest.mark.asyncio
async def test_health_reports_database_available(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["database"]["available"] is True
    assert body["database"]["configured"] is True


@pytest.mark.asyncio
async def test_submit_and_retrieve_research_persisted(client):
    """Submit research, then retrieve it (simulating a backend restart)."""
    # Submit.
    post = await client.post(
        "/api/v1/research",
        json={
            "company_name": "PersistCo",
            "industry": "Biotech",
            "research_question": "Market share trends?",
        },
    )
    assert post.status_code == 201, post.text
    body = post.json()
    research_id = body["research_id"]
    assert body["status"] == "completed"
    assert body["results"]["final_report"]["company"] == "PersistCo"

    # Retrieve with the SAME client (new request = simulated restart).
    r = await client.get(f"/api/v1/research/{research_id}")
    assert r.status_code == 200
    fetched = r.json()
    assert fetched["research_id"] == research_id
    assert fetched["status"] == "completed"
    assert fetched["results"]["company_name"] == "PersistCo"
    assert fetched["results"]["organization_id"] == "org-dev"
    assert len(fetched["results"]["execution_metadata"]) == 8


@pytest.mark.asyncio
async def test_cross_organization_isolation_at_api(client):
    """A GET for a research record must not leak across organizations."""
    post = await client.post(
        "/api/v1/research",
        json={
            "company_name": "OrgA-Co",
            "industry": "AI",
            "research_question": "What is the market position?",
        },
    )
    assert post.status_code == 201
    research_id = post.json()["research_id"]

    # Same organization (default org-dev) can retrieve.
    r = await client.get(f"/api/v1/research/{research_id}")
    assert r.status_code == 200

    # Direct DB check: a different organization cannot see it.
    from app.core.database import db
    from app.repositories.research import ResearchRepository

    async for session in db.get_session():
        repo = ResearchRepository(session)
        fetched = await repo.get_by_id(research_id, "org-other")
        break
    assert fetched is None


@pytest.mark.asyncio
async def test_get_research_not_found(client):
    r = await client.get("/api/v1/research/does-not-exist-persist")
    assert r.status_code == 404
