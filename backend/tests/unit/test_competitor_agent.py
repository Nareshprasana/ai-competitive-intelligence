"""Tests for the Company Research Agent with mocked LLM and search provider."""

import asyncio

from app.agents.competitor_researcher import CompetitorResearcherAgent
from app.core.llm import LLMMessage, LLMResponse
from app.tools.search.providers.mock import MockSearchProvider


class FakeLLMClient:
    """Fake LLM client that returns structured competitor data."""

    def __init__(self, competitors):
        self.competitors = competitors
        self.call_count = 0

    def is_available(self):
        return True

    async def complete(self, messages, **kwargs):
        self.call_count += 1
        import json

        return LLMResponse(
            content=json.dumps(self.competitors),
            model="test-model",
            provider="mock",
            usage={},
        )

    async def complete_structured(self, messages, response_model, **kwargs):
        self.call_count += 1
        import json

        content = json.dumps(self.competitors[0] if self.competitors else {})
        return response_model.model_validate_json(content)

    async def close(self):
        pass


class UnavailableLLMClient:
    def is_available(self):
        return False

    async def close(self):
        pass


def _make_agent(competitors=None, mock_results=None):
    provider = MockSearchProvider(results=mock_results)
    from app.agents.base import AgentBudget

    agent = CompetitorResearcherAgent(
        provider, budget=AgentBudget(max_search_queries=4)
    )
    if competitors is not None:
        agent._llm_client = FakeLLMClient(competitors)
    else:
        agent._llm_client = UnavailableLLMClient()
    return agent, provider


def _company_profile():
    return {
        "description": (
            "Enterprise AI platform serving enterprise businesses on SaaS plans."
        ),
        "products": ["Enterprise AI platform"],
        "target_customers": ["Enterprise businesses"],
        "geographical_presence": ["North America"],
        "business_model": "SaaS subscriptions",
    }


def test_agent_competitor_discovery_with_llm():
    competitors = [
        {
            "company_name": "BetaAI",
            "website": "https://betaai.com",
            "competitor_type": "direct",
            "company_description": (
                "Enterprise AI platform serving enterprise businesses on SaaS plans."
            ),
            "products_and_services": ["Enterprise AI platform"],
            "target_customers": ["Enterprise businesses"],
            "geographic_markets": ["North America"],
            "competitive_strengths": ["Strong R&D"],
            "competitive_weaknesses": ["High price"],
            "evidence": [
                {
                    "claim": (
                        "BetaAI offers an enterprise AI platform to enterprise "
                        "businesses in North America through SaaS subscriptions."
                    ),
                    "source_url": "https://betaai.com",
                    "source_title": "BetaAI",
                }
            ],
        }
    ]
    custom_results = {
        "acme corp competitors ai software": [
            {
                "url": "https://betaai.com",
                "title": "BetaAI - Enterprise AI Platform",
                "snippet": (
                    "BetaAI offers an enterprise AI platform to enterprise "
                    "businesses in North America through SaaS subscriptions."
                ),
                "source_domain": "betaai.com",
                "published_at": None,
            }
        ]
    }
    agent, provider = _make_agent(competitors, custom_results)

    result = asyncio.run(
        agent.discover(
            company_name="acme corp",
            industry="AI Software",
            research_question="Who are the competitors?",
            research_id="res-test-1",
            company_profile=_company_profile(),
        )
    )

    assert result["competitors"] is not None
    assert len(result["competitors"]) == 1
    assert result["competitors"][0]["company_name"] == "BetaAI"
    assert result["competitors"][0]["competitor_type"] == "direct"
    assert result["competitors"][0]["website"] == "https://betaai.com"
    assert result["competitors"][0]["qualification_score"] >= 0.65
    assert result["competitors"][0]["qualification_factors"]["product_similarity"] == 1.0
    assert result["competitors"][0]["evidence"][0]["source_url"] == "https://betaai.com"
    assert result["competitors"][0]["evidence"][0]["evidence_type"] == "official_website"
    assert result["competitors"][0]["evidence"][0]["claim"] == (
        "BetaAI offers an enterprise AI platform to enterprise businesses in "
        "North America through SaaS subscriptions."
    )
    assert result["competitors"][0]["competitive_strengths"] == []
    assert result["competitors"][0]["competitive_weaknesses"] == []
    assert result["competitors"][0]["source_references"] == ["https://betaai.com"]
    assert result["_metadata_details"]["llm_available"] is True


def test_agent_competitor_discovery_without_llm():
    agent, provider = _make_agent(competitors=None)

    result = asyncio.run(
        agent.discover(
            company_name="Acme Corp",
            industry="AI Software",
            research_question="Who are the competitors?",
            research_id="res-test-2",
        )
    )

    assert result["competitors"] is not None
    assert len(result["competitors"]) >= 0
    assert result["_metadata_details"]["llm_available"] is False


