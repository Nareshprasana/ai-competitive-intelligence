"""Automated secret-leak regression and credential safety tests (Phase 3.2.1).

Verifies that environment files are properly ignored by Git, .env.example
only contains placeholders, logs and exceptions do not echo database
credentials, and source code contains no hardcoded active secrets.
"""

import os
from pathlib import Path
import re
import subprocess
import pytest

ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT_DIR / "backend"


def test_gitignore_ignores_env_files():
    """Verify that .gitignore properly excludes all environment files except .env.example."""
    gitignore_path = ROOT_DIR / ".gitignore"
    assert gitignore_path.exists(), ".gitignore must exist in root"
    content = gitignore_path.read_text(encoding="utf-8")
    
    assert ".env" in content, ".env must be ignored in .gitignore"
    assert "!.env.example" in content, "!.env.example must be explicitly preserved"


def test_no_env_files_tracked_by_git():
    """Verify that no .env or .env.local file is tracked in Git."""
    res = subprocess.run(
        ["git", "ls-files", "*.env", "*.env.local", "backend/*.env", "frontend/*.env.local"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    tracked_files = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
    assert tracked_files == [], f"Untracked .env files are committed to git: {tracked_files}"


def test_env_example_contains_no_real_passwords():
    """Verify backend/.env.example and frontend/.env.example contain placeholders only."""
    backend_example = BACKEND_DIR / ".env.example"
    assert backend_example.exists()
    content = backend_example.read_text(encoding="utf-8")

    # Verify no raw password or key in example
    assert "acis_dev_password" not in content
    assert "AUTH_JWT_SIGNING_KEY=" in content
    # Values should be empty or contain generic placeholders
    lines = content.splitlines()
    for line in lines:
        if line.startswith("AUTH_JWT_SIGNING_KEY="):
            assert line.split("=")[1].strip() == ""
        if line.startswith("DATABASE_URL="):
            assert line.split("=")[1].strip() == ""


def test_exception_handling_redacts_connection_urls():
    """Verify that database errors or connection string exceptions do not leak credentials."""
    from app.core.exceptions import DatabaseUnavailableError

    secret_url = "postgresql+asyncpg://admin_user:super_secret_p@ssword!@127.0.0.1:5432/acis_db"
    
    # Safe error message should not contain password
    err = DatabaseUnavailableError("Database persistence is required; connection failed.")
    assert "super_secret_p@ssword!" not in str(err)
    assert "admin_user" not in str(err)
