"""Tests for database layer (core/database.py).

Verifies graceful degradation without PostgreSQL: app starts, engine/session
do not crash at import, health reports unavailable honestly.
"""

import pytest

from app.core.config import get_settings
from app.core.database import db, DatabaseManager, Base, PGVECTOR_AVAILABLE
from app.core.exceptions import DatabaseUnavailableError


@pytest.fixture(autouse=True)
def unconfigured_db_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    get_settings.cache_clear()
    orig_configured = db._configured
    orig_available = db._available
    orig_engine = db._engine
    orig_factory = db._session_factory
    db._configured = False
    db._available = False
    db._engine = None
    db._session_factory = None
    yield
    db._configured = orig_configured
    db._available = orig_available
    db._engine = orig_engine
    db._session_factory = orig_factory
    get_settings.cache_clear()


def test_database_manager_starts_without_url():
    mgr = DatabaseManager()
    assert mgr.is_available is False
    # Accessing the engine without a configured URL must raise, never silently connect.
    try:
        _ = mgr.engine
        assert False, "expected DatabaseUnavailableError"
    except DatabaseUnavailableError:
        pass


def test_session_factory_raises_when_unavailable():
    mgr = DatabaseManager()
    try:
        _ = mgr.session_factory
        assert False, "expected DatabaseUnavailableError"
    except DatabaseUnavailableError:
        pass


def test_base_declarative():
    assert Base is not None


def test_health_check_never_raises_without_db():
    import asyncio

    result = asyncio.run(db.health_check())
    assert result["available"] is False
    assert result["configured"] is False
    assert "error" in result
