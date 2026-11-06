"""Portable database-backed security tests using an isolated SQLite database.

These tests exercise ORM encryption, repository ownership filters, and
authentication flows. The SQLite rate-limit adapter is test-only and does not
verify PostgreSQL upsert or cross-process behavior.
"""

import base64
import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
import jwt
from fastapi import HTTPException, Request
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, inspect as sa_inspect, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session as SyncSession, attributes

from app.core.config import get_settings
from app.core.database import Base, db, get_db_session
from app.models.company import CompanyProfile, EvidenceClaim
from app.models.competitor import Competitor, CompetitorEvidence
from app.models.identity import (
    AuditEvent,
    AuthSession,
    Organization,
    OrganizationMembership,
    RateLimitBucket,
    RefreshToken,
    User,
)
from app.repositories.research import ResearchRepository
from app.security.auth import (
    AuthenticatedUser,
    Permission,
    Role,
    email_lookup_hash,
    get_organization_context,
    hash_password,
    hash_refresh_token,
    require_permission,
    require_platform_admin,
    verify_password,
)


async def _sqlite_rate_limit(
    request: Request,
    session,
    *,
    identity: str,
    limit: int,
) -> None:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=get_settings().rate_limit_window_seconds)
    bucket_key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    bucket = await session.get(RateLimitBucket, bucket_key)
    if bucket is None:
        count = 1
        session.add(
            RateLimitBucket(
                bucket_key=bucket_key,
                window_start=now,
                request_count=count,
            )
        )
    else:
        previous_window = bucket.window_start
        if previous_window.tzinfo is None:
            previous_window = previous_window.replace(tzinfo=timezone.utc)
        if previous_window < window_start:
            bucket.window_start = now
            bucket.request_count = 1
        else:
            bucket.request_count += 1
        count = bucket.request_count
    await session.commit()
    if count > limit:
        raise HTTPException(
            status_code=429,
            detail="Request rate limit exceeded.",
            headers={"Retry-After": str(get_settings().rate_limit_window_seconds)},
        )


@pytest_asyncio.fixture
async def sqlite_security_environment(tmp_path, monkeypatch):
    """Create a fresh SQLite DB and ephemeral test keys for one test."""
    aes_key_id = f"sqlite-test-{uuid4().hex[:12]}"
    encryption_keys = json.dumps(
        {
            aes_key_id: base64.b64encode(secrets.token_bytes(32)).decode("ascii"),
        }
    )
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("DATA_ENCRYPTION_KEYS", encryption_keys)
    monkeypatch.setenv("DATA_ENCRYPTION_ACTIVE_KEY_ID", aes_key_id)
    monkeypatch.setenv("AUTH_JWT_SIGNING_KEY", secrets.token_hex(32))
    monkeypatch.setenv("AUTH_EMAIL_LOOKUP_KEY", secrets.token_hex(32))
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv(
        "BACKEND_CORS_ORIGINS",
        json.dumps(["http://localhost:3000"]),
    )
    monkeypatch.setenv("AUTH_RATE_LIMIT_REQUESTS", "1000")
    monkeypatch.setenv("API_RATE_LIMIT_REQUESTS", "1000")

    get_settings.cache_clear()
    database_path = tmp_path / "acis-security-test.sqlite3"
    engine = create_async_engine(
        URL.create("sqlite+aiosqlite", database=str(database_path)),
        pool_pre_ping=True,
    )

    def restore_utc_timezone(_session, instance):
        state = sa_inspect(instance)
        for attribute in state.mapper.column_attrs:
            value = state.dict.get(attribute.key)
            if isinstance(value, datetime) and value.tzinfo is None:
                attributes.set_committed_value(
                    instance,
                    attribute.key,
                    value.replace(tzinfo=timezone.utc),
                )

    event.listen(SyncSession, "loaded_as_persistent", restore_utc_timezone)

    @event.listens_for(engine.sync_engine, "connect")
    def enable_sqlite_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    monkeypatch.setattr(db, "_engine", engine)
    monkeypatch.setattr(db, "_session_factory", session_factory)
    monkeypatch.setattr(db, "_configured", True)
    monkeypatch.setattr(db, "_available", True)
    monkeypatch.setattr(db, "_checkpointer", None)

    import app.api.v1.endpoints.auth as auth_endpoints
    import app.main as main
    import app.security.auth as security_auth

    monkeypatch.setattr(main, "enforce_rate_limit", _sqlite_rate_limit)
    monkeypatch.setattr(auth_endpoints, "enforce_rate_limit", _sqlite_rate_limit)
    monkeypatch.setattr(security_auth, "enforce_rate_limit", _sqlite_rate_limit)

    async def override_db_session():
        async with session_factory() as session:
            yield session

    def create_test_app():
        application = main.create_app()
        application.dependency_overrides[get_db_session] = override_db_session
        return application

    environment = {
        "engine": engine,
        "session_factory": session_factory,
        "create_app": create_test_app,
        "aes_key_id": aes_key_id,
    }
    try:
        yield environment
    finally:
        event.remove(SyncSession, "loaded_as_persistent", restore_utc_timezone)
        await engine.dispose()
        get_settings.cache_clear()


