"""research_planner node: produces a deterministic research plan from inputs."""

from app.graph.nodes.base import run_node
from app.graph.state import ResearchState


async def _research_planner(state: ResearchState) -> dict:
    plan = {
        "plan_id": f"plan-{state.research_id}",
        "company_name": state.company_name,
        "industry": state.industry,
        "research_question": state.research_question,
        "steps": [
            "initialize_research",
            "research_planner",
            "company_researcher",
            "competitor_discovery",
            "evidence_validator_mock",
            "strategic_analyst_mock",
            "report_generator_mock",
            "finalize_research",
        ],
        "focus_areas": [
            "company_profile",
            "competitor_discovery",
            "product_intelligence",
            "market_intelligence",
            "evidence_validation",
            "strategic_analysis",
        ],
        "note": "Deterministic mock plan (Phase 1). No external research performed.",
    }
    return {
        "research_plan": plan,
        "_metadata_details": {"steps": len(plan["steps"])},
    }


async def research_planner(state: ResearchState) -> dict:
    """Create the research plan that guides the remaining mock agents."""
    if not state.company_name or not state.research_question:
        raise ValueError("company_name and research_question are required to plan research.")
    return await run_node(
        node_name="research_planner",
        state=state,
        node_fn=_research_planner,
        mock=True,
    )
