"""Focused tests for authentication primitives and authorization policies."""

import asyncio
import base64
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.graph.nodes.base import run_node
from app.graph.state import ResearchState
from app.main import create_app
from app.schemas.research import ResearchRequest
from app.security import crypto
from app.security.auth import (
    AuthenticatedUser,
    OrganizationContext,
    Permission,
    Role,
    create_access_token,
    decode_access_token,
    email_lookup_hash,
    hash_password,
    require_permission,
    require_platform_admin,
    verify_csrf,
    verify_password,
)


def _settings(*, signing_key: str = "test-signing-key-with-32-characters") -> SimpleNamespace:
    return SimpleNamespace(
        auth_jwt_signing_key=SecretStr(signing_key),
        auth_email_lookup_key=SecretStr(
            "test-email-lookup-key-with-at-least-32-characters"
        ),
        auth_access_token_minutes=10,
        data_encryption_keys=SecretStr(
            json.dumps(
                {
                    "test-key": base64.b64encode(b"k" * 32).decode("ascii"),
                }
            )
        ),
        data_encryption_active_key_id="test-key",
    )


def test_argon2id_password_hashing_and_password_bounds():
    encoded = hash_password("a-long-password-value")
    assert encoded.startswith("$argon2id$")
    assert verify_password(encoded, "a-long-password-value")
    assert not verify_password(encoded, "not-the-password")
    with pytest.raises(ValueError):
        hash_password("short")
    assert not verify_password("$argon2id$malformed", "password")


def test_access_token_validates_and_rejects_tampering(monkeypatch):
    monkeypatch.setattr("app.security.auth.get_settings", _settings)
    token = create_access_token("user-1", "session-1")
    claims = decode_access_token(token)
    assert claims["sub"] == "user-1"
    assert claims["sid"] == "session-1"
    with pytest.raises(HTTPException) as error:
        decode_access_token(token + "tampered")
    assert error.value.status_code == 401


@pytest.mark.parametrize("token", ["", "not-a-jwt", "a.b.c", "eyJhbGciOiJub25lIn0.e30."])
def test_malformed_access_tokens_are_rejected(monkeypatch, token):
    monkeypatch.setattr("app.security.auth.get_settings", _settings)
    with pytest.raises(HTTPException) as error:
        decode_access_token(token)
    assert error.value.status_code == 401


def test_email_lookup_hash_is_normalized_and_keyed(monkeypatch):
    monkeypatch.setattr("app.security.auth.get_settings", _settings)
    assert email_lookup_hash("User@Example.test") == email_lookup_hash(
        " user@example.test "
    )


def test_expired_access_token_is_rejected(monkeypatch):
    monkeypatch.setattr("app.security.auth.get_settings", _settings)
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "user-1",
            "sid": "session-1",
            "jti": "token-1",
            "iat": now - timedelta(minutes=2),
            "exp": now - timedelta(minutes=1),
            "iss": "acis",
            "aud": "acis-api",
        },
        _settings().auth_jwt_signing_key.get_secret_value(),
        algorithm="HS256",
    )
    with pytest.raises(HTTPException) as error:
        decode_access_token(token)
    assert error.value.status_code == 401


def test_role_permissions_are_enforced():
    analyst = OrganizationContext(
        AuthenticatedUser("u1", "a@example.com", "s1", False),
        "org1",
        Role.ANALYST,
    )
    viewer = OrganizationContext(
        AuthenticatedUser("u2", "v@example.com", "s2", False),
        "org1",
        Role.VIEWER,
    )
    dependency = require_permission(Permission.CREATE_RESEARCH)
    assert asyncio.run(dependency(analyst)) == analyst
    with pytest.raises(HTTPException) as error:
        asyncio.run(dependency(viewer))
    assert error.value.status_code == 403


def test_role_permission_matrix_and_platform_admin_boundary():
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
        Role.VIEWER: {Permission.VIEW_RESEARCH, Permission.VIEW_STRATEGY_REPORTS},
    }

    for role, allowed_permissions in expected.items():
        context = OrganizationContext(
            AuthenticatedUser("user", "user@example.test", "session", False),
            "org",
            role,
        )
        for permission in Permission:
            dependency = require_permission(permission)
            if permission in allowed_permissions:
                assert asyncio.run(dependency(context)) == context
            else:
                with pytest.raises(HTTPException) as error:
                    asyncio.run(dependency(context))
                assert error.value.status_code == 403

    platform_admin = AuthenticatedUser(
        "admin", "admin@example.test", "session", True
    )
    ordinary_user = AuthenticatedUser(
        "user", "user@example.test", "session", False
    )
    assert asyncio.run(require_platform_admin(platform_admin)) == platform_admin
    with pytest.raises(HTTPException) as error:
        asyncio.run(require_platform_admin(ordinary_user))
    assert error.value.status_code == 403


