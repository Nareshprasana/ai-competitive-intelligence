"""Research service: orchestrates the LangGraph workflow for a research request."""

from datetime import datetime, timezone
from typing import Any, Dict, List

from app.core.config import get_settings
from app.core.database import db
from app.core.exceptions import ResearchError
from app.core.logging import get_logger
from app.graph.builder import get_graph
from app.graph.state import ResearchState
from app.schemas.research import (
    ResearchRequest,
    ResearchResult,
    ResearchStatusResponse,
    NodeExecutionMetadata,
)

logger = get_logger("app.services.research_service")

# In-memory store for research results (Phase 1). Replaced by database-backed
# persistence in a later phase once PostgreSQL is available.
_research_store: Dict[str, ResearchResult] = {}


def _settings_default_organization_id() -> str:
    return get_settings().default_organization_id


def _state_to_result(state: ResearchState) -> ResearchResult:
    """Convert a final ResearchState into a ResearchResult schema."""
    errors: List[Dict[str, Any]] = list(state.errors or [])
    metadata = [
        NodeExecutionMetadata(
            node_name=m.get("node_name", "unknown"),
            status=m.get("status", "unknown"),
            started_at=m.get("started_at", ""),
            completed_at=m.get("completed_at", ""),
            duration_ms=m.get("duration_ms", 0.0),
            mock=m.get("mock", True),
            details=m.get("details", {}),
        )
        for m in (state.execution_metadata or [])
    ]

    status = "failed" if errors else "completed"

    return ResearchResult(
        research_id=state.research_id,
        status=status,
        company_name=state.company_name,
        industry=state.industry,
        research_question=state.research_question,
        organization_id=state.organization_id,
        research_plan=state.research_plan,
        company_profile=state.company_profile,
        competitors=list(state.competitors or []),
        product_intelligence=state.product_intelligence,
        market_intelligence=state.market_intelligence,
        evidence=list(state.evidence or []),
        validation_results=state.validation_results,
        strategic_analysis=state.strategic_analysis,
        review_status=state.review_status,
        reviewer_feedback=state.reviewer_feedback,
        final_report=state.final_report,
        errors=errors,
        execution_metadata=metadata,
        created_at=state.created_at,
        updated_at=state.updated_at,
    )


async def run_research(request: ResearchRequest) -> ResearchResult:
    """Execute the full research graph and return structured results.

    The run is synchronous within the request (deterministic mock agents, no
    external calls). Errors from any node are captured in state and reflected
    in the returned status; success is never reported when a node fails.
    """
    organization_id = request.organization_id or _settings_default_organization_id()

    initial_state = ResearchState(
        research_id=f"res-{_new_id()}",
        organization_id=organization_id,
        company_name=request.company_name,
        industry=request.industry,
        research_question=request.research_question,
        review_status="started",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
    )

    logger.info("Starting research %s for %s", initial_state.research_id, request.company_name)

    graph = get_graph()
    # LangGraph Pydantic state: invoke with the state object. This langgraph
    # version returns the final state as a dict; validate it back into the
    # typed model so downstream code works with attributes.
    final_state = await graph.ainvoke(initial_state)
    if isinstance(final_state, dict):
        final_state = ResearchState(**final_state)

    result = _state_to_result(final_state)

    # Persist in-memory for GET /research/{id}. Degradation note: without a
    # database, results live only in memory for this process.
    _research_store[result.research_id] = result

    if result.status == "failed":
        logger.warning("Research %s completed with %d errors", result.research_id, len(result.errors))

    return result


async def get_research(research_id: str) -> ResearchStatusResponse:
    """Fetch a previously-run research result by ID."""
    result = _research_store.get(research_id)
    if result is None:
        # Also check the database if configured (Phase 2 persistence).
        from app.core.exceptions import NotFoundError

        raise NotFoundError(
            f"Research {research_id} not found.",
            details={"research_id": research_id},
        )
    return ResearchStatusResponse(
        research_id=result.research_id,
        status=result.status,
        results=result,
    )


def list_research_ids() -> List[str]:
    """Return known research IDs (in-memory store)."""
    return list(_research_store.keys())


def _new_id() -> str:
    import uuid

    return uuid.uuid4().hex[:12]


__all__ = ["run_research", "get_research", "list_research_ids"]
