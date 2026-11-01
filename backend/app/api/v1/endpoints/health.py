"""Health-check endpoint.

GET /api/v1/health

Returns the service status and honest dependency status (database, LLM
configuration). Never falsely reports a successful database connection.
"""

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.database import db
from app.core.llm import llm_factory

router = APIRouter()


@router.get("", response_model=dict, summary="Health check")
async def health() -> dict:
    """Return application and dependency health status.

    The ``database`` field reflects actual configured/connectable state. The
    ``llm`` field reflects whether an API key is configured (no calls made).
    """
    settings = get_settings()
    database_status = await db.health_check()

    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "database": database_status,
        "llm": {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "configured": settings.is_llm_configured,
        },
        "endpoints": {
            "research": f"{settings.api_v1_str}/research",
            "research_by_id": f"{settings.api_v1_str}/research/{{research_id}}",
        },
    }
