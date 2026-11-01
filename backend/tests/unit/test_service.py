"""Tests for the research service layer (services/research_service.py)."""

import asyncio
from importlib import import_module
import pytest

from app.agents.company_researcher import CompanyResearcherAgent
from app.agents.competitor_researcher import CompetitorResearcherAgent
from app.tools.search.providers.mock import MockSearchProvider
from app.schemas.research import ResearchRequest
from app.services.research_service import (
    run_research,
    get_research,
    list_research_ids,
    _research_store,
)


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


def test_store_starts_empty():
    _research_store.clear()
    assert list_research_ids() == []


async def _submit():
    return await run_research(
        ResearchRequest(
            company_name="Acme Corp",
            industry="AI Software",
            research_question="Pricing vs competitors?",
        )
    )


def test_run_research_returns_structured_result():
    _research_store.clear()
    result = asyncio.run(_submit())
    assert result.research_id.startswith("res-")
    assert result.status == "completed"
    assert result.company_name == "Acme Corp"
    assert result.industry == "AI Software"
    assert result.final_report is not None
    assert result.final_report["company"] == "Acme Corp"
    assert len(result.execution_metadata) == 8
    assert [m.node_name for m in result.execution_metadata] == [
        "initialize_research",
        "research_planner",
        "company_researcher",
        "competitor_discovery",
        "evidence_validator_mock",
        "strategic_analyst_mock",
        "report_generator_mock",
        "finalize_research",
    ]
    assert result.errors == []


def test_get_research_returns_stored_result():
    _research_store.clear()
    result = asyncio.run(_submit())
    fetched = asyncio.run(get_research(result.research_id))
    assert fetched.research_id == result.research_id
    assert fetched.status == "completed"
    assert fetched.results is not None


def test_get_research_missing_raises_not_found():
    _research_store.clear()
    try:
        asyncio.run(get_research("does-not-exist"))
        assert False, "expected NotFoundError"
    except Exception as exc:
        from app.core.exceptions import NotFoundError

        assert isinstance(exc, NotFoundError)
