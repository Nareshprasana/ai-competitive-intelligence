"""Tests for custom exceptions (core/exceptions.py)."""

from app.core.exceptions import (
    ACISException,
    ValidationError,
    NotFoundError,
    ResearchError,
    LLMConfigurationError,
    DatabaseUnavailableError,
)


def test_exception_status_codes():
    assert ValidationError("bad").status_code == 400
    assert NotFoundError("missing").status_code == 404
    assert ResearchError("fail").status_code == 502
    assert LLMConfigurationError("no key").status_code == 503
    assert DatabaseUnavailableError("down").status_code == 503


def test_exception_error_codes_and_message():
    exc = ValidationError("field required", details={"field": "company_name"})
    assert exc.message == "field required"
    assert exc.error_code == "VALIDATION_ERROR"
    assert exc.details == {"field": "company_name"}
