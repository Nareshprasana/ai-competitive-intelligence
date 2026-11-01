"""Tests for the Company Research Agent with mocked LLM and search provider."""

import asyncio

from app.agents.company_researcher import CompanyResearcherAgent
from app.core.config import get_settings
from app.core.llm import LLMConfig, LLMMessage, OpenRouterLLMClient
from app.core.exceptions import LLMConfigurationError
from app.schemas.company import CompanyProfile
from app.schemas.evidence import VerificationStatus
from app.tools.search.providers.mock import MockSearchProvider
from app.tools.search.schemas import SearchQuery


class FakeLLMClient:
    """Fake LLM client that returns a structured company profile."""

    def __init__(self, profile: CompanyProfile):
        self.profile = profile
        self.call_count = 0

    def is_available(self):
        return True

    async def complete(self, messages, **kwargs):
        self.call_count += 1
        from app.core.llm import LLMResponse
        return LLMResponse(
            content=self.profile.model_dump_json(),
            model="test-model",
            provider="mock",
            usage={},
        )

    async def complete_structured(self, messages, response_model, **kwargs):
        self.call_count += 1
        return self.profile

    async def close(self):
        pass


class UnavailableLLMClient:
    def is_available(self):
        return False

    async def close(self):
        pass


def _make_agent(profile=None):
    provider = MockSearchProvider()
    agent = CompanyResearcherAgent(
        provider, budget=__import__("app.agents.base", fromlist=["AgentBudget"]).AgentBudget(max_search_queries=4)
    )
    if profile is not None:
        agent._llm_client = FakeLLMClient(profile)
    else:
        agent._llm_client = UnavailableLLMClient()
    return agent, provider


def test_agent_research_with_llm():
    profile = CompanyProfile(
        company_name="Acme Corp",
        industry="AI Software",
        description="Leading AI software company.",
        headquarters="San Francisco, CA",
        products=["Platform A"],
    )
    agent, provider = _make_agent(profile)

    result = asyncio.run(
        agent.research(
            company_name="Acme Corp",
            industry="AI Software",
            research_question="What does Acme Corp do?",
            research_id="res-test-1",
        )
    )

    assert result["company_profile"] is not None
    assert result["company_profile"]["company_name"] == "Acme Corp"
    assert result["company_profile"]["industry"] == "AI Software"
    assert len(result["evidence"]) > 0
    assert result["search_results"]
    assert result["_metadata_details"]["llm_available"] is True


def test_agent_research_without_llm():
    """Without LLM config, falls back to search-snippet profile."""
    agent, provider = _make_agent(profile=None)
    result = asyncio.run(
        agent.research(
            company_name="Acme Corp",
            industry="AI Software",
            research_question="What does Acme Corp do?",
            research_id="res-test-2",
        )
    )

    assert result["company_profile"] is not None
    assert result["company_profile"]["company_name"] == "Acme Corp"
    # Snippet-based profile should have unverified evidence
    assert len(result["evidence"]) > 0
    assert result["_metadata_details"]["llm_available"] is False


def test_agent_budget_limits_searches():
    profile = CompanyProfile(company_name="Acme Corp")
    agent, provider = _make_agent(profile)
    agent.budget.max_search_queries = 2

    result = asyncio.run(
        agent.research(
            company_name="Acme Corp",
            industry="AI Software",
            research_question="q",
            research_id="res-test-3",
        )
    )
    # Should not exceed the search budget
    assert provider.call_count <= 2


def test_agent_rejects_empty_company_name():
    agent, provider = _make_agent()
    try:
        asyncio.run(
            agent.research(
                company_name="",
                industry="AI",
                research_question="q",
                research_id="res-test-4",
            )
        )
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_evidence_items_have_provenance():
    profile = CompanyProfile(company_name="Acme Corp")
    agent, provider = _make_agent(profile)
    result = asyncio.run(
        agent.research(
            company_name="Acme Corp",
            industry="AI Software",
            research_question="q",
            research_id="res-test-5",
        )
    )
    for ev in result["evidence"]:
        assert "evidence_id" in ev
        assert "claim" in ev
        assert "source_url" in ev
        assert "source_domain" in ev
        assert "confidence" in ev
        assert "verification_status" in ev


__all__ = []
