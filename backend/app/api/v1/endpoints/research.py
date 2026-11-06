"""Research endpoints.

POST /api/v1/research   - submit and execute a research run
GET  /api/v1/research/{research_id} - fetch a research run's status and results
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.schemas.research import ResearchRequest, ResearchResponse, ResearchStatusResponse
from app.services.research_service import (
    get_research,
    list_research,
    review_evidence,
    run_research,
)
from app.security.auth import (
    OrganizationContext,
    Permission,
    require_permission,
)

logger = get_logger("app.api.v1.endpoints.research")

router = APIRouter()


class HumanEvidenceReviewRequest(BaseModel):
    decision: str = Field(
        ...,
        description="Review decision: verified, partially_verified, unverified, contradicted, rejected",
    )
    analyst_notes: Optional[str] = Field(
        None, max_length=2000, description="Analyst rationale and evidence notes"
    )
    override_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Optional overridden confidence score [0.0, 1.0]"
    )


@router.get(
    "",
    summary="List research runs for the organization",
)
async def list_research_endpoint(
    context: OrganizationContext = Depends(
        require_permission(Permission.VIEW_RESEARCH)
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[Dict[str, Any]]:
    """Return all research runs conducted for the authenticated organization."""
    return await list_research(context.organization_id, limit=limit, offset=offset)


@router.post(
    "",
    response_model=ResearchResponse,
    status_code=201,
    summary="Submit and execute a competitive-intelligence research run",
)
async def submit_research(
    request: ResearchRequest,
    context: OrganizationContext = Depends(
        require_permission(Permission.CREATE_RESEARCH)
    ),
) -> ResearchResponse:
    """Accept a research request, execute the LangGraph workflow, and return results.

    The response includes a research_id, execution status, and the structured
    result produced by the graph nodes.
    """
    logger.info("Research submission accepted for organization=%s", context.organization_id)
    result = await run_research(request, organization_id=context.organization_id)
    return ResearchResponse(
        research_id=result.research_id,
        status=result.status,
        message=(
            "Research completed."
            if result.status == "completed"
            else "Research completed with errors; see results.errors."
        ),
        results=result,
    )


@router.get(
    "/{research_id}",
    response_model=ResearchStatusResponse,
    summary="Get research status and results by ID",
)
async def get_research_endpoint(
    context: OrganizationContext = Depends(
        require_permission(Permission.VIEW_RESEARCH)
    ),
    research_id: str = Path(..., min_length=1, description="Research run identifier"),
) -> ResearchStatusResponse:
    """Return the status and structured results for a previously submitted research run."""
    logger.debug("Fetching research for organization=%s", context.organization_id)
    return await get_research(research_id, organization_id=context.organization_id)


@router.post(
    "/{research_id}/evidence/{evidence_id}/review",
    summary="Record human analyst review decision on an evidence claim",
)
async def review_evidence_endpoint(
    request: HumanEvidenceReviewRequest,
    context: OrganizationContext = Depends(
        require_permission(Permission.MANAGE_EVIDENCE)
    ),
    research_id: str = Path(..., min_length=1, description="Research run identifier"),
    evidence_id: str = Path(..., min_length=1, description="Evidence claim identifier"),
) -> Dict[str, Any]:
    """Record an analyst review decision on an evidence claim with tenant isolation and audit tracking."""
    logger.info(
        "Human evidence review recorded research_id=%s evidence_id=%s decision=%s by=%s",
        research_id,
        evidence_id,
        request.decision,
        context.user.email,
    )
    return await review_evidence(
        research_id=research_id,
        evidence_id=evidence_id,
        organization_id=context.organization_id,
        decision=request.decision,
        analyst_notes=request.analyst_notes,
        override_confidence=request.override_confidence,
        reviewer_email=context.user.email,
    )


__all__ = ["router"]
