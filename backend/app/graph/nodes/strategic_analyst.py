"""strategic_analyst node: real AI-powered Strategic Analyst Agent (Phase 2F).

Replaces the deterministic mock strategic_analyst_mock. This node invokes the
StrategicAnalystAgent which ingests validated company profile, competitor discovery,
evidence items, and validation results from ResearchState, generating:
- Strategic company profiles
- Multi-dimensional competitor comparisons
- Macro positioning, vulnerability, and gap analysis
- Structured SWOT analysis with explicit assumptions and confidence scores
- Market opportunities with qualitative impact and execution feasibility
- Competitive threats with severity, likelihood, and mitigation strategies
- Actionable, prioritized recommendations across immediate to long-term horizons
- Evidence gap detection and unresolved contradiction tracking
- Deterministic, explainable confidence scoring

Results are durably persisted to the database within encrypted research storage
using strict organization tenant isolation.
"""

from typing import Any, Dict, Optional

from app.agents.strategic_analyst import StrategicAnalystAgent
from app.core.config import get_settings
from app.core.database import db
from app.core.logging import get_logger
from app.graph.nodes.base import run_node
from app.graph.state import ResearchState
from app.repositories.strategy import StrategyRepository

logger = get_logger("app.graph.nodes.strategic_analyst")


async def _persist_strategic_analysis(
    *,
    research_id: str,
    organization_id: str,
    strategic_analysis: Dict[str, Any],
) -> None:
    """Persist strategic analysis results with organization-scoped tenant isolation."""
    async for session in db.get_session():
        strategy_repo = StrategyRepository(session)
        review_status = (
            "requires_review"
            if strategic_analysis.get("analysis_status") == "requires_review"
            else None
        )
        await strategy_repo.save_strategic_analysis(
            research_id=research_id,
            organization_id=organization_id,
            strategic_analysis=strategic_analysis,
            review_status=review_status,
        )
        await session.commit()
        break


async def _strategic_analyst(state: ResearchState) -> dict:
    """Run the Strategic Analyst Agent and return state update."""
    if not state.company_name:
        raise ValueError("company_name is required for strategic analysis.")

    organization_id = state.organization_id or get_settings().default_organization_id
    research_id = state.research_id

    agent = StrategicAnalystAgent()
    result = await agent.analyze_state(state)
    analysis_dict = result.model_dump(mode="json")

    # Persist to database if research_id is present
    if research_id:
        try:
            await _persist_strategic_analysis(
                research_id=research_id,
                organization_id=organization_id,
                strategic_analysis=analysis_dict,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Strategic analysis persistence failed research_id=%s error=%s",
                research_id,
                exc,
            )

    return {
        "strategic_analysis": analysis_dict,
        "_metadata_details": {
            "overall_confidence": result.overall_confidence,
            "swot_strengths": len(result.swot_analysis.strengths),
            "swot_weaknesses": len(result.swot_analysis.weaknesses),
            "swot_opportunities": len(result.swot_analysis.opportunities),
            "swot_threats": len(result.swot_analysis.threats),
            "opportunities_count": len(result.market_opportunities),
            "threats_count": len(result.competitive_threats),
            "recommendations_count": len(result.strategic_recommendations),
            "evidence_gaps_count": len(result.evidence_gaps),
            "analysis_status": result.analysis_status,
        },
    }


async def strategic_analyst(state: ResearchState) -> dict:
    """Execute real Strategic Analyst Agent LangGraph node."""
    return await run_node(
        node_name="strategic_analyst",
        state=state,
        node_fn=_strategic_analyst,
        mock=False,
    )


__all__ = ["strategic_analyst", "_strategic_analyst", "_persist_strategic_analysis"]
