"""Research endpoints.

POST /api/v1/research   - submit and execute a research run
GET  /api/v1/research/{research_id} - fetch a research run's status and results
"""

from fastapi import APIRouter, Path

from app.core.logging import get_logger
from app.schemas.research import ResearchRequest, ResearchResponse, ResearchStatusResponse
from app.services.research_service import get_research, run_research

logger = get_logger("app.api.v1.endpoints.research")

router = APIRouter()


@router.post(
    "",
    response_model=ResearchResponse,
    status_code=201,
    summary="Submit and execute a competitive-intelligence research run",
)
async def submit_research(request: ResearchRequest) -> ResearchResponse:
    """Accept a research request, execute the LangGraph workflow, and return results.

    The response includes a research_id, execution status, and the structured
    result produced by the graph nodes.
    """
    logger.info("Research submission: company=%s industry=%s", request.company_name, request.industry)
    result = await run_research(request)
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
    research_id: str = Path(..., min_length=1, description="Research run identifier"),
) -> ResearchStatusResponse:
    """Return the status and structured results for a previously submitted research run."""
    logger.debug("Fetching research %s", research_id)
    return await get_research(research_id)


__all__ = ["router"]
