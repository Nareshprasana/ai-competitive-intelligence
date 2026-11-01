"""Tests for database layer (core/database.py).

Verifies graceful degradation without PostgreSQL: app starts, engine/session
do not crash at import, health reports unavailable honestly.
"""

from app.core.database import db, DatabaseManager, Base, PGVECTOR_AVAILABLE
from app.core.exceptions import DatabaseUnavailableError


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
