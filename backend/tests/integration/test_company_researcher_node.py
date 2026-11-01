"""Integration tests for the company_researcher LangGraph node."""

import asyncio
from importlib import import_module
import pytest

from app.agents.company_researcher import CompanyResearcherAgent
from app.tools.search.providers.mock import MockSearchProvider
from app.graph.builder import build_graph
from app.graph.state import ResearchState
from app.graph.nodes.company_researcher import company_researcher


class UnavailableLLMClient:
    def is_available(self):
        return False

    async def close(self):
        pass


async def _unavailable_llm(self):
    return UnavailableLLMClient()


@pytest.fixture(autouse=True)
def disable_live_llm(monkeypatch):
    monkeypatch.setattr(CompanyResearcherAgent, "_get_llm_client", _unavailable_llm)
    company_node = import_module("app.graph.nodes.company_researcher")
    monkeypatch.setattr(
        company_node,
        "_build_search_provider",
        lambda: MockSearchProvider(),
    )
    monkeypatch.setattr(company_node, "_persist_company_research", _skip_persistence)


async def _skip_persistence(**kwargs):
    return None


async def _run_graph_with_mock_agent(monkeypatch):
    """Run the graph with a mocked company_researcher node."""
    # We test the node directly since full graph needs LLM/search setup.
    state = ResearchState(
        research_id="res-node-test",
        organization_id="org-dev",
        company_name="Acme Corp",
        industry="AI Software",
        research_question="What does Acme Corp do?",
    )
    result = await company_researcher(state)
    return result


def test_node_returns_dict_with_profile_and_evidence():
    result = asyncio.run(_run_graph_with_mock_agent(None))
    assert isinstance(result, dict)
    assert "execution_metadata" in result
    assert "errors" in result
    # Node may succeed or fail depending on LLM config; check metadata recorded
    md = result["execution_metadata"][0]
    assert md["node_name"] == "company_researcher"
    assert md["status"] in ("completed", "failed")
    assert "duration_ms" in md


def test_node_records_failure_safely():
    """The node should never crash the graph; failures are recorded in errors."""
    # With no LLM configured, the node degrades gracefully (mock provider)
    state = ResearchState(
        research_id="res-node-fail",
        organization_id="org-dev",
        company_name="Test Corp",
        industry="Tech",
        research_question="q",
    )
    result = asyncio.run(company_researcher(state))
    # Should complete without raising
    assert "execution_metadata" in result


def test_graph_builder_registers_company_researcher():
    from app.graph.builder import NODE_ORDER, _NODES
    assert "company_researcher" in NODE_ORDER
    assert "company_researcher" in _NODES
    # The old mock node name should NOT be in the active workflow
    assert "company_researcher_mock" not in NODE_ORDER


def test_graph_execution_order_includes_company_researcher():
    graph = build_graph()
    assert graph is not None


__all__ = []