def test_csrf_requires_allowed_origin_and_matching_double_submit_token(monkeypatch):
    settings = _settings()
    settings.backend_cors_origins = ["https://app.example.test"]
    monkeypatch.setattr("app.security.auth.get_settings", lambda: settings)
    request = SimpleNamespace(
        headers={"origin": "https://app.example.test"}
    )
    verify_csrf(request, "same-token", "same-token")
    with pytest.raises(HTTPException):
        verify_csrf(request, "cookie-token", "other-token")


def test_encrypted_text_and_checkpoint_payload_round_trip(monkeypatch):
    monkeypatch.setattr(crypto, "get_settings", _settings)
    plaintext = "sensitive research content"
    encrypted = crypto.encrypt_text(plaintext, associated_data="test.field")
    assert plaintext not in encrypted
    assert crypto.decrypt_text(encrypted, associated_data="test.field") == plaintext
    with pytest.raises(ValueError):
        crypto.decrypt_text(encrypted, associated_data="other.field")

    serializer = crypto.EncryptedCheckpointSerializer()
    value = {"question": plaintext, "count": 3}
    value_type, payload = serializer.dumps_typed(value)
    assert plaintext.encode() not in payload
    assert serializer.loads_typed((value_type, payload)) == value


def test_research_request_rejects_client_organization_id():
    with pytest.raises(ValueError):
        ResearchRequest(
            company_name="Example",
            industry="Software",
            research_question="Assess product competition",
            organization_id="attacker-org",
        )


def test_graph_failure_does_not_expose_exception_content():
    async def fail(_state):
        raise RuntimeError("database password=private-value")

    result = asyncio.run(
        run_node(
            node_name="test_node",
            state=ResearchState(
                research_id="test-id",
                company_name="Example",
                industry="Software",
                research_question="Assess competitors",
            ),
            node_fn=fail,
        )
    )
    assert result["errors"][0]["error"] == "The operation could not be completed."
    assert "private-value" not in str(result)


def test_research_endpoint_requires_authentication_without_database():
    client = TestClient(create_app())
    response = client.get("/api/v1/research/res-unknown")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


def test_api_rate_limit_applies_before_authentication(monkeypatch):
    import app.main as main

    class FakeSession:
        def __init__(self):
            self.events = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        def add(self, event):
            self.events.append(event)

        async def commit(self):
            return None

    fake_session = FakeSession()
    monkeypatch.setattr(main.db, "_configured", True)
    monkeypatch.setattr(main.db, "_available", True)
    monkeypatch.setattr(main.db, "_session_factory", lambda: fake_session)
    calls = []

    async def block_request(_request, _session, *, identity, limit):
        calls.append((identity, limit))
        raise HTTPException(
            status_code=429,
            detail="Request rate limit exceeded.",
            headers={"Retry-After": "60"},
        )

    monkeypatch.setattr(main, "enforce_rate_limit", block_request)
    response = TestClient(main.create_app()).get("/api/v1/research/untrusted-id")

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"
    assert response.headers["X-Request-ID"]
    assert calls and calls[0][0].startswith("ip:")
    assert len(fake_session.events) == 1


def test_error_responses_do_not_echo_credentials_or_internal_exception_details():
    from app.core.database import get_db_session

    async def unused_session():
        yield object()

    app = create_app()
    app.dependency_overrides[get_db_session] = unused_session
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://localhost:3000"},
        json={"email": "not-an-email", "password": "do-not-echo-this-password"},
    )
    assert response.status_code == 422
    assert "do-not-echo-this-password" not in response.text
    assert "input" not in response.text.lower()
    assert response.headers["X-Request-ID"]


def test_request_size_limit_and_correlation_id_are_enforced():
    client = TestClient(create_app())
    too_large = client.post(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Content-Type": "application/json",
            "Content-Length": str(4 * 1024 * 1024 + 1),
        },
        content=b"",
    )
    assert too_large.status_code == 413
    assert too_large.headers["X-Request-ID"]

    malformed_length = client.post(
        "/api/v1/auth/login",
        headers={"Content-Length": "not-a-number"},
        content=b"",
    )
    assert malformed_length.status_code == 400
    assert malformed_length.headers["X-Request-ID"]
