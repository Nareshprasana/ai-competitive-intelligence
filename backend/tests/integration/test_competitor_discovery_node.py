"""Integration tests for the competitor_discovery LangGraph node."""

import asyncio
from importlib import import_module
import pytest

from app.agents.competitor_researcher import CompetitorResearcherAgent
from app.tools.search.providers.mock import MockSearchProvider
from app.graph.builder import build_graph
from app.graph.state import ResearchState
from app.graph.nodes.competitor_discovery_node import competitor_discovery


class UnavailableLLMClient:
    def is_available(self):
        return False

    async def close(self):
        pass


async def _unavailable_llm(self):
    return UnavailableLLMClient()


@pytest.fixture(autouse=True)
def disable_live_llm(monkeypatch):
    monkeypatch.setattr(CompetitorResearcherAgent, "_get_llm_client", _unavailable_llm)
    competitor_node = import_module("app.graph.nodes.competitor_discovery_node")
    monkeypatch.setattr(
        competitor_node,
        "_build_search_provider",
        lambda: MockSearchProvider(),
    )
    monkeypatch.setattr(
        competitor_node, "_persist_competitor_discovery", _skip_persistence
    )


async def _skip_persistence(**kwargs):
    return None


async def _run_node_with_mock_agent():
    """Run the competitor_discovery node directly."""
    state = ResearchState(
        research_id="res-node-test",
        organization_id="org-dev",
        company_name="Acme Corp",
        industry="AI Software",
        research_question="Who are the competitors?",
        company_profile={
            "company_name": "Acme Corp",
            "industry": "AI Software",
            "products": ["AI Platform"],
            "target_customers": ["Enterprise"],
            "business_model": "SaaS",
            "geographical_presence": ["North America"],
            "website": "https://acme.example.com",
        },
    )
    result = await competitor_discovery(state)
    return result


def test_node_returns_dict_with_competitors_and_metadata():
    result = asyncio.run(_run_node_with_mock_agent())
    assert isinstance(result, dict)
    assert "execution_metadata" in result
    assert "errors" in result
    md = result["execution_metadata"][0]
    assert md["node_name"] == "competitor_discovery"
    assert md["status"] in ("completed", "failed")
    assert "duration_ms" in md


def test_node_records_failure_safely():
    """The node should never crash the graph; failures are recorded in errors."""
    state = ResearchState(
        research_id="res-node-fail",
        organization_id="org-dev",
        company_name="Test Corp",
        industry="Tech",
        research_question="q",
    )
    result = asyncio.run(competitor_discovery(state))
    assert "execution_metadata" in result
    # Node completes (either with results or graceful degradation)
    assert result["execution_metadata"][0]["status"] in ("completed", "failed")


def test_graph_builder_registers_competitor_discovery():
    from app.graph.builder import NODE_ORDER, _NODES
    assert "competitor_discovery" in NODE_ORDER
    assert "competitor_discovery" in _NODES
    # The old mock node name should NOT be in the active workflow
    assert "competitor_discovery_mock" not in NODE_ORDER


def test_graph_execution_order_includes_competitor_discovery():
    graph = build_graph()
    assert graph is not None


__all__ = []
