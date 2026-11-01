"""strategic_analyst_mock node: deterministic mock strategic analysis."""

from app.graph.nodes.base import run_node
from app.graph.state import ResearchState


async def _strategic_analyst(state: ResearchState) -> dict:
    analysis = {
        "opportunities": [
            {
                "id": "opp-1",
                "title": "Underserved segment in " + state.industry,
                "description": "Mock opportunity identified from market gap analysis.",
                "priority": "high",
            }
        ],
        "threats": [
            {
                "id": "thr-1",
                "title": "Established competitors",
                "description": "Mock threat: multiple direct competitors identified.",
                "severity": "medium",
            }
        ],
        "recommendations": [
            "Validate mock findings with primary research before acting.",
            "Differentiate " + state.company_name + " on pricing and customer experience.",
        ],
        "note": "Deterministic mock strategic analysis (Phase 1). Not real strategic advice.",
    }
    return {
        "strategic_analysis": analysis,
        "_metadata_details": {
            "opportunity_count": len(analysis["opportunities"]),
            "threat_count": len(analysis["threats"]),
        },
    }


async def strategic_analyst_mock(state: ResearchState) -> dict:
    """Return deterministic mock strategic analysis (not real analysis)."""
    if not state.competitors:
        raise ValueError("Competitor data is required for strategic analysis.")
    return await run_node(
        node_name="strategic_analyst_mock",
        state=state,
        node_fn=_strategic_analyst,
        mock=True,
    )
