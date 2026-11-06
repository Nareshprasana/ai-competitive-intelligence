"""Tests for the LangGraph builder and full graph execution (graph/builder.py)."""

import asyncio
from importlib import import_module

import app.graph.builder as builder_module
from app.agents.company_researcher import CompanyResearcherAgent
from app.agents.competitor_researcher import CompetitorResearcherAgent
from app.tools.search.providers.mock import MockSearchProvider
from app.graph.builder import build_graph, NODE_ORDER, get_graph
from app.graph.state import ResearchState


EXPECTED_ORDER = [
    "initialize_research",
    "research_planner",
    "company_researcher",
    "competitor_discovery",
    "evidence_validator",
    "strategic_analyst_mock",
    "report_generator_mock",
    "finalize_research",
]


class UnavailableLLMClient:
    def is_available(self):
        return False

    async def close(self):
        pass


async def _unavailable_llm(self):
    return UnavailableLLMClient()


def _disable_live_llm(monkeypatch):
    monkeypatch.setattr(CompanyResearcherAgent, "_get_llm_client", _unavailable_llm)
    monkeypatch.setattr(CompetitorResearcherAgent, "_get_llm_client", _unavailable_llm)
    company_node = import_module("app.graph.nodes.company_researcher")
    competitor_node = import_module("app.graph.nodes.competitor_discovery_node")
    monkeypatch.setattr(
        company_node,
        "_build_search_provider",
        lambda: MockSearchProvider(),
    )
    monkeypatch.setattr(
        competitor_node,
        "_build_search_provider",
        lambda: MockSearchProvider(),
    )
    monkeypatch.setattr(company_node, "_persist_company_research", _skip_persistence)
    monkeypatch.setattr(
        competitor_node, "_persist_competitor_discovery", _skip_persistence
    )


async def _skip_persistence(**kwargs):
    return None


def test_node_order_matches_requirement():
    assert NODE_ORDER == EXPECTED_ORDER


def test_build_graph_produces_expected_nodes():
    g = build_graph()
    assert g is not None


def test_competitor_and_search_results_are_checkpointed(monkeypatch):
    from langgraph.checkpoint.memory import InMemorySaver

    _disable_live_llm(monkeypatch)
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "competitor-checkpoint"}}
    state = ResearchState(
        research_id="res-checkpoint",
        organization_id="org-dev",
        company_name="Acme Corp",
        industry="AI Software",
        research_question="Pricing vs competitors?",
    )
    asyncio.run(graph.ainvoke(state, config=config))
    snapshot = asyncio.run(graph.aget_state(config))
    assert snapshot.values["search_results"]
    assert "competitors" in snapshot.values
    assert any(
        item["node_name"] == "competitor_discovery"
        for item in snapshot.values["execution_metadata"]
    )


def test_full_graph_execution_all_nodes_completed(monkeypatch):
    _disable_live_llm(monkeypatch)
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
    # company_researcher, competitor_discovery, and evidence_validator are real agents (mock=False);
    # all others are mocks.
    mock_flags = [m["mock"] for m in final.execution_metadata]
    assert mock_flags.count(False) == 3
    assert mock_flags.count(True) == 5
    assert final.final_report is not None
    assert final.final_report["company"] == "Acme Corp"


def test_graph_never_reports_success_when_node_fails(monkeypatch):
    """Inject a failing node and verify the run ends in 'failed', not success.

    The failure is injected via a ``run_node``-wrapped node placed in the
    builder's node registry, so the graph's exception-handling path is
    exercised exactly as it would be in production.
    """
    _disable_live_llm(monkeypatch)
    from app.graph.nodes.base import run_node

    async def _failing_inner(state):
        raise RuntimeError("simulated node failure")

    async def _failing_wrapped(state):
        return await run_node(
            node_name="company_researcher",
            state=state,
            node_fn=_failing_inner,
            mock=False,
        )

    monkeypatch.setitem(builder_module._NODES, "company_researcher", _failing_wrapped)

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
    assert any(e["node_name"] == "company_researcher" for e in final.errors)
    # Metadata should record the failure.
    failed = [m for m in final.execution_metadata if m["node_name"] == "company_researcher"]
    assert failed and failed[0]["status"] == "failed"


def test_get_graph_returns_cached_compiled_graph():
    g1 = get_graph()
    g2 = get_graph()
    assert g1 is g2
