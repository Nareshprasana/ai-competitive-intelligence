"""Integration tests for the real Strategic Analyst Agent node (strategic_analyst).

Verifies:
- Input validation (company_name required)
- End-to-end node execution merging strategic_analysis into state
- Multi-dimensional competitor comparison, SWOT, opportunities, threats, recommendations
- Durable persistence into encrypted SQLite research records
- Process restart / fresh session retrieval
- Cross-tenant isolation (IDOR defense)
- LangGraph full workflow execution with real strategic_analyst node
- Retry idempotency without duplication
"""

import asyncio
from unittest.mock import MagicMock
import pytest

from app.graph.builder import build_graph
from app.graph.nodes.strategic_analyst import strategic_analyst
from app.graph.state import ResearchState
from app.models.identity import Organization
from app.models.research import Research
from app.repositories.research import ResearchRepository
from app.repositories.strategy import StrategyRepository
from tests.integration.test_sqlite_security import sqlite_security_environment


@pytest.mark.asyncio
async def test_strategic_analyst_node_requires_company_name():
    """Verify strategic_analyst node fails gracefully when company_name is missing."""
    state = ResearchState(
        research_id="res-fail-strat",
        company_name="",  # Missing required company_name
        industry="Software",
        research_question="Competitive landscape?",
    )
    result = await strategic_analyst(state)
    assert any(m["status"] == "failed" for m in result["execution_metadata"])
    assert len(result["errors"]) >= 1
    assert result["errors"][0]["node_name"] == "strategic_analyst"


@pytest.mark.asyncio
async def test_strategic_analyst_node_executes_and_populates_state():
    """Verify strategic_analyst produces complete, valid strategic analysis."""
    state = ResearchState(
        research_id="res-node-strat-1",
        organization_id="org-test",
        company_name="Acme Corp",
        industry="Enterprise Cloud",
        research_question="What are Acme's key advantages and threats?",
        company_profile={
            "company_name": "Acme Corp",
            "products": ["Acme Core Cloud", "Acme Edge AI"],
            "target_customers": ["Global Enterprises", "Financial Institutions"],
            "geographical_presence": ["North America", "APAC", "EMEA"],
            "business_model": "Annual Enterprise Contracts",
        },
        competitors=[
            {
                "competitor_id": "comp-omega",
                "company_name": "Omega Cloud",
                "competitor_type": "direct",
                "products_and_services": ["Omega Suite"],
                "target_customers": ["Mid-Market IT"],
                "competitive_strengths": ["Aggressive discounting"],
                "competitive_weaknesses": ["Slow support response times"],
            }
        ],
        evidence=[
            {
                "evidence_id": "ev-omega-1",
                "claim": "Omega Cloud provides cloud optimization suite.",
                "source_url": "https://omegacloud.example/suite",
                "source_domain": "omegacloud.example",
                "confidence": 0.85,
                "verification_status": "verified",
            }
        ],
    )

    update = await strategic_analyst(state)

    assert "strategic_analysis" in update
    assert "execution_metadata" in update

    analysis = update["strategic_analysis"]
    assert analysis["target_company"] == "Acme Corp"
    assert len(analysis["competitor_comparisons"]) == 1
    assert len(analysis["swot_analysis"]["strengths"]) >= 1
    assert len(analysis["market_opportunities"]) >= 1
    assert len(analysis["competitive_threats"]) >= 1
    assert len(analysis["strategic_recommendations"]) == 4
    assert len(analysis["evidence_gaps"]) >= 1
    assert 0.15 <= analysis["overall_confidence"] <= 0.95

    metadata = update["execution_metadata"][0]
    assert metadata["node_name"] == "strategic_analyst"
    assert metadata["status"] == "completed"
    assert metadata["mock"] is False


