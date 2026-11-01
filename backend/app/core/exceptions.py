"""Custom application exceptions and centralized exception handlers.

All exceptions carry a safe, client-facing message. Internal details are never
leaked to API clients. Handlers convert exceptions into consistent JSON error
responses.
"""

from typing import Any, Dict, Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse


class ACISException(Exception):
    """Base exception for ACIS application errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}


class ValidationError(ACISException):
    """Raised when input validation fails (client error)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class NotFoundError(ACISException):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details=details,
        )


class ResearchError(ACISException):
    """Raised when the research workflow fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="RESEARCH_ERROR",
            details=details,
        )


class LLMConfigurationError(ACISException):
    """Raised when the LLM is invoked without proper configuration."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="LLM_NOT_CONFIGURED",
            details=details,
        )


class DatabaseUnavailableError(ACISException):
    """Raised when database-backed functionality is requested but unavailable."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="DATABASE_UNAVAILABLE",
            details=details,
        )


def _error_payload(exc: ACISException) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "error": True,
        "error_code": exc.error_code,
        "message": exc.message,
    }
    if exc.details:
        payload["details"] = exc.details
    return payload


async def acis_exception_handler(request: Request, exc: ACISException) -> JSONResponse:
    """Handler for ACISException -> consistent JSON error response."""
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(exc),
    )


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handler for Pydantic/Starlette validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "error_code": "VALIDATION_ERROR",
            "message": "Request validation failed.",
            "details": {"errors": str(exc)},
        },
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all handler. Never leaks internal stack traces to clients."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred.",
        },
    )


EXCEPTION_HANDLERS = {
    ACISException: acis_exception_handler,
}
