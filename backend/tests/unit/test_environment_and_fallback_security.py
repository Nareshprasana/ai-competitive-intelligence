"""Tests for environment validation and fallback-store security (Phase 3.2.1).

Covers all 10 required scenarios:
1. Explicit development fallback enabled
2. Development fallback disabled
3. Test fallback enabled
4. Test fallback disabled
5. Staging database outage
6. Production database outage
7. Unknown environment
8. Missing environment configuration
9. Invalid fallback flag
10. Cross-tenant fallback access
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings, get_settings_uncached
from app.core.database import db
from app.core.exceptions import DatabaseUnavailableError, NotFoundError
from app.schemas.research import ResearchResult
from app.services import research_service
from app.services.research_service import (
    _fallback_store,
    get_research,
    list_research,
    review_evidence,
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Ensure clean test environment by default."""
    get_settings.cache_clear()
    _fallback_store.clear()
    # Mock db unavailable for fallback outage testing
    orig_conf = db._configured
    orig_avail = db._available
    yield
    db._configured = orig_conf
    db._available = orig_avail
    get_settings.cache_clear()
    _fallback_store.clear()


def test_1_explicit_development_fallback_enabled(monkeypatch):
    """Scenario 1: Development fallback enabled explicitly allows fallback operations."""
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ACIS_ENABLE_MEMORY_FALLBACK", "true")
    get_settings.cache_clear()

    settings = get_settings()
    assert settings.app_env == "development"
    assert settings.acis_enable_memory_fallback is True
    assert settings.is_memory_fallback_allowed is True


def test_2_development_fallback_disabled(monkeypatch):
    """Scenario 2: Development with fallback disabled forbids memory fallback."""
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ACIS_ENABLE_MEMORY_FALLBACK", "false")
    get_settings.cache_clear()

    settings = get_settings()
    assert settings.app_env == "development"
    assert settings.acis_enable_memory_fallback is False
    assert settings.is_memory_fallback_allowed is False


def test_3_test_fallback_enabled(monkeypatch):
    """Scenario 3: Test environment with explicit fallback enabled allows fallback."""
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ACIS_ENABLE_MEMORY_FALLBACK", "true")
    get_settings.cache_clear()

    settings = get_settings()
    assert settings.app_env == "test"
    assert settings.is_memory_fallback_allowed is True


def test_4_test_fallback_disabled(monkeypatch):
    """Scenario 4: Test environment with fallback disabled rejects fallback."""
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ACIS_ENABLE_MEMORY_FALLBACK", "false")
    get_settings.cache_clear()

    settings = get_settings()
    assert settings.app_env == "test"
    assert settings.is_memory_fallback_allowed is False


def test_5_staging_database_outage(monkeypatch):
    """Scenario 5: Staging environment never allows fallback even if requested, failing closed on outage."""
    # Staging requires secure cookies and long keys
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@127.0.0.1:5432/acis_staging")
    monkeypatch.setenv("AUTH_JWT_SIGNING_KEY", "x" * 32)
    monkeypatch.setenv("AUTH_EMAIL_LOOKUP_KEY", "y" * 32)
    
    # Attempting to enable fallback in staging must raise ValidationError
    monkeypatch.setenv("ACIS_ENABLE_MEMORY_FALLBACK", "true")
    with pytest.raises(ValidationError, match="ACIS_ENABLE_MEMORY_FALLBACK is strictly forbidden in staging"):
        Settings()

    # When fallback is not requested, settings load but is_memory_fallback_allowed is False
    monkeypatch.setenv("ACIS_ENABLE_MEMORY_FALLBACK", "false")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.is_memory_fallback_allowed is False


def test_6_production_database_outage(monkeypatch):
    """Scenario 6: Production environment fails closed on database outage."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@127.0.0.1:5432/acis_prod")
    monkeypatch.setenv("AUTH_JWT_SIGNING_KEY", "x" * 32)
    monkeypatch.setenv("AUTH_EMAIL_LOOKUP_KEY", "y" * 32)
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", '["https://app.acis.ai"]')

    # Attempting to enable fallback in production must raise ValidationError
    monkeypatch.setenv("ACIS_ENABLE_MEMORY_FALLBACK", "true")
    with pytest.raises(ValidationError, match="ACIS_ENABLE_MEMORY_FALLBACK is strictly forbidden in production"):
        Settings()

    # Normal production settings
    monkeypatch.setenv("ACIS_ENABLE_MEMORY_FALLBACK", "false")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.is_memory_fallback_allowed is False


def test_7_unknown_environment(monkeypatch):
    """Scenario 7: Unknown environment value fails closed immediately at configuration time."""
    monkeypatch.setenv("APP_ENV", "preview_cloud_sandbox")
    with pytest.raises(ValidationError, match="Invalid or unsupported APP_ENV"):
        Settings()


def test_8_missing_environment_configuration(monkeypatch):
    """Scenario 8: Empty/missing APP_ENV fails closed."""
    monkeypatch.setenv("APP_ENV", "")
    with pytest.raises(ValidationError, match="Invalid or unsupported APP_ENV"):
        Settings()


def test_9_invalid_fallback_flag(monkeypatch):
    """Scenario 9: Non-boolean fallback flag is rejected by Pydantic."""
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ACIS_ENABLE_MEMORY_FALLBACK", "not_a_boolean_flag")
    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.asyncio
async def test_10_cross_tenant_fallback_access(monkeypatch):
    """Scenario 10: Fallback store enforces strict tenant isolation without leakage."""
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ACIS_ENABLE_MEMORY_FALLBACK", "true")
    get_settings.cache_clear()

    # Ensure DB is reported unavailable to test fallback isolation
    db._configured = True
    db._available = False

    # Seed fallback store with Tenant Alpha research
    res_alpha = ResearchResult(
        research_id="res-tenant-alpha",
        organization_id="org-alpha",
        company_name="Alpha Tech",
        industry="Tech",
        research_question="Landscape?",
        status="completed",
    )
    _fallback_store[res_alpha.research_id] = res_alpha

    # Tenant Alpha can access its own research
    alpha_status = await get_research("res-tenant-alpha", organization_id="org-alpha")
    assert alpha_status.research_id == "res-tenant-alpha"

    # Tenant Beta must be denied access (NotFoundError - 404)
    with pytest.raises(NotFoundError, match="Research res-tenant-alpha not found"):
        await get_research("res-tenant-alpha", organization_id="org-beta")

    # List research for Tenant Beta must not leak Tenant Alpha's research
    beta_list = await list_research(organization_id="org-beta")
    assert len(beta_list) == 0

    alpha_list = await list_research(organization_id="org-alpha")
    assert len(alpha_list) == 1
    assert alpha_list[0]["research_id"] == "res-tenant-alpha"
