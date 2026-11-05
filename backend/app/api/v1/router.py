"""Versioned API router (v1).

All v1 endpoints are mounted here and included in the FastAPI app under
``settings.api_v1_str`` (default ``/api/v1``).
Mount new business endpoints under ``authenticated_router``; only explicitly
public health and authentication routes belong directly on ``api_router``.
"""

from fastapi import APIRouter, Depends

from app.api.v1.endpoints import auth, health, research
from app.security.auth import get_current_user

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.public_router, tags=["authentication", "organizations"])

authenticated_router = APIRouter(dependencies=[Depends(get_current_user)])
authenticated_router.include_router(
    auth.protected_router, tags=["authentication", "organizations"]
)
authenticated_router.include_router(
    research.router, prefix="/research", tags=["research"]
)
api_router.include_router(authenticated_router)

__all__ = ["api_router"]
