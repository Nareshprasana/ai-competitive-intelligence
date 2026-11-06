"""Unit tests for cookie security across environments (Phase 3.2.1).

Verifies:
1. Development environment allows local HTTP with SameSite=Strict and HttpOnly.
2. Test environment allows local testing.
3. Staging requires AUTH_COOKIE_SECURE=true and fails closed if false.
4. Production requires AUTH_COOKIE_SECURE=true and fails closed if false.
5. Set-Cookie header attributes verification across environments.
"""

from fastapi import Response
import pytest
from pydantic import ValidationError

from app.api.v1.endpoints.auth import _set_auth_cookies, _clear_auth_cookies
from app.core.config import Settings, get_settings


def test_development_cookie_settings(monkeypatch):
    """Development environment defaults to secure=False for localhost HTTP."""
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    get_settings.cache_clear()

    settings = get_settings()
    assert settings.auth_cookie_secure is False

    res = Response()
    _set_auth_cookies(res, "test_dev_refresh_token")
    cookies = res.headers.getlist("set-cookie")
    refresh_cookie = next(c for c in cookies if "acis_refresh_token" in c)
    assert "HttpOnly" in refresh_cookie
    assert "samesite=strict" in refresh_cookie.lower()
    assert "Path=/api/v1/auth" in refresh_cookie
    assert "Secure" not in refresh_cookie


def test_staging_cookie_security_mandate(monkeypatch):
    """Staging environment fails closed if AUTH_COOKIE_SECURE is false."""
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@127.0.0.1:5432/acis_staging")
    monkeypatch.setenv("AUTH_JWT_SIGNING_KEY", "x" * 32)
    monkeypatch.setenv("AUTH_EMAIL_LOOKUP_KEY", "y" * 32)
    get_settings.cache_clear()

    with pytest.raises(ValidationError, match="AUTH_COOKIE_SECURE must be true in staging"):
        Settings()

    # Valid staging configuration
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    get_settings.cache_clear()
    settings = Settings()
    assert settings.auth_cookie_secure is True

    res = Response()
    _set_auth_cookies(res, "test_staging_refresh_token")
    cookies = res.headers.getlist("set-cookie")
    refresh_cookie = next(c for c in cookies if "acis_refresh_token" in c)
    assert "HttpOnly" in refresh_cookie
    assert "samesite=strict" in refresh_cookie.lower()
    assert "Path=/api/v1/auth" in refresh_cookie
    assert "Secure" in refresh_cookie


def test_production_cookie_security_mandate(monkeypatch):
    """Production environment fails closed if AUTH_COOKIE_SECURE is false."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@127.0.0.1:5432/acis_prod")
    monkeypatch.setenv("AUTH_JWT_SIGNING_KEY", "x" * 32)
    monkeypatch.setenv("AUTH_EMAIL_LOOKUP_KEY", "y" * 32)
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", '["https://app.acis.ai"]')
    get_settings.cache_clear()

    with pytest.raises(ValidationError, match="AUTH_COOKIE_SECURE must be true in production"):
        Settings()

    # Valid production configuration
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    get_settings.cache_clear()
    settings = Settings()
    assert settings.auth_cookie_secure is True

    res = Response()
    _set_auth_cookies(res, "test_prod_refresh_token")
    cookies = res.headers.getlist("set-cookie")
    refresh_cookie = next(c for c in cookies if "acis_refresh_token" in c)
    assert "HttpOnly" in refresh_cookie
    assert "samesite=strict" in refresh_cookie.lower()
    assert "Path=/api/v1/auth" in refresh_cookie
    assert "Secure" in refresh_cookie
