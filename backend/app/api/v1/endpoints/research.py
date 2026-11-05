"""Research endpoints.

POST /api/v1/research   - submit and execute a research run
GET  /api/v1/research/{research_id} - fetch a research run's status and results
"""

from fastapi import APIRouter, Depends, Path

from app.core.logging import get_logger
from app.schemas.research import ResearchRequest, ResearchResponse, ResearchStatusResponse
from app.services.research_service import get_research, run_research
from app.security.auth import (
    OrganizationContext,
    Permission,
    require_permission,
)

logger = get_logger("app.api.v1.endpoints.research")

router = APIRouter()


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


__all__ = ["router"]