def test_agent_rejects_empty_company_name():
    agent, provider = _make_agent()

    try:
        asyncio.run(
            agent.discover(
                company_name="",
                industry="AI",
                research_question="q",
                research_id="res-test-3",
            )
        )
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_competitor_profiles_have_required_fields():
    competitors = [
        {
            "company_name": "BetaAI",
            "website": "https://betaai.com",
            "competitor_type": "direct",
            "company_description": "AI company.",
            "products_and_services": ["AI Platform"],
            "target_customers": ["Enterprise"],
            "geographic_markets": ["North America"],
            "competitive_strengths": ["Strong R&D"],
            "competitive_weaknesses": ["High price"],
            "evidence": [
                {
                    "claim": (
                        "BetaAI offers an enterprise AI platform to enterprise "
                        "businesses in North America through SaaS subscriptions."
                    ),
                    "source_url": "https://betaai.com",
                }
            ],
        }
    ]
    results = {
        "acme corp competitors ai software": [
            {
                "url": "https://betaai.com",
                "title": "BetaAI - Enterprise AI Platform",
                "snippet": (
                    "BetaAI offers an enterprise AI platform to enterprise "
                    "businesses in North America through SaaS subscriptions."
                ),
                "source_domain": "betaai.com",
            }
        ]
    }
    agent, provider = _make_agent(competitors, results)

    result = asyncio.run(
        agent.discover(
            company_name="Acme Corp",
            industry="AI Software",
            research_question="q",
            research_id="res-test-4",
            company_profile=_company_profile(),
        )
    )

    for comp in result["competitors"]:
        assert "competitor_id" in comp
        assert "company_name" in comp
        assert "competitor_type" in comp
        assert comp["competitor_type"] in ("direct", "indirect", "emerging", "substitute")
        assert "qualification_score" in comp
        assert 0.0 <= comp["qualification_score"] <= 1.0
        assert isinstance(comp["qualification_factors"], dict)
        assert "evidence" in comp
        for ev in comp["evidence"]:
            assert "claim" in ev
            assert "source_url" in ev
            assert "source_domain" in ev
            assert "confidence" in ev


def test_conflicting_source_status_and_duplicate_candidates_are_preserved():
    snippet = (
        "BetaAI offers an enterprise AI platform to enterprise businesses in "
        "North America through SaaS subscriptions."
    )
    candidates = [
        {
            "company_name": "BetaAI",
            "company_description": _company_profile()["description"],
            "products_and_services": ["Enterprise AI platform"],
            "target_customers": ["Enterprise businesses"],
            "geographic_markets": ["North America"],
            "evidence": [
                {
                    "claim": (
                        "BetaAI is a startup that recently launched an enterprise "
                        "AI platform for enterprise businesses in North America."
                    ),
                    "source_url": "https://industry.example/betaai",
                    "verification_status": "conflicting",
                }
            ],
        },
        {
            "company_name": "Beta AI",
            "company_description": _company_profile()["description"],
            "products_and_services": ["Enterprise AI platform"],
            "target_customers": ["Enterprise businesses"],
            "geographic_markets": ["North America"],
        },
    ]
    results = {
        "acme corp competitors ai software": [
            {
                "url": "https://betaai.com",
                "title": "BetaAI",
                "snippet": snippet,
                "source_domain": "betaai.com",
            },
            {
                "url": "https://industry.example/betaai",
                "title": "BetaAI market analysis",
                "snippet": (
                    "BetaAI is a startup that recently launched an enterprise "
                    "AI platform for enterprise businesses in North America."
                ),
                "source_domain": "industry.example",
            },
        ]
    }
    agent, _ = _make_agent(candidates, results)
    result = asyncio.run(
        agent.discover(
            company_name="Acme Corp",
            industry="AI Software",
            research_question="Who are the competitors?",
            research_id="res-conflict",
            company_profile=_company_profile(),
        )
    )
    assert len(result["competitors"]) == 1
    profile = result["competitors"][0]
    assert profile["competitor_type"] == "emerging"
    assert len(profile["evidence"]) == 2
    assert profile["evidence"][0]["source_url"] == "https://betaai.com"
    assert any(item["verification_status"] == "conflicting" for item in profile["evidence"])
    assert profile["verification_status"] == "conflicting"
    assert len(set(profile["source_references"])) == 2


def test_independent_source_corroboration_and_unknown_fields_are_explicit():
    snippet = (
        "BetaAI offers an enterprise AI platform to enterprise businesses in "
        "North America through SaaS subscriptions."
    )
    candidate = {
        "company_name": "BetaAI",
        "company_description": _company_profile()["description"],
        "products_and_services": ["Enterprise AI platform"],
        "target_customers": ["Enterprise businesses"],
    }
    results = {
        "acme corp competitors ai software": [
            {
                "url": "https://betaai.com",
                "title": "BetaAI",
                "snippet": snippet,
                "source_domain": "betaai.com",
            },
            {
                "url": "https://industry.example/betaai",
                "title": "BetaAI profile",
                "snippet": snippet,
                "source_domain": "industry.example",
            },
        ]
    }
    agent, _ = _make_agent([candidate], results)
    result = asyncio.run(
        agent.discover(
            company_name="Acme Corp",
            industry="AI Software",
            research_question="Who are the competitors?",
            research_id="res-corroboration",
            company_profile=_company_profile(),
        )
    )
    profile = result["competitors"][0]
    assert profile["verification_status"] == "partially_verified"
    assert all(
        item["verification_status"] == "partially_verified"
        for item in profile["evidence"]
    )
    assert "geographic_markets" in profile["unknown_information"]


