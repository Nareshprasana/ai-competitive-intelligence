"""Tests for environment-based Pydantic settings (core/config.py)."""

from app.core.config import get_settings_uncached, Settings


def test_settings_defaults():
    s = get_settings_uncached()
    assert s.app_name == "ai-competitive-intelligence"
    assert s.app_env == "development"
    assert s.api_v1_str == "/api/v1"
    assert "http://localhost:3000" in s.backend_cors_origins


def test_settings_not_configured_by_default():
    s = get_settings_uncached()
    assert s.is_llm_configured is False
    assert s.is_database_configured is False
    assert s.openrouter_api_key is None
    assert s.database_url is None


def test_cors_origin_string_parsing():
    s = Settings(backend_cors_origins="http://a.example.com, http://b.example.com")
    assert s.backend_cors_origins == ["http://a.example.com", "http://b.example.com"]


def test_cors_origin_list_unchanged():
    s = Settings(backend_cors_origins=["http://a.example.com"])
    assert s.backend_cors_origins == ["http://a.example.com"]
