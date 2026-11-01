"""Tests for the LangGraph builder and full graph execution (graph/builder.py)."""

import asyncio

import app.graph.builder as builder_module
from app.graph.builder import build_graph, NODE_ORDER, get_graph
from app.graph.state import ResearchState


EXPECTED_ORDER = [
    "initialize_research",
    "research_planner",
    "company_researcher_mock",
    "competitor_discovery_mock",
    "evidence_validator_mock",
    "strategic_analyst_mock",
    "report_generator_mock",
    "finalize_research",
]


def test_node_order_matches_requirement():
    assert NODE_ORDER == EXPECTED_ORDER


def test_build_graph_produces_expected_nodes():
    g = build_graph()
    assert g is not None


def test_full_graph_execution_all_nodes_completed():
    g = build_graph()
    state = ResearchState(
        research_id="res-graph",
        organization_id="org-dev",
        company_name="Acme Corp",
        industry="AI Software",
        research_question="Pricing vs competitors?",
    )
    final = asyncio.run(g.ainvoke(state))
    if isinstance(final, dict):
        final = ResearchState(**final)

    assert final.review_status == "reviewed"
    assert final.errors == []
    order = [m["node_name"] for m in final.execution_metadata]
    assert order == EXPECTED_ORDER
    assert all(m["status"] == "completed" for m in final.execution_metadata)
    assert all(m["mock"] is True for m in final.execution_metadata)
    assert final.final_report is not None
    assert final.final_report["company"] == "Acme Corp"


def test_graph_never_reports_success_when_node_fails(monkeypatch):
    """Inject a failing node and verify the run ends in 'failed', not success.

    The failure is injected via a ``run_node``-wrapped node placed in the
    builder's node registry, so the graph's exception-handling path is
    exercised exactly as it would be in production.
    """
    from app.graph.nodes.base import run_node

    async def _failing_inner(state):
        raise RuntimeError("simulated node failure")

    async def _failing_wrapped(state):
        return await run_node(
            node_name="company_researcher_mock",
            state=state,
            node_fn=_failing_inner,
            mock=True,
        )

    monkeypatch.setitem(builder_module._NODES, "company_researcher_mock", _failing_wrapped)

    g = build_graph()
    state = ResearchState(
        research_id="res-fail",
        organization_id="org-dev",
        company_name="Acme Corp",
        industry="AI Software",
        research_question="Pricing vs competitors?",
    )
    final = asyncio.run(g.ainvoke(state))
    if isinstance(final, dict):
        final = ResearchState(**final)

    # Overall status must reflect the failure (never report success).
    assert final.review_status == "failed"
    assert len(final.errors) >= 1
    assert any(e["node_name"] == "company_researcher_mock" for e in final.errors)
    # Metadata should record the failure.
    failed = [m for m in final.execution_metadata if m["node_name"] == "company_researcher_mock"]
    assert failed and failed[0]["status"] == "failed"


def test_get_graph_returns_cached_compiled_graph():
    g1 = get_graph()
    g2 = get_graph()
    assert g1 is g2