@pytest_asyncio.fixture
async def sqlite_client(sqlite_security_environment):
    app = sqlite_security_environment["create_app"]()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client


async def _create_organizations(session_factory, *organization_ids: str) -> None:
    async with session_factory() as session:
        session.add_all(
            Organization(organization_id=org_id, name=org_id)
            for org_id in organization_ids
        )
        await session.commit()


async def _create_user(
    session_factory,
    *,
    user_id: str,
    email: str,
    role: str,
    organization_id: str,
    is_platform_admin: bool = False,
    is_active: bool = True,
) -> None:
    async with session_factory() as session:
        session.add(
            User(
                user_id=user_id,
                email=email,
                email_lookup_hash=email_lookup_hash(email),
                password_hash=hash_password("test-password-with-sufficient-length"),
                is_active=is_active,
                is_platform_admin=is_platform_admin,
            )
        )
        session.add(
            OrganizationMembership(
                user_id=user_id,
                organization_id=organization_id,
                role=role,
            )
        )
        await session.commit()


@pytest.mark.asyncio
async def test_sqlite_research_company_competitor_and_evidence_round_trip(
    sqlite_security_environment,
):
    factory = sqlite_security_environment["session_factory"]
    await _create_organizations(factory, "org-a", "org-b")
    research_id = f"research-{uuid4().hex}"
    evidence_secret = "private evidence source snippet"

    async with factory() as session:
        repository = ResearchRepository(session)
        created = await repository.create(
            research_id=research_id,
            organization_id="org-a",
            company_name="Acme Confidential",
            industry="Private Software",
            research_question="Assess confidential market position",
            status="completed",
            results={"private_result": "sensitive research payload"},
            errors=[],
        )
        assert created["company_name"] == "Acme Confidential"
        await session.commit()

        company = CompanyProfile(
            company_id="company-a",
            organization_id="org-a",
            company_name="Acme",
            industry="Software",
            profile={"private": "company profile"},
            source_references=[{"url": "https://example.test/company"}],
        )
        session.add(company)
        await session.flush()
        session.add(
            EvidenceClaim(
                evidence_id="evidence-a",
                company_profile_id=company.id,
                organization_id="org-a",
                claim="A private supported claim",
                source_url="https://example.test/source",
                source_domain="example.test",
                evidence_type="company",
                confidence=0.9,
                verification_status="verified",
                raw_snippet=evidence_secret,
            )
        )
        competitor = Competitor(
            competitor_id="competitor-a",
            research_id=research_id,
            organization_id="org-a",
            company_name="Rival",
            company_key="rival",
            competitor_type="direct",
            company_description="Private competitor description",
            profile={"private": "competitor profile"},
            qualification_score=0.8,
            confidence=0.9,
            verification_status="verified",
            source_references=[{"url": "https://example.test/rival"}],
        )
        session.add(competitor)
        await session.flush()
        session.add(
            CompetitorEvidence(
                evidence_id="competitor-evidence-a",
                competitor_id="competitor-a",
                organization_id="org-a",
                research_id=research_id,
                claim="A private competitor claim",
                source_url="https://example.test/rival-source",
                source_domain="example.test",
                evidence_type="independent",
                confidence=0.85,
                verification_status="verified",
                raw_snippet=evidence_secret,
            )
        )
        await session.commit()

        fetched = await repository.get_by_id(research_id, "org-a")
        assert fetched["results"] == {"private_result": "sensitive research payload"}
        assert await repository.get_by_id(research_id, "org-b") is None

        fetched_company = await session.scalar(
            select(CompanyProfile).where(CompanyProfile.company_id == "company-a")
        )
        fetched_evidence = await session.scalar(
            select(EvidenceClaim).where(EvidenceClaim.evidence_id == "evidence-a")
        )
        fetched_competitor = await session.scalar(
            select(Competitor).where(Competitor.competitor_id == "competitor-a")
        )
        fetched_competitor_evidence = await session.scalar(
            select(CompetitorEvidence).where(
                CompetitorEvidence.evidence_id == "competitor-evidence-a"
            )
        )
        assert fetched_company.profile == {"private": "company profile"}
        assert fetched_evidence.raw_snippet == evidence_secret
        assert fetched_competitor.profile == {"private": "competitor profile"}
        assert fetched_competitor_evidence.raw_snippet == evidence_secret

        raw_rows = (
            await session.execute(
                text(
                    "SELECT company_name, results FROM researches "
                    "WHERE research_id = :research_id"
                ),
                {"research_id": research_id},
            )
        ).one()
        raw_evidence = (
            await session.execute(
                text(
                    "SELECT claim, raw_snippet FROM evidence_claims "
                    "WHERE evidence_id = 'evidence-a'"
                )
            )
        ).one()
        raw_company_profile = (
            await session.execute(
                text(
                    "SELECT profile, source_references FROM company_profiles "
                    "WHERE company_id = 'company-a'"
                )
            )
        ).one()
        raw_competitor = (
            await session.execute(
                text(
                    "SELECT company_description, profile, source_references "
                    "FROM competitors WHERE competitor_id = 'competitor-a'"
                )
            )
        ).one()
        raw_competitor_evidence = (
            await session.execute(
                text(
                    "SELECT claim, raw_snippet FROM competitor_evidence "
                    "WHERE evidence_id = 'competitor-evidence-a'"
                )
            )
        ).one()
        assert "Acme Confidential" not in repr(raw_rows)
        assert "sensitive research payload" not in repr(raw_rows)
        assert evidence_secret not in repr(raw_evidence)
        assert "company profile" not in repr(raw_company_profile)
        assert "competitor profile" not in repr(raw_competitor)
        assert "Private competitor description" not in repr(raw_competitor)
        assert evidence_secret not in repr(raw_competitor_evidence)
        assert all(
            value.startswith(f"acis:v1:{sqlite_security_environment['aes_key_id']}:")
            for value in (
                raw_evidence.claim,
                raw_evidence.raw_snippet,
                raw_company_profile.profile,
                raw_company_profile.source_references,
                raw_competitor.company_description,
                raw_competitor.profile,
                raw_competitor.source_references,
                raw_competitor_evidence.claim,
                raw_competitor_evidence.raw_snippet,
            )
        )


