"""Keep PostgreSQL-backed tests isolated from development databases."""

import os
import re
import json

import pytest
from sqlalchemy.engine import make_url


def pytest_configure() -> None:
    test_url = os.getenv("ACIS_TEST_DATABASE_URL")
    if not test_url:
        os.environ["DATABASE_URL"] = ""
        return

    url = make_url(test_url)
    if url.get_backend_name() != "postgresql" or not re.search(
        r"(?:^|[_-])test(?:$|[_-])", url.database or "", re.IGNORECASE
    ):
        raise pytest.UsageError(
            "ACIS_TEST_DATABASE_URL must point to a dedicated PostgreSQL "
            "database with 'test' as a delimited name component."
        )

    encryption_keys = os.getenv("DATA_ENCRYPTION_KEYS", "")
    active_key_id = os.getenv("DATA_ENCRYPTION_ACTIVE_KEY_ID", "")
    try:
        keyring = json.loads(encryption_keys)
    except json.JSONDecodeError as exc:
        raise pytest.UsageError(
            "PostgreSQL tests require DATA_ENCRYPTION_KEYS to be a JSON keyring "
            "matching the key used by the test database."
        ) from exc
    if not isinstance(keyring, dict) or active_key_id not in keyring:
        raise pytest.UsageError(
            "PostgreSQL tests require DATA_ENCRYPTION_ACTIVE_KEY_ID and a matching "
            "DATA_ENCRYPTION_KEYS entry for the dedicated test database."
        )
    if len(os.getenv("AUTH_JWT_SIGNING_KEY", "")) < 32:
        raise pytest.UsageError(
            "PostgreSQL API tests require a test-only AUTH_JWT_SIGNING_KEY with "
            "at least 32 characters."
        )
    if len(os.getenv("AUTH_EMAIL_LOOKUP_KEY", "")) < 32:
        raise pytest.UsageError(
            "PostgreSQL tests require a test-only AUTH_EMAIL_LOOKUP_KEY with "
            "at least 32 characters."
        )

    os.environ["DATABASE_URL"] = test_url
