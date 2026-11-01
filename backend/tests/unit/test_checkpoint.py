"""Tests for LangGraph PostgreSQL checkpointing (core/checkpoint.py).

Requires DATABASE_URL to point at a live PostgreSQL instance. Verifies that
the AsyncPostgresSaver adapter can set up checkpoints tables, store a
thread-based checkpoint, and retrieve it (resume capability).
"""

import asyncio
import os

import pytest
from langgraph.graph import StateGraph, START, END
from psycopg import Connection

from app.core.checkpoint import AsyncPostgresSaver
from app.core.config import get_settings
from app.core.database import db
from app.graph.state import ResearchState
from app.graph.nodes import (
    initialize_research,
    research_planner,
    evidence_validator_mock,
    strategic_analyst_mock,
    report_generator_mock,
    finalize_research,
)
from app.graph.nodes.company_researcher_mock import company_researcher_mock
from app.graph.nodes.competitor_discovery_mock import competitor_discovery_mock
from app.graph.state import ResearchState

# Ensure settings are re-read with DATABASE_URL from the environment.
get_settings.cache_clear()
db._configured = False
db._engine = None
db._session_factory = None
db._available = False
db._checkpointer = None

TEST_DATABASE_URL = os.getenv("ACIS_TEST_DATABASE_URL") or os.getenv("DATABASE_URL") or ""
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="PostgreSQL tests require ACIS_TEST_DATABASE_URL or DATABASE_URL.",
)
# libpq form for psycopg-based checkpointer.
CHECKPOINT_CONN_STRING = TEST_DATABASE_URL.replace(
    "postgresql+asyncpg://", "postgresql://", 1
)


@pytest.fixture(autouse=True)
async def _reset_db_each_test():
    """Reset the shared db singleton so each test gets a fresh engine on its
    own event loop (avoids 'Event loop is closed' across tests)."""
    get_settings.cache_clear()
    db._configured = False
    db._engine = None
    db._session_factory = None
    db._available = False
    db._checkpointer = None
    yield
    # Best-effort cleanup of any checkpointer connection.
    if db._checkpointer is not None:
        try:
            db._checkpointer.conn.close()
        except Exception:  # noqa: BLE001
            pass
        db._checkpointer = None


def _build_graph(checkpointer):
    builder = StateGraph(ResearchState)
    nodes = [
        ("initialize_research", initialize_research),
        ("research_planner", research_planner),
        ("company_researcher_mock", company_researcher_mock),
        ("competitor_discovery_mock", competitor_discovery_mock),
        ("evidence_validator_mock", evidence_validator_mock),
        ("strategic_analyst_mock", strategic_analyst_mock),
        ("report_generator_mock", report_generator_mock),
        ("finalize_research", finalize_research),
    ]
    for name, fn in nodes:
        builder.add_node(name, fn)
    builder.add_edge(START, "initialize_research")
    for i in range(len(nodes) - 1):
        builder.add_edge(nodes[i][0], nodes[i + 1][0])
    builder.add_edge("finalize_research", END)
    return builder.compile(checkpointer=checkpointer)


@pytest.mark.asyncio
async def test_checkpointer_setup_creates_tables():
    """setup() creates the dedicated checkpoints tables (separate from researches)."""
    from sqlalchemy import text

    assert db.is_available is True
    conn = Connection.connect(
        CHECKPOINT_CONN_STRING, autocommit=True, prepare_threshold=0
    )
    saver = AsyncPostgresSaver(conn)
    try:
        await asyncio.to_thread(saver.setup)
        async for session in db.get_session():
            result = await session.execute(
                text("SELECT to_regclass('public.checkpoints')")
            )
            assert result.scalar() == "checkpoints"
            result = await session.execute(
                text("SELECT to_regclass('public.checkpoint_writes')")
            )
            assert result.scalar() == "checkpoint_writes"
            break
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_thread_based_checkpoint_store_and_retrieve():
    """A research run with a thread_id checkpoints state and can be retrieved."""
    conn = Connection.connect(
        CHECKPOINT_CONN_STRING, autocommit=True, prepare_threshold=0
    )
    saver = AsyncPostgresSaver(conn)
    try:
        await asyncio.to_thread(saver.setup)
        graph = _build_graph(saver)
        state = ResearchState(
            research_id="res-ckpt-test",
            organization_id="org-dev",
            company_name="Acme Corp",
            industry="AI Software",
            research_question="Pricing vs competitors?",
        )
        config = {"configurable": {"thread_id": "thread-persist-1"}}
        final = await graph.ainvoke(state, config=config)
        if isinstance(final, dict):
            final = ResearchState(**final)

        assert final.review_status == "reviewed"
        assert final.errors == []

        # Retrieve the checkpoint (resume capability).
        checkpoint = await saver.aget_tuple(config)
        assert checkpoint is not None
        assert checkpoint.checkpoint is not None
        channel_values = checkpoint.checkpoint.get("channel_values", {})
        assert channel_values.get("company_name") == "Acme Corp"
        assert channel_values.get("review_status") == "reviewed"
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_database_available_for_checkpointing():
    """The database is available so checkpointing can be configured."""
    assert db.is_available is True
    health = await db.health_check()
    assert health["available"] is True
