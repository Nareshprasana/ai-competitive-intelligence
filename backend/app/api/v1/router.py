"""Versioned API router (v1).

All v1 endpoints are mounted here and included in the FastAPI app under
``settings.api_v1_str`` (default ``/api/v1``).
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, research

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(research.router, prefix="/research", tags=["research"])

__all__ = ["api_router"]
