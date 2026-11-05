"""PostgreSQL-backed authentication and tenant-isolation regression tests."""

import os
import secrets
from datetime import datetime, timedelta, timezone
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
    from app.core.database import db
    from app.models.identity import AuthSession, RefreshToken
    from app.security.auth import hash_refresh_token

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
    async with db.session_factory() as session:
        old_record = await session.get(RefreshToken, hash_refresh_token(first_refresh))
        assert old_record is not None
        assert old_record.used_at is not None
        assert old_record.revoked_at is not None
        auth_session = await session.get(AuthSession, old_record.session_id)
        assert auth_session is not None and auth_session.revoked_at is not None

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


@pytest.mark.asyncio
async def test_csrf_and_origin_are_required_for_refresh(authenticated_client):
    client, email, password, _organization_id = authenticated_client
    origin = {"Origin": "http://localhost:3000"}
    login_response = await client.post(
        "/api/v1/auth/login",
        headers=origin,
        json={"email": email, "password": password},
    )
    csrf_token = login_response.json()["csrf_token"]

    missing_csrf = await client.post("/api/v1/auth/refresh", headers=origin)
    assert missing_csrf.status_code == 403
    invalid_origin = await client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "https://attacker.example", "X-CSRF-Token": csrf_token},
    )
    assert invalid_origin.status_code == 403


@pytest.mark.asyncio
async def test_logout_revokes_persisted_session(authenticated_client):
    from app.core.database import db
    from app.models.identity import AuthSession
    from app.security.auth import decode_access_token

    client, email, password, _organization_id = authenticated_client
    login_response = await client.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://localhost:3000"},
        json={"email": email, "password": password},
    )
    access_token = login_response.json()["access_token"]
    session_id = decode_access_token(access_token)["sid"]

    logout_response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_response.status_code == 204
    async with db.session_factory() as session:
        auth_session = await session.get(AuthSession, session_id)
        assert auth_session is not None and auth_session.revoked_at is not None
    rejected = await client.get(
        "/api/v1/auth/organizations",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert rejected.status_code == 401


@pytest.mark.asyncio
async def test_invitation_expiry_single_use_and_role_assignment(authenticated_client):
    from sqlalchemy import select

    from app.core.database import db
    from app.models.identity import (
        OrganizationInvitation,
        OrganizationMembership,
        User,
    )
    from app.security.auth import email_lookup_hash, hash_refresh_token

    client, creator_email, _password, organization_id = authenticated_client
    now = datetime.now(timezone.utc)
    invited_email = f"{uuid4().hex}@example.test"
    raw_token = secrets.token_urlsafe(48)
    expired_email = f"{uuid4().hex}@example.test"
    expired_token = secrets.token_urlsafe(48)
    async with db.session_factory() as session:
        creator = await session.scalar(
            select(User).where(User.email_lookup_hash == email_lookup_hash(creator_email))
        )
        assert creator is not None
        session.add_all(
            [
                OrganizationInvitation(
                    token_hash=hash_refresh_token(raw_token),
                    organization_id=organization_id,
                    email=invited_email,
                    email_lookup_hash=email_lookup_hash(invited_email),
                    role="analyst",
                    created_by=creator.user_id,
                    expires_at=now + timedelta(minutes=5),
                ),
                OrganizationInvitation(
                    token_hash=hash_refresh_token(expired_token),
                    organization_id=organization_id,
                    email=expired_email,
                    email_lookup_hash=email_lookup_hash(expired_email),
                    role="viewer",
                    created_by=creator.user_id,
                    expires_at=now - timedelta(minutes=1),
                ),
            ]
        )
        await session.commit()

    acceptance = {
        "email": invited_email,
        "password": "a-valid-long-password-for-tests",
        "token": raw_token,
    }
    accepted = await client.post("/api/v1/auth/invitations/accept", json=acceptance)
    assert accepted.status_code == 201
    repeated = await client.post("/api/v1/auth/invitations/accept", json=acceptance)
    assert repeated.status_code == 400
    expired = await client.post(
        "/api/v1/auth/invitations/accept",
        json={
            "email": expired_email,
            "password": "a-valid-long-password-for-tests",
            "token": expired_token,
        },
    )
    assert expired.status_code == 400

    async with db.session_factory() as session:
        invited_user = await session.scalar(
            select(User).where(
                User.email_lookup_hash == email_lookup_hash(invited_email)
            )
        )
        assert invited_user is not None
        membership = await session.get(
            OrganizationMembership, (invited_user.user_id, organization_id)
        )
        assert membership is not None and membership.role == "analyst"


@pytest.mark.asyncio
async def test_revoked_membership_denies_research_access(authenticated_client):
    from sqlalchemy import select

    from app.core.database import db
    from app.models.identity import OrganizationMembership, User
    from app.security.auth import email_lookup_hash

    client, email, password, organization_id = authenticated_client
    login_response = await client.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://localhost:3000"},
        json={"email": email, "password": password},
    )
    access_token = login_response.json()["access_token"]
    async with db.session_factory() as session:
        user = await session.scalar(
            select(User).where(User.email_lookup_hash == email_lookup_hash(email))
        )
        assert user is not None
        membership = await session.get(
            OrganizationMembership, (user.user_id, organization_id)
        )
        assert membership is not None
        membership.is_active = False
        await session.commit()

    response = await client.get(
        "/api/v1/research/nonexistent",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Organization-ID": organization_id,
        },
    )
    assert response.status_code == 403