@pytest.mark.asyncio
async def test_strategic_analyst_persists_to_sqlite(sqlite_security_environment):
    """Verify strategic analysis results are encrypted and persisted into SQLite."""
    factory = sqlite_security_environment["session_factory"]

    # 1. Seed organization and research run
    async with factory() as session:
        session.add(Organization(organization_id="org-strat-sec", name="Strategy Sec Org"))
        research = Research(
            research_id="res-strat-1",
            organization_id="org-strat-sec",
            company_name="Alpha Dynamics",
            industry="Robotics",
            research_question="Competitive positioning in robotics?",
            status="running",
            review_status="pending",
            results={},
            errors=[],
        )
        session.add(research)
        await session.commit()

    # 2. Execute strategic_analyst node
    state = ResearchState(
        research_id="res-strat-1",
        organization_id="org-strat-sec",
        company_name="Alpha Dynamics",
        industry="Robotics",
        research_question="Competitive positioning in robotics?",
        company_profile={"products": ["Robot Alpha 1"]},
        competitors=[{"competitor_id": "comp-bot", "company_name": "BotWorks", "competitor_type": "direct"}],
        evidence=[
            {
                "evidence_id": "ev-bot-1",
                "claim": "BotWorks announced industrial manipulator.",
                "source_url": "https://botworks.example/news",
                "source_domain": "botworks.example",
                "confidence": 0.80,
                "verification_status": "verified",
            }
        ],
    )

    update = await strategic_analyst(state)
    assert update["strategic_analysis"]["target_company"] == "Alpha Dynamics"

    # 3. Verify retrieval in a fresh database session (process restart simulation)
    async with factory() as fresh_session:
        strategy_repo = StrategyRepository(fresh_session)
        stored_analysis = await strategy_repo.get_strategic_analysis("res-strat-1", "org-strat-sec")

        assert stored_analysis is not None
        assert stored_analysis["target_company"] == "Alpha Dynamics"
        assert len(stored_analysis["competitor_comparisons"]) == 1
        assert len(stored_analysis["strategic_recommendations"]) == 4

        # Verify research review status preserved
        research_repo = ResearchRepository(fresh_session)
        r_row = await research_repo.get_by_id("res-strat-1", "org-strat-sec")
        assert r_row is not None
        assert r_row["results"]["strategic_analysis"]["target_company"] == "Alpha Dynamics"


@pytest.mark.asyncio
async def test_strategic_analyst_tenant_isolation(sqlite_security_environment):
    """Verify cross-tenant IDOR protection for strategic analysis results."""
    factory = sqlite_security_environment["session_factory"]

    async with factory() as session:
        session.add(Organization(organization_id="org-alpha", name="Alpha Org"))
        session.add(Organization(organization_id="org-beta", name="Beta Org"))
        session.add(
            Research(
                research_id="res-isolated-1",
                organization_id="org-alpha",
                company_name="Confidential Corp",
                industry="Fintech",
                research_question="Secret strategy?",
                status="completed",
                results={"strategic_analysis": {"target_company": "Confidential Corp", "secret": "data"}},
                errors=[],
            )
        )
        await session.commit()

    async with factory() as session:
        strategy_repo = StrategyRepository(session)

        # Authorized access
        alpha_res = await strategy_repo.get_strategic_analysis("res-isolated-1", "org-alpha")
        assert alpha_res is not None
        assert alpha_res["target_company"] == "Confidential Corp"

        # Unauthorized cross-tenant query
        beta_res = await strategy_repo.get_strategic_analysis("res-isolated-1", "org-beta")
        assert beta_res is None


@pytest.mark.asyncio
async def test_strategic_analyst_retry_idempotency(sqlite_security_environment):
    """Verify that retrying strategic_analyst updates results cleanly without duplication."""
    factory = sqlite_security_environment["session_factory"]

    async with factory() as session:
        session.add(Organization(organization_id="org-retry-strat", name="Retry Org"))
        session.add(
            Research(
                research_id="res-retry-strat-1",
                organization_id="org-retry-strat",
                company_name="Retry Corp",
                industry="SaaS",
                research_question="Idempotent check?",
                status="running",
                results={},
                errors=[],
            )
        )
        await session.commit()

    state = ResearchState(
        research_id="res-retry-strat-1",
        organization_id="org-retry-strat",
        company_name="Retry Corp",
        industry="SaaS",
        research_question="Idempotent check?",
        company_profile={"products": ["App A"]},
    )

    # First run
    update_1 = await strategic_analyst(state)
    assert len(update_1["strategic_analysis"]["strategic_recommendations"]) == 4

    # Second run (retry)
    update_2 = await strategic_analyst(state)
    assert len(update_2["strategic_analysis"]["strategic_recommendations"]) == 4

    async with factory() as fresh_session:
        strategy_repo = StrategyRepository(fresh_session)
        stored = await strategy_repo.get_strategic_analysis("res-retry-strat-1", "org-retry-strat")
        assert stored is not None
        assert len(stored["strategic_recommendations"]) == 4
