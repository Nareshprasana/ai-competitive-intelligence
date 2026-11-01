"""Centralized logging configuration for ACIS.

Uses Python's standard ``logging`` module with JSON-friendly formatting.
Sensitive data (API keys, secrets, request bodies containing PII) must never
be logged. Log level is controlled via the ``LOG_LEVEL`` environment variable
(default ``INFO``).
"""

import logging
import sys
from typing import Optional


class _MaskingFormatter(logging.Formatter):
    """Formatter that redacts common secret-like tokens from log messages."""

    _SECRET_TOKENS = (
        "OPENROUTER_API_KEY",
        "API_KEY",
        "SECRET_KEY",
        "DATABASE_URL",
        "PASSWORD",
        "TOKEN",
    )

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        for token in self._SECRET_TOKENS:
            import re

            message = re.sub(
                rf"({token}\s*[:=]\s*)\S+",
                rf"\1[REDACTED]",
                message,
                flags=re.IGNORECASE,
            )
        return message


def configure_logging(level: Optional[str] = None) -> None:
    """Configure the root logger once.

    Safe to call multiple times; reconfiguration removes existing handlers to
    avoid duplicate log lines.
    """
    import os

    log_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplication on reload.
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    formatter = _MaskingFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Keep noisy third-party loggers at WARNING unless debug is on.
    if log_level != "DEBUG":
        for name in ("uvicorn", "uvicorn.error", "sqlalchemy.engine", "langgraph"):
            logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module name."""
    return logging.getLogger(name)
