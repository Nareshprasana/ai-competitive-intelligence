"""Research service: orchestrates the LangGraph workflow for a research request.

Persists research records to PostgreSQL via :class:`app.repositories.research.ResearchRepository`
when a database is configured, falling back to an in-memory store otherwise
(graceful degradation for development/test without PostgreSQL).

Organization ownership is enforced server-side: the owning ``organization_id``
is derived from the request/default settings and never overridden by a
client-supplied value.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.core.database import db
from app.core.checkpoint import AsyncPostgresSaver
from app.core.exceptions import NotFoundError, ResearchError
from app.core.logging import get_logger
from app.graph.builder import get_graph
from app.graph.state import ResearchState
from app.repositories.research import ResearchRepository
from app.schemas.research import (
    ResearchRequest,
    ResearchResult,
    ResearchStatusResponse,
    NodeExecutionMetadata,
)

logger = get_logger("app.services.research_service")

# Fallback in-memory store used only when no database is configured.
# Primary persistence is PostgreSQL via ResearchRepository.
_fallback_store: Dict[str, ResearchResult] = {}
# Backward-compatible alias (existing tests reference _research_store).
_research_store: Dict[str, ResearchResult] = _fallback_store


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


async def _get_repository(session) -> ResearchRepository:
    return ResearchRepository(session)


async def _persist_result(result: ResearchResult) -> None:
    """Persist a research result to PostgreSQL when configured, else fallback."""
    if not db.is_available:
        _fallback_store[result.research_id] = result
        return

    async for session in db.get_session():
        repo = await _get_repository(session)
        await repo.create(
            research_id=result.research_id,
            organization_id=result.organization_id,
            company_name=result.company_name,
            industry=result.industry,
            research_question=result.research_question,
            status=result.status,
            review_status=result.review_status,
            results=result.model_dump(mode="json"),
            errors=result.errors,
        )
        await session.commit()
        break


async def _update_persisted_result(result: ResearchResult) -> None:
    """Update an existing persisted research result (status/results/errors)."""
    if not db.is_available:
        _fallback_store[result.research_id] = result
        return

    async for session in db.get_session():
        repo = await _get_repository(session)
        await repo.update_status(
            research_id=result.research_id,
            organization_id=result.organization_id,
            status=result.status,
            review_status=result.review_status,
            results=result.model_dump(mode="json"),
            errors=result.errors,
        )
        await session.commit()
        break


async def _fetch_from_db(
    research_id: str, organization_id: str
) -> Optional[ResearchResult]:
    """Fetch a research result from PostgreSQL by ID and organization."""
    if not db.is_available:
        return None

    async for session in db.get_session():
        repo = await _get_repository(session)
        row = await repo.get_by_id(research_id, organization_id)
        break
    if row is None:
        return None
    return _row_to_result(row)


def _row_to_result(row: Dict[str, Any]) -> ResearchResult:
    """Convert a repository row dict into a ResearchResult schema.

    The ``results`` column stores the full ``ResearchResult.model_dump()``,
    so nested artifacts (plan, profile, competitors, report, metadata, etc.)
    are read from there. Top-level columns keep the indexed/queryable fields.
    """
    results_payload = row.get("results") or {}
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
        for m in (results_payload.get("execution_metadata") or [])
    ]
    return ResearchResult(
        research_id=row["research_id"],
        status=row["status"],
        company_name=row["company_name"],
        industry=row["industry"],
        research_question=row["research_question"],
        organization_id=row["organization_id"],
        research_plan=results_payload.get("research_plan"),
        company_profile=results_payload.get("company_profile"),
        competitors=results_payload.get("competitors", []),
        product_intelligence=results_payload.get("product_intelligence"),
        market_intelligence=results_payload.get("market_intelligence"),
        evidence=results_payload.get("evidence", []),
        validation_results=results_payload.get("validation_results"),
        strategic_analysis=results_payload.get("strategic_analysis"),
        review_status=row.get("review_status") or results_payload.get("review_status"),
        reviewer_feedback=results_payload.get("reviewer_feedback"),
        final_report=results_payload.get("final_report"),
        errors=row.get("errors", []) or results_payload.get("errors", []),
        execution_metadata=metadata,
        created_at=row.get("created_at") or results_payload.get("created_at"),
        updated_at=row.get("updated_at") or results_payload.get("updated_at"),
    )


async def run_research(
    request: ResearchRequest, *, organization_id: Optional[str] = None
) -> ResearchResult:
    """Execute the full research graph and return structured results.

    The run is synchronous within the request (deterministic mock agents, no
    external calls). Errors from any node are captured in state and reflected
    in the returned status; success is never reported when a node fails.

    When PostgreSQL is configured, the result is persisted via the repository
    and the LangGraph checkpointer is used for thread-based checkpointing.
    """
    if organization_id is None:
        if db.is_available:
            raise ValueError("A validated organization context is required.")
        organization_id = _settings_default_organization_id()
    research_id = f"res-{_new_id()}"

    initial_state = ResearchState(
        research_id=research_id,
        organization_id=organization_id,
        company_name=request.company_name,
        industry=request.industry,
        research_question=request.research_question,
        review_status="started",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
    )

    logger.info(
        "Starting research %s for organization=%s", research_id, organization_id
    )

    graph = get_graph()
    checkpointer: Optional[AsyncPostgresSaver] = None
    config: Optional[Dict[str, Any]] = None

    if db.is_available:
        try:
            checkpointer = await db.get_checkpointer()
            graph = get_graph(checkpointer=checkpointer)
            config = {
                "configurable": {
                    "thread_id": f"org:{organization_id}:research:{research_id}"
                }
            }
        except Exception:  # noqa: BLE001 - degrade gracefully
            logger.warning(
                "Checkpointer unavailable; research will run without checkpoint recovery."
            )
            checkpointer = None
            config = None

    # LangGraph Pydantic state: invoke with the state object. This langgraph
    # version returns the final state as a dict; validate it back into the
    # typed model so downstream code works with attributes.
    invoke_kwargs: Dict[str, Any] = {}
    if config is not None:
        invoke_kwargs["config"] = config
    final_state = await graph.ainvoke(initial_state, **invoke_kwargs)
    if isinstance(final_state, dict):
        final_state = ResearchState(**final_state)

    result = _state_to_result(final_state)

    # Persist to PostgreSQL (or fallback in-memory store).
    await _persist_result(result)

    if result.status == "failed":
        logger.warning("Research %s completed with %d errors", result.research_id, len(result.errors))

    return result


async def get_research(research_id: str, organization_id: Optional[str] = None) -> ResearchStatusResponse:
    """Fetch a previously-run research result by ID.

    When a database is configured, the record is retrieved from PostgreSQL and
    restricted to the owning organization. Otherwise the fallback store is used.
    """
    organization_id = organization_id or _settings_default_organization_id()

    if db.is_available:
        result = await _fetch_from_db(research_id, organization_id)
        if result is not None:
            return ResearchStatusResponse(
                research_id=result.research_id,
                status=result.status,
                results=result,
            )
        raise NotFoundError(
            f"Research {research_id} not found.",
            details={"research_id": research_id},
        )

    result = _fallback_store.get(research_id)
    if result is None:
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
    """Return known research IDs (fallback store when no database)."""
    if db.is_available:
        # Database-backed listing requires a session/repository; return empty
        # here (callers should use the repository directly for DB listing).
        return []
    return list(_fallback_store.keys())


def _new_id() -> str:
    import uuid

    return uuid.uuid4().hex[:12]


__all__ = ["run_research", "get_research", "list_research_ids"]