@pytest.mark.asyncio
async def test_sqlite_login_refresh_replay_revocation_and_logout(
    sqlite_security_environment, sqlite_client
):
    factory = sqlite_security_environment["session_factory"]
    await _create_organizations(factory, "org-a", "org-b")
    await _create_user(
        factory,
        user_id="viewer-a",
        email="viewer@example.test",
        role=Role.VIEWER.value,
        organization_id="org-a",
    )

    origin = {"Origin": "http://localhost:3000"}
    login = await sqlite_client.post(
        "/api/v1/auth/login",
        headers=origin,
        json={
            "email": "viewer@example.test",
            "password": "test-password-with-sufficient-length",
        },
    )
    assert login.status_code == 200
    access_token = login.json()["access_token"]
    first_refresh = sqlite_client.cookies.get("acis_refresh_token")
    first_csrf = login.json()["csrf_token"]
    assert first_refresh
    assert "httponly" in login.headers.get("set-cookie", "").lower()

    async with factory() as session:
        user = await session.get(User, "viewer-a")
        assert user.password_hash.startswith("$argon2id$")
        assert verify_password(
            user.password_hash,
            "test-password-with-sufficient-length",
        )
        stored_hashes = list(await session.scalars(select(RefreshToken.token_hash)))
        assert hash_refresh_token(first_refresh) in stored_hashes
        assert first_refresh not in stored_hashes

    expired_claims = jwt.decode(
        access_token,
        options={"verify_signature": False, "verify_exp": False},
    )
    expired_claims["exp"] = int(datetime.now(timezone.utc).timestamp()) - 1
    expired_token = jwt.encode(
        expired_claims,
        get_settings().auth_jwt_signing_key.get_secret_value(),
        algorithm="HS256",
    )
    expired = await sqlite_client.get(
        "/api/v1/auth/organizations",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert expired.status_code == 401

    invalid_csrf = await sqlite_client.post(
        "/api/v1/auth/refresh",
        headers={**origin, "X-CSRF-Token": "incorrect"},
    )
    assert invalid_csrf.status_code == 403

    rotated = await sqlite_client.post(
        "/api/v1/auth/refresh",
        headers={**origin, "X-CSRF-Token": first_csrf},
    )
    assert rotated.status_code == 200
    second_refresh = sqlite_client.cookies.get("acis_refresh_token")
    second_csrf = rotated.json()["csrf_token"]
    assert second_refresh and second_refresh != first_refresh

    replay = await sqlite_client.post(
        "/api/v1/auth/refresh",
        headers={**origin, "X-CSRF-Token": second_csrf},
        cookies={
            "acis_refresh_token": first_refresh,
            "acis_csrf_token": second_csrf,
        },
    )
    assert replay.status_code == 401
    async with factory() as session:
        auth_session = await session.scalar(select(AuthSession))
        token_records = list(await session.scalars(select(RefreshToken)))
        assert auth_session.revoked_at is not None
        assert token_records and all(token.revoked_at is not None for token in token_records)

    rejected = await sqlite_client.get(
        "/api/v1/auth/organizations",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert rejected.status_code == 401

    second_login = await sqlite_client.post(
        "/api/v1/auth/login",
        headers=origin,
        json={
            "email": "viewer@example.test",
            "password": "test-password-with-sufficient-length",
        },
    )
    assert second_login.status_code == 200
    logout = await sqlite_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {second_login.json()['access_token']}"},
    )
    assert logout.status_code == 204
    after_logout = await sqlite_client.get(
        "/api/v1/auth/organizations",
        headers={"Authorization": f"Bearer {second_login.json()['access_token']}"},
    )
    assert after_logout.status_code == 401

    async with factory() as session:
        audit_events = list(await session.scalars(select(AuditEvent)))
        audit_fields = list(
            await session.execute(
                select(
                    AuditEvent.action,
                    AuditEvent.resource_type,
                    AuditEvent.request_id,
                    AuditEvent.outcome,
                )
            )
        )
        audit_text = repr(audit_fields)
        assert "test-password-with-sufficient-length" not in audit_text
        assert first_refresh not in audit_text
        assert all(event.request_id for event in audit_events)


@pytest.mark.asyncio
async def test_sqlite_membership_role_boundaries_and_cross_organization_idor(
    sqlite_security_environment, sqlite_client
):
    factory = sqlite_security_environment["session_factory"]
    await _create_organizations(factory, "org-a", "org-b")
    password_hash = hash_password("test-password-with-sufficient-length")
    role_users = [
        ("owner-a", Role.OWNER, "owner@example.test", False),
        ("admin-a", Role.ADMIN, "admin@example.test", False),
        ("analyst-a", Role.ANALYST, "analyst@example.test", False),
        ("viewer-a", Role.VIEWER, "viewer@example.test", False),
        ("platform-a", Role.VIEWER, "platform@example.test", True),
    ]
    async with factory() as session:
        for user_id, role, email, platform_admin in role_users:
            session.add(
                User(
                    user_id=user_id,
                    email=email,
                    email_lookup_hash=email_lookup_hash(email),
                    password_hash=password_hash,
                    is_platform_admin=platform_admin,
                )
            )
            session.add(
                OrganizationMembership(
                    user_id=user_id,
                    organization_id="org-a",
                    role=role.value,
                )
            )
        await session.commit()
        repository = ResearchRepository(session)
        await repository.create(
            research_id="org-b-research",
            organization_id="org-b",
            company_name="Private B",
            industry="Private",
            research_question="Private question",
            status="completed",
        )
        await session.commit()

        expected = {
            Role.OWNER: set(Permission),
            Role.ADMIN: set(Permission)
            - {Permission.MANAGE_ORGANIZATION, Permission.MANAGE_CONFIGURATION},
            Role.ANALYST: {
                Permission.CREATE_RESEARCH,
                Permission.VIEW_RESEARCH,
                Permission.MANAGE_COMPETITORS,
                Permission.MANAGE_EVIDENCE,
                Permission.VIEW_STRATEGY_REPORTS,
            },
            Role.VIEWER: {
                Permission.VIEW_RESEARCH,
                Permission.VIEW_STRATEGY_REPORTS,
            },
        }
        for user_id, role, email, platform_admin in role_users:
            user = AuthenticatedUser(user_id, email, "session", platform_admin)
            request = Request({"type": "http", "headers": [], "state": {}})
            context = await get_organization_context(
                request,
                user,
                "org-a",
                session,
            )
            assert context.role is role
            for permission in Permission:
                dependency = require_permission(permission)
                if permission in expected[role]:
                    assert await dependency(context) == context
                else:
                    with pytest.raises(HTTPException) as error:
                        await dependency(context)
                    assert error.value.status_code == 403
            if platform_admin:
                assert await require_platform_admin(user) == user
            else:
                with pytest.raises(HTTPException) as error:
                    await require_platform_admin(user)
                assert error.value.status_code == 403

    login = await sqlite_client.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://localhost:3000"},
        json={
            "email": "viewer@example.test",
            "password": "test-password-with-sufficient-length",
        },
    )
    assert login.status_code == 200
    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}",
        "X-Organization-ID": "org-a",
    }
    visible_orgs = await sqlite_client.get(
        "/api/v1/auth/organizations",
        headers={"Authorization": headers["Authorization"]},
    )
    assert visible_orgs.status_code == 200
    assert [item["organization_id"] for item in visible_orgs.json()] == ["org-a"]

    hidden_research = await sqlite_client.get(
        "/api/v1/research/org-b-research",
        headers=headers,
    )
    assert hidden_research.status_code == 404
    wrong_org = await sqlite_client.get(
        "/api/v1/research/org-b-research",
        headers={**headers, "X-Organization-ID": "org-b"},
    )
    assert wrong_org.status_code == 403

    denied_create = await sqlite_client.post(
        "/api/v1/research",
        headers=headers,
        json={
            "company_name": "Example",
            "industry": "Software",
            "research_question": "Assess direct competitors",
        },
    )
    assert denied_create.status_code == 403
    revoked_user = await sqlite_client.get(
        "/api/v1/research/org-b-research",
        headers={**headers, "X-Organization-ID": "org-a"},
    )
    assert revoked_user.status_code == 404
    async with factory() as session:
        membership = await session.get(
            OrganizationMembership, ("viewer-a", "org-a")
        )
        membership.is_active = False
        await session.commit()
    after_revocation = await sqlite_client.get(
        "/api/v1/research/org-b-research",
        headers=headers,
    )
    assert after_revocation.status_code == 403


