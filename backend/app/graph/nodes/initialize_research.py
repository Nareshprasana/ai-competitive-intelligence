"""initialize_research node: sets up research identifiers and initial status."""

import uuid
from datetime import datetime, timezone

from app.graph.nodes.base import run_node, utc_now_iso
from app.graph.state import ResearchState


async def _initialize_research(state: ResearchState) -> dict:
    research_id = state.research_id or f"res-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    return {
        "research_id": research_id,
        "review_status": "started",
        "created_at": now,
        "updated_at": now,
        "_metadata_details": {"research_id": research_id},
    }


async def initialize_research(state: ResearchState) -> dict:
    """Initialize a research run: assign/research_id and mark it started."""
    return await run_node(
        node_name="initialize_research",
        state=state,
        node_fn=_initialize_research,
        mock=True,
    )
