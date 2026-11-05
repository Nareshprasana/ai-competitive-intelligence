"""PostgreSQL-backed authentication and tenant-isolation regression tests."""

import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

TEST_DATABASE_URL = os.getenv("ACIS_TEST_DATABASE_URL") or ""
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="PostgreSQL tests require a dedicated ACIS_TEST_DATABASE_URL.",
)


@pytest.fixture
async def authenticated_client():
    from app.core.config import get_settings
    from app.core.database import db
    from app.main import create_app
    from app.models.identity import Organization, OrganizationMembership, User
    from app.security.auth import email_lookup_hash, hash_password

    get_settings.cache_clear()
    db._configured = False
    db._engine = None
    db._session_factory = None
    db._available = False
    db._checkpointer = None

    user_id = str(uuid4())
    organization_id = f"auth-test-{uuid4().hex[:12]}"
    email = f"{uuid4().hex}@example.test"
    password = "test-password-that-is-long-enough"
    async with db.session_factory() as session:
        session.add(Organization(organization_id=organization_id, name="Test Org"))
        session.add(
            User(
                user_id=user_id,
                email=email,
                email_lookup_hash=email_lookup_hash(email),
                password_hash=hash_password(password),
            )
        )
        session.add(
            OrganizationMembership(
                user_id=user_id,
                organization_id=organization_id,
                role="viewer",
            )
        )
        await session.commit()

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client, email, password, organization_id
    await db.dispose_checkpointer()
    await db.dispose()


@pytest.mark.asyncio
async def test_login_refresh_rotation_and_reuse_revokes_session(authenticated_client):
    client, email, password, organization_id = authenticated_client
    origin = {"Origin": "http://localhost:3000"}
    login_response = await client.post(
        "/api/v1/auth/login",
        headers=origin,
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    first_access = login_response.json()["access_token"]
    first_refresh = client.cookies.get("acis_refresh_token")
    first_csrf = login_response.json()["csrf_token"]
    assert first_refresh

    refreshed = await client.post(
        "/api/v1/auth/refresh",
        headers={**origin, "X-CSRF-Token": first_csrf},
    )
    assert refreshed.status_code == 200
    second_access = refreshed.json()["access_token"]
    assert second_access != first_access
    second_csrf = refreshed.json()["csrf_token"]

    replayed = await client.post(
        "/api/v1/auth/refresh",
        headers={**origin, "X-CSRF-Token": second_csrf},
        cookies={
            "acis_refresh_token": first_refresh,
            "acis_csrf_token": second_csrf,
        },
    )
    assert replayed.status_code == 401

    orgs = await client.get(
        "/api/v1/auth/organizations",
        headers={"Authorization": f"Bearer {second_access}"},
    )
    assert orgs.status_code == 401
    assert organization_id


@pytest.mark.asyncio
async def test_membership_is_required_and_viewers_cannot_create_research(
    authenticated_client,
):
    client, email, password, organization_id = authenticated_client
    response = await client.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://localhost:3000"},
        json={"email": email, "password": password},
    )
    token = response.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": organization_id,
    }

    denied = await client.post(
        "/api/v1/research",
        headers=headers,
        json={
            "company_name": "Example",
            "industry": "Software",
            "research_question": "Assess direct competitors",
        },
    )
    assert denied.status_code == 403

    wrong_tenant = await client.get(
        "/api/v1/research/not-owned",
        headers={**headers, "X-Organization-ID": "another-organization"},
    )
    assert wrong_tenant.status_code == 403

    organization_injection = await client.post(
        "/api/v1/research",
        headers=headers,
        json={
            "company_name": "Example",
            "industry": "Software",
            "research_question": "Assess direct competitors",
            "organization_id": "another-organization",
        },
    )
    assert organization_injection.status_code == 422