@pytest.mark.asyncio
async def test_sqlite_login_throttling_is_shared_by_apps_using_the_same_test_database(
    sqlite_security_environment,
):
    from app.main import create_app

    settings = get_settings()
    settings.auth_rate_limit_requests = 2
    app_one = sqlite_security_environment["create_app"]()
    app_two = create_app()
    app_two.dependency_overrides[get_db_session] = (
        app_one.dependency_overrides[get_db_session]
    )
    transport_one = ASGITransport(app=app_one)
    transport_two = ASGITransport(app=app_two)
    async with AsyncClient(transport=transport_one, base_url="http://testserver") as first:
        async with AsyncClient(transport=transport_two, base_url="http://testserver") as second:
            for client in (first, second):
                response = await client.post(
                    "/api/v1/auth/login",
                    headers={"Origin": "http://localhost:3000"},
                    json={"email": "missing@example.test", "password": "invalid"},
                )
                assert response.status_code == 401
            limited = await first.post(
                "/api/v1/auth/login",
                headers={"Origin": "http://localhost:3000"},
                json={"email": "missing@example.test", "password": "invalid"},
            )
            assert limited.status_code == 429
            assert limited.headers["X-Request-ID"]


@pytest.mark.asyncio
async def test_sqlite_api_request_validation_size_origin_and_audit_redaction(
    sqlite_security_environment, sqlite_client
):
    bad_origin = await sqlite_client.post(
        "/api/v1/auth/login",
        headers={"Origin": "https://attacker.example"},
        json={"email": "nobody@example.test", "password": "private-password"},
    )
    assert bad_origin.status_code == 403
    assert bad_origin.headers["X-Request-ID"]

    invalid_payload = await sqlite_client.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://localhost:3000"},
        json={"email": "invalid", "password": "private-password"},
    )
    assert invalid_payload.status_code == 422
    assert "private-password" not in invalid_payload.text
    assert invalid_payload.headers["X-Request-ID"]

    oversized = await sqlite_client.post(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Content-Type": "application/json",
            "Content-Length": str(4 * 1024 * 1024 + 1),
        },
        content=b"",
    )
    assert oversized.status_code == 413
    assert oversized.headers["X-Request-ID"]

    factory = sqlite_security_environment["session_factory"]
    async with factory() as session:
        audit_fields = list(
            await session.execute(
                select(
                    AuditEvent.action,
                    AuditEvent.resource_type,
                    AuditEvent.request_id,
                    AuditEvent.outcome,
                )
            )
        )
        assert audit_fields
        serialized = repr(audit_fields)
        assert "private-password" not in serialized
        assert "nobody@example.test" not in serialized



