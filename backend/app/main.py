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
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

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
from app.models.identity import AuditEvent
from app.security.crypto import validate_encryption_configuration
from app.security.auth import client_identity, enforce_rate_limit

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: configure logging on start, dispose DB on stop."""
    configure_logging()
    settings = get_settings()
    logger.info("Starting %s (version %s, env %s)", settings.app_name, settings.app_version, settings.app_env)
    if settings.app_env.lower() == "production":
        validate_encryption_configuration()
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
        docs_url=(
            None
            if settings.app_env.lower() == "production"
            else f"{settings.api_v1_str}/docs"
        ),
        openapi_url=(
            None
            if settings.app_env.lower() == "production"
            else f"{settings.api_v1_str}/openapi.json"
        ),
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

    # Request-size, correlation, and audit middleware.
    max_bytes = settings.max_request_size_mb * 1024 * 1024

    @app.middleware("http")
    async def request_security(request: Request, call_next):
        request_id = uuid4().hex
        request.state.request_id = request_id
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                declared_length = int(content_length)
            except ValueError:
                response = JSONResponse(
                    status_code=400,
                    content={
                        "error": True,
                        "error_code": "INVALID_CONTENT_LENGTH",
                        "message": "Invalid request body length.",
                    },
                )
                response.headers["X-Request-ID"] = request_id
                return response
            if declared_length < 0:
                response = JSONResponse(
                    status_code=400,
                    content={
                        "error": True,
                        "error_code": "INVALID_CONTENT_LENGTH",
                        "message": "Invalid request body length.",
                    },
                )
                response.headers["X-Request-ID"] = request_id
                return response
            if declared_length > max_bytes:
                response = JSONResponse(
                    status_code=413,
                    content={
                        "error": True,
                        "error_code": "REQUEST_TOO_LARGE",
                        "message": f"Request body exceeds {settings.max_request_size_mb} MB limit.",
                    },
                )
                response.headers["X-Request-ID"] = request_id
                return response

        if (
            request.method != "OPTIONS"
            and request.url.path.startswith(settings.api_v1_str)
            and request.url.path != f"{settings.api_v1_str}/health"
            and db.is_available
        ):
            async with db.session_factory() as session:
                try:
                    await enforce_rate_limit(
                        request,
                        session,
                        identity=f"ip:{client_identity(request)}",
                        limit=settings.api_rate_limit_requests,
                    )
                except HTTPException as exc:
                    session.add(
                        AuditEvent(
                            action=f"{request.method} {request.url.path}"[:128],
                            resource_type="api_request",
                            request_id=request_id,
                            outcome="failure",
                        )
                    )
                    await session.commit()
                    response = JSONResponse(
                        status_code=exc.status_code,
                        content={
                            "error": True,
                            "error_code": "RATE_LIMIT_EXCEEDED",
                            "message": "Request rate limit exceeded.",
                        },
                        headers=exc.headers,
                    )
                    response.headers["X-Request-ID"] = request_id
                    return response

        chunks = []
        size = 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > max_bytes:
                response = JSONResponse(
                    status_code=413,
                    content={
                        "error": True,
                        "error_code": "REQUEST_TOO_LARGE",
                        "message": f"Request body exceeds {settings.max_request_size_mb} MB limit.",
                    },
                )
                response.headers["X-Request-ID"] = request_id
                return response
            chunks.append(chunk)
        request._body = b"".join(chunks)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        route = request.scope.get("route")
        route_path = getattr(route, "path", request.url.path)
        if route_path not in ("/", f"{settings.api_v1_str}/health"):
            try:
                if db.is_available:
                    async with db.session_factory() as session:
                        session.add(
                            AuditEvent(
                                actor_user_id=getattr(
                                    request.state, "actor_user_id", None
                                ),
                                organization_id=getattr(
                                    request.state, "organization_id", None
                                ),
                                action=f"{request.method} {route_path}"[:128],
                                resource_type="api_request",
                                request_id=request_id,
                                outcome=(
                                    "success" if response.status_code < 400 else "failure"
                                ),
                            )
                        )
                        await session.commit()
            except SQLAlchemyError as exc:
                logger.error(
                    "Audit event persistence failed request_id=%s error_type=%s",
                    request_id,
                    type(exc).__name__,
                )
        return response

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
