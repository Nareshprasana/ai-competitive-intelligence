"""FastAPI application factory for ACIS.

Creates the application with:
- Centralized logging and exception handling.
- CORS (restricted to configured origins).
- Request-size limiting.
- Versioned API router under /api/v1.
- Health-check endpoint.
- Graceful startup/shutdown (database engine disposed on shutdown).
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import db
from app.core.exceptions import (
    ACISException,
    EXCEPTION_HANDLERS,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging, get_logger
from app.api.v1.router import api_router

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: configure logging on start, dispose DB on stop."""
    configure_logging()
    settings = get_settings()
    logger.info("Starting %s (version %s, env %s)", settings.app_name, settings.app_version, settings.app_env)
    if not settings.is_llm_configured:
        logger.info("LLM not configured; running in mock-agent mode (no LLM credits consumed).")
    if not settings.is_database_configured:
        logger.info("DATABASE_URL not configured; database-backed features unavailable.")
    yield
    logger.info("Shutting down %s", settings.app_name)
    await db.dispose()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI Competitive Intelligence System - LangGraph multi-agent backend",
        docs_url=f"{settings.api_v1_str}/docs",
        openapi_url=f"{settings.api_v1_str}/openapi.json",
        lifespan=lifespan,
    )

    # Centralized exception handlers.
    app.add_exception_handler(ACISException, EXCEPTION_HANDLERS[ACISException])
    app.add_exception_handler(Exception, unhandled_exception_handler)
    # Note: FastAPI/Starlette request validation errors (RequestValidationError)
    # are handled separately below to return a consistent shape.

    from fastapi.exceptions import RequestValidationError

    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # CORS - restricted to configured origins (no wildcard in production).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.backend_cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Request-size limiting middleware.
    max_bytes = settings.max_request_size_mb * 1024 * 1024

    @app.middleware("http")
    async def request_size_limit(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length is not None and int(content_length) > max_bytes:
            return JSONResponse(
                status_code=413,
                content={
                    "error": True,
                    "error_code": "REQUEST_TOO_LARGE",
                    "message": f"Request body exceeds {settings.max_request_size_mb} MB limit.",
                },
            )
        return await call_next(request)

    # Versioned API routes.
    app.include_router(api_router, prefix=settings.api_v1_str)

    return app


app = create_app()


# Root health (convenience) - the versioned health lives at /api/v1/health.
@app.get("/", tags=["health"])
async def root():
    return {
        "service": get_settings().app_name,
        "version": get_settings().app_version,
        "health": "/api/v1/health",
        "docs": "/api/v1/docs",
    }


__all__ = ["create_app", "app"]