@pytest.mark.asyncio
async def test_sqlite_encryption_failure_and_plaintext_rejection(
    sqlite_security_environment,
):
    from app.security.crypto import EncryptionConfigurationError

    factory = sqlite_security_environment["session_factory"]
    await _create_organizations(factory, "org-enc")

    research_id = f"enc-{uuid4().hex}"
    async with factory() as session:
        repo = ResearchRepository(session)
        await repo.create(
            research_id=research_id,
            organization_id="org-enc",
            company_name="Valid Encryption Co",
            industry="Tech",
            research_question="Question?",
            status="completed",
        )
        await session.commit()

    # Tampered / corrupted key ID raises EncryptionConfigurationError
    async with factory() as session:
        await session.execute(
            text(
                "UPDATE researches SET company_name = 'acis:v1:unknownkey:dGFtcGVyZWQ=' "
                "WHERE research_id = :rid"
            ),
            {"rid": research_id},
        )
        await session.commit()

    async with factory() as session:
        repo = ResearchRepository(session)
        with pytest.raises(EncryptionConfigurationError):
            await repo.get_by_id(research_id, "org-enc")

    # Corrupted ciphertext / invalid authentication tag raises ValueError
    valid_key_id = sqlite_security_environment["aes_key_id"]
    corrupted_payload = base64.urlsafe_b64encode(b"x" * 28).decode("ascii")
    async with factory() as session:
        await session.execute(
            text(
                f"UPDATE researches SET company_name = 'acis:v1:{valid_key_id}:{corrupted_payload}' "
                "WHERE research_id = :rid"
            ),
            {"rid": research_id},
        )
        await session.commit()

    async with factory() as session:
        repo = ResearchRepository(session)
        with pytest.raises(ValueError, match="integrity validation"):
            await repo.get_by_id(research_id, "org-enc")

    # Plaintext without envelope is rejected
    plaintext_id = f"plain-{uuid4().hex}"
    async with factory() as session:
        await session.execute(
            text(
                "INSERT INTO researches ("
                "  research_id, organization_id, company_name, industry, "
                "  research_question, status, errors"
                ") VALUES ("
                "  :rid, 'org-enc', 'Raw Plaintext Value', 'acis:v1:dummy:payload', "
                "  'acis:v1:dummy:payload', 'completed', '[]'"
                ")"
            ),
            {"rid": plaintext_id},
        )
        await session.commit()

    async with factory() as session:
        repo = ResearchRepository(session)
        with pytest.raises(ValueError, match="Invalid encrypted data envelope"):
            await repo.get_by_id(plaintext_id, "org-enc")


