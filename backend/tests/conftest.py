"""Keep PostgreSQL-backed tests isolated from development databases."""

import os
import re

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

    os.environ["DATABASE_URL"] = test_url
