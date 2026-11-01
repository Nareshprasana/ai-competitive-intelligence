"""competitor_discovery_mock node: deterministic mock competitor list."""

from app.graph.nodes.base import run_node
from app.graph.state import ResearchState


async def _competitor_discovery(state: ResearchState) -> dict:
    competitors = [
        {
            "competitor_id": f"comp-{i}",
            "name": f"Mock Competitor {i} ({state.industry})",
            "industry": state.industry,
            "relationship": "direct",
            "strength": "moderate",
            "note": "Deterministic mock data from competitor_discovery_mock; no real discovery performed.",
        }
        for i in range(1, 4)
    ]
    return {
        "competitors": competitors,
        "_metadata_details": {"competitor_count": len(competitors)},
    }


async def competitor_discovery_mock(state: ResearchState) -> dict:
    """Return a deterministic mock list of competitors (not real discovery)."""
    if not state.industry:
        raise ValueError("industry is required for competitor discovery.")
    return await run_node(
        node_name="competitor_discovery_mock",
        state=state,
        node_fn=_competitor_discovery,
        mock=True,
    )