@pytest.mark.asyncio
async def test_sqlite_secure_error_responses(
    sqlite_security_environment, sqlite_client
):
    factory = sqlite_security_environment["session_factory"]
    await _create_organizations(factory, "org-sec")
    await _create_user(
        factory,
        user_id="user-sec",
        email="sec@example.test",
        role=Role.VIEWER.value,
        organization_id="org-sec",
    )

    # 401 unauthenticated does not echo token or leak internal details
    resp_401 = await sqlite_client.get(
        "/api/v1/auth/organizations",
        headers={"Authorization": "Bearer invalid-or-malformed-token"},
    )
    assert resp_401.status_code == 401
    assert "invalid-or-malformed-token" not in resp_401.text
    assert resp_401.headers.get("X-Request-ID")

    login = await sqlite_client.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://localhost:3000"},
        json={
            "email": "sec@example.test",
            "password": "test-password-with-sufficient-length",
        },
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    # 404 not found includes correlation ID and does not leak resource details
    resp_404 = await sqlite_client.get(
        "/api/v1/research/non-existent-secret-id-999",
        headers={"Authorization": f"Bearer {token}", "X-Organization-ID": "org-sec"},
    )
    assert resp_404.status_code == 404
    assert resp_404.headers.get("X-Request-ID")

    # 403 forbidden on wrong organization
    resp_403 = await sqlite_client.get(
        "/api/v1/research/non-existent-secret-id-999",
        headers={"Authorization": f"Bearer {token}", "X-Organization-ID": "unauthorized-org"},
    )
    assert resp_403.status_code == 403
    assert resp_403.headers.get("X-Request-ID")
