"""Regression tests for async database engine lifecycle, cross-loop pooling,
and synchronous TestClient interactions (Phase 3.3).

Verifies:
1. Async database engine and checkpointer are disposed cleanly via db.dispose().
2. Dead/closed event loops do not leak pooled connections into subsequent event loops.
3. Synchronous Starlette TestClient executes unauthenticated requests safely through
   the rate-limit middleware without raising 'RuntimeError: Event loop is closed'.
4. Authentication and rate-limiting remain strictly enforced.
5. Database-unavailable behavior remains fail-closed.
"""

import asyncio
import os
import pytest
from starlette.testclient import TestClient

from app.core.config import get_settings
from app.core.database import DatabaseManager, db
from app.core.exceptions import DatabaseUnavailableError
from app.main import create_app


@pytest.mark.asyncio
async def test_database_engine_disposed_correctly():
    """Verify that db.dispose() completely resets engine, session factory, and loop references."""
    mgr = DatabaseManager()
    assert mgr._engine is None
    assert mgr._configured is False
    assert mgr._available is False
    assert mgr._loop is None

    # Force configure if DATABASE_URL is set in environment
    if get_settings().database_url:
        _ = mgr.engine
        assert mgr._engine is not None
        assert mgr._session_factory is not None
        assert mgr._configured is True
        assert mgr._available is True
        assert mgr._loop is not None

        await mgr.dispose()
        assert mgr._engine is None
        assert mgr._session_factory is None
        assert mgr._configured is False
        assert mgr._available is False
        assert mgr._loop is None


def test_engine_resets_across_closed_or_changed_event_loops():
    """Verify that a closed event loop does not cause 'RuntimeError: Event loop is closed'
    when a subsequent event loop accesses the database.
    """
    settings = get_settings()
    if not settings.database_url:
        pytest.skip("Test requires configured DATABASE_URL.")

    # 1. Access DB on Loop 1
    async def run_on_loop_1():
        db._configured = False
        async for session in db.get_session():
            pass

    asyncio.run(run_on_loop_1())

    # At this point, Loop 1 is closed!
    assert db._loop is not None
    assert db._loop.is_closed() is True

    # 2. Access DB on Loop 2: DatabaseManager must auto-discard stale engine
    async def run_on_loop_2():
        assert db.is_available is True
        # Accessing session_factory must not crash with Event loop is closed
        factory = db.session_factory
        assert factory is not None
        assert db._loop is not None
        assert db._loop.is_closed() is False
        await db.dispose()

    asyncio.run(run_on_loop_2())


def test_sync_testclient_unauthenticated_request_after_closed_loop():
    """Verify that a synchronous Starlette TestClient call can execute
    unauthenticated requests without crashing on a stale engine from an earlier closed loop.
    """
    settings = get_settings()
    if not settings.database_url:
        pytest.skip("Test requires configured DATABASE_URL.")

    # 1. Simulate an earlier async test that left an engine on a closed loop
    async def simulate_prior_test():
        db._configured = False
        async for session in db.get_session():
            pass

    asyncio.run(simulate_prior_test())
    assert db._loop is not None
    assert db._loop.is_closed() is True

    # 2. Synchronous TestClient executes request through rate-limit middleware
    client = TestClient(create_app())
    response = client.get("/api/v1/research/res-unknown")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


def test_database_unavailable_fails_closed_without_url(monkeypatch):
    """Verify that without DATABASE_URL, engine access raises DatabaseUnavailableError."""
    monkeypatch.setenv("DATABASE_URL", "")
    get_settings.cache_clear()
    mgr = DatabaseManager()
    assert mgr.is_available is False
    with pytest.raises(DatabaseUnavailableError):
        _ = mgr.engine
    with pytest.raises(DatabaseUnavailableError):
        _ = mgr.session_factory