def test_industry_only_candidate_is_not_qualified():
    candidate = {
        "company_name": "OtherCo",
        "company_description": "OtherCo sells unrelated packaged food.",
        "products_and_services": ["Packaged food"],
        "target_customers": ["Grocery stores"],
        "evidence": [],
    }
    results = {
        "acme corp competitors ai software": [
            {
                "url": "https://otherco.com",
                "title": "OtherCo",
                "snippet": "OtherCo sells unrelated packaged food.",
                "source_domain": "otherco.com",
            }
        ]
    }
    agent, _ = _make_agent([candidate], results)
    result = asyncio.run(
        agent.discover(
            company_name="Acme Corp",
            industry="AI Software",
            research_question="Who are the competitors?",
            research_id="res-unrelated",
            company_profile=_company_profile(),
        )
    )
    assert result["competitors"] == []


def test_search_failure_is_reported_without_losing_discovery_state():
    class FailingProvider:
        name = "failing"

        async def search(self, query):
            raise RuntimeError("search unavailable")

        async def close(self):
            return None

    from app.agents.base import AgentBudget

    agent = CompetitorResearcherAgent(
        FailingProvider(), budget=AgentBudget(max_search_queries=1)
    )
    agent._llm_client = UnavailableLLMClient()
    result = asyncio.run(
        agent.discover(
            company_name="Acme Corp",
            industry="AI",
            research_question="Who competes?",
            research_id="res-search-failure",
        )
    )
    assert result["competitors"] == []
    assert result["_metadata_details"]["search_failures"] == 1


def test_llm_failure_falls_back_to_unverified_source_extraction():
    class FailingLLM:
        def is_available(self):
            return True

        async def complete(self, messages, **kwargs):
            raise RuntimeError("temporary model failure")

        async def close(self):
            return None

    results = {
        "acme corp competitors ai software": [
            {
                "url": "https://betaai.com",
                "title": "BetaAI - Enterprise AI Platform",
                "snippet": (
                    "BetaAI offers an enterprise AI platform to enterprise "
                    "businesses in North America through SaaS subscriptions."
                ),
                "source_domain": "betaai.com",
            }
        ]
    }
    agent, _ = _make_agent(mock_results=results)
    agent._llm_client = FailingLLM()
    result = asyncio.run(
        agent.discover(
            company_name="Acme Corp",
            industry="AI Software",
            research_question="Who are the competitors?",
            research_id="res-llm-failure",
            company_profile=_company_profile(),
        )
    )
    assert result["_metadata_details"]["llm_available"] is True
    assert result["_metadata_details"]["llm_extraction_failed"] is True
    assert result["_metadata_details"]["extraction_strategy"] == "heuristic"
    assert result["_metadata_details"]["candidates_extracted"] == 1


def test_llm_cannot_inject_an_unretrieved_evidence_url():
    candidates = [
        {
            "company_name": "BetaAI",
            "company_description": "Enterprise AI platform.",
            "products_and_services": ["Enterprise AI platform"],
            "target_customers": ["Enterprise businesses"],
            "geographic_markets": ["North America"],
            "evidence": [
                {
                    "claim": "Invented claim",
                    "source_url": "https://attacker.example/forged",
                    "source_title": "Forged",
                }
            ],
        }
    ]
    results = {
        "acme corp competitors ai software": [
            {
                "url": "https://betaai.com",
                "title": "BetaAI - Enterprise AI Platform",
                "snippet": (
                    "BetaAI offers an enterprise AI platform to enterprise "
                    "businesses in North America through SaaS subscriptions."
                ),
                "source_domain": "betaai.com",
            }
        ]
    }
    agent, _ = _make_agent(candidates, results)
    result = asyncio.run(
        agent.discover(
            company_name="Acme Corp",
            industry="AI Software",
            research_question="Who are the competitors?",
            research_id="res-citation-check",
            company_profile=_company_profile(),
        )
    )
    assert result["competitors"]
    assert all(
        evidence["source_url"] == "https://betaai.com"
        for evidence in result["competitors"][0]["evidence"]
    )
    assert all(
        evidence["claim"] != "Invented claim"
        for evidence in result["competitors"][0]["evidence"]
    )


def test_reused_company_search_results_are_not_searched_again():
    agent, provider = _make_agent(competitors=None)
    prior = {
        "url": "https://betaai.com",
        "title": "BetaAI competitors",
        "snippet": "BetaAI offers an enterprise AI platform.",
        "source_domain": "betaai.com",
        "query": "acme corp competitors ai software",
        "provider": "mock",
    }
    result = asyncio.run(
        agent.discover(
            company_name="Acme Corp",
            industry="AI Software",
            research_question="Who are the competitors?",
            research_id="res-reuse",
            company_profile=_company_profile(),
            prior_search_results=[prior],
        )
    )
    assert provider.call_count == 3
    assert result["_metadata_details"]["results_found"] >= 1


__all__ = []
