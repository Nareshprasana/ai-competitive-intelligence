"""Tests for the LLM client with mocked HTTP."""

import asyncio
from unittest.mock import AsyncMock, patch

from app.core.llm import (
    LLMConfig,
    LLMMessage,
    LLMResponse,
    OpenRouterLLMClient,
)
from app.core.exceptions import LLMConfigurationError


def test_llm_client_not_configured_raises():
    client = OpenRouterLLMClient(
        LLMConfig(provider="openrouter", model="deepseek/deepseek-chat")
    )
    try:
        asyncio.run(
            client.complete([LLMMessage(role="user", content="hi")])
        )
        assert False, "expected LLMConfigurationError"
    except LLMConfigurationError:
        pass


def test_llm_client_configured_with_key():
    client = OpenRouterLLMClient(
        LLMConfig(
            provider="openrouter",
            model="deepseek/deepseek-chat",
            api_key="test-key-123",
        )
    )
    assert client.is_available() is True


def test_llm_client_malformed_json():
    client = OpenRouterLLMClient(
        LLMConfig(
            provider="openrouter",
            model="deepseek/deepseek-chat",
            api_key="test-key",
        )
    )

    async def run():
        with patch.object(client, "_get_client", new_callable=AsyncMock) as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = lambda: {
                "choices": [{"message": {"content": "not valid json"}}]
            }
            mock_client.return_value.post = AsyncMock(return_value=mock_response)

            try:
                await client.complete_structured(
                    [LLMMessage(role="user", content="extract")],
                    response_model=__import__(
                        "app.schemas.company", fromlist=["CompanyProfile"]
                    ).CompanyProfile,
                )
                assert False, "expected LLMConfigurationError"
            except LLMConfigurationError as exc:
                assert "malformed JSON" in exc.message or "schema validation" in exc.message

    asyncio.run(run())


def test_llm_response_structure():
    response = LLMResponse(
        content='{"company_name": "Acme"}',
        model="deepseek/deepseek-chat",
        provider="openrouter",
        usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    )
    assert response.content == '{"company_name": "Acme"}'
    assert response.usage["total_tokens"] == 15


__all__ = []
