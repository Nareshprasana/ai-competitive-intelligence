"""Tests for the LLM factory (core/llm.py).

Verifies: lazy construction, no init at import, provider independence,
OpenRouter-compatible config, and a clear error when invoked without an API key
(so no LLM credits can be consumed accidentally in Phase 1).
"""

import app.core.llm as llm_module
from app.core.llm import LLMConfig, LLMFactory, OpenRouterLLMClient, llm_factory
from app.core.exceptions import LLMConfigurationError


def test_llm_factory_no_init_at_import():
    # The factory and client are not created at import time.
    assert llm_module.llm_factory._client is None
    assert llm_module.llm_factory._config is None


def test_llm_config_from_env_without_key_not_configured():
    config = LLMFactory()._load_config()
    assert config.provider == "openrouter"
    assert config.model == "deepseek/deepseek-chat"
    assert config.is_configured is False


def test_create_client_is_openrouter_compatible():
    factory = LLMFactory()
    client = factory.create_client(LLMConfig(provider="openrouter", model="deepseek/deepseek-chat"))
    assert isinstance(client, OpenRouterLLMClient)
    assert client.config.provider == "openrouter"


def test_complete_without_api_key_raises_clear_error():
    factory = LLMFactory()
    client = factory.create_client(LLMConfig(provider="openrouter", model="deepseek/deepseek-chat"))
    try:
        import asyncio

        asyncio.run(client.complete([{"role": "user", "content": "hi"}]))
        assert False, "expected LLMConfigurationError"
    except LLMConfigurationError as exc:
        assert "LLM is not configured" in exc.message or "disabled in Phase 1" in exc.message
        assert exc.error_code == "LLM_NOT_CONFIGURED"
