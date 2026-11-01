"""Provider-independent LLM abstraction (OpenRouter-compatible).

Design goals:
- Configurable provider, model, base URL, API key from environment only.
- No hardcoded secrets.
- No initialization at module import time.
- No LLM calls during application import.
- Real HTTP client against OpenRouter (DeepSeek, or any OpenAI-compatible provider).
- Structured outputs using Pydantic.
- Handles malformed output, API timeouts, rate limits; retries transient failures.
- Limits retries and token usage.

The client is constructed lazily. ``complete`` raises ``LLMConfigurationError``
if invoked without an API key, making it impossible to accidentally consume
LLM credits when not configured.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Type, TypeVar

import httpx
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.exceptions import LLMConfigurationError
from app.core.logging import get_logger

logger = get_logger("app.core.llm")

T = TypeVar("T", bound=BaseModel)

# Default OpenRouter chat completions endpoint.
CHAT_COMPLETIONS_PATH = "/chat/completions"

# Maximum tokens per LLM call (budget guard).
MAX_TOKENS_PER_CALL = 4096

# Default max retries for transient failures.
DEFAULT_MAX_RETRIES = 3

# Retryable HTTP status codes (rate limiting, transient server errors).
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


class LLMMessage(BaseModel):
    """A single chat message."""

    role: str
    content: str


class LLMResponse(BaseModel):
    """A single LLM completion response."""

    content: str
    model: str
    provider: str
    usage: Dict[str, int] = Field(default_factory=dict)


class LLMConfig(BaseModel):
    """Configuration for an LLM provider."""

    model_config = {"extra": "forbid"}

    provider: str = Field(default="openrouter", description="LLM provider name.")
    model: str = Field(default="deepseek/deepseek-chat", description="Model name.")
    api_key: Optional[str] = Field(default=None, description="API key (from env only).")
    base_url: str = Field(
        default="https://openrouter.ai/api/v1", description="Base API URL."
    )
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=256, le=MAX_TOKENS_PER_CALL)
    timeout_seconds: int = Field(default=30, ge=5, le=120)
    max_retries: int = Field(default=DEFAULT_MAX_RETRIES, ge=0, le=10)

    @property
    def is_configured(self) -> bool:
        """True only when an API key is explicitly provided."""
        return bool(self.api_key)


class BaseLLMClient:
    """Abstract interface for an LLM client."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    async def complete(self, messages: List[LLMMessage], **kwargs: Any) -> LLMResponse:
        raise NotImplementedError

    async def complete_structured(
        self,
        messages: List[LLMMessage],
        response_model: Type[T],
        **kwargs: Any,
    ) -> T:
        """Complete and parse the response into a Pydantic model."""
        raise NotImplementedError

    def is_available(self) -> bool:
        return self.config.is_configured


class OpenRouterLLMClient(BaseLLMClient):
    """OpenRouter-compatible LLM client.

    Makes real HTTP calls to OpenRouter when an API key is configured.
    Without an API key, ``complete`` raises ``LLMConfigurationError``.
    """

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": "Bearer " + (self.config.api_key or ""),
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(self.config.timeout_seconds),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def complete(self, messages: List[LLMMessage], **kwargs: Any) -> LLMResponse:
        """Send a chat completion request to OpenRouter.

        Raises ``LLMConfigurationError`` if no API key is configured.
        Retries transient failures (rate limits, timeouts, 5xx).
        """
        if not self.config.is_configured:
            raise LLMConfigurationError(
                "LLM is not configured. Set OPENROUTER_API_KEY before calling the LLM.",
                details={
                    "provider": self.config.provider,
                    "model": self.config.model,
                    "hint": "No LLM credits are consumed when OPENROUTER_API_KEY is unset.",
                },
            )

        client = await self._get_client()
        url = self.config.base_url.rstrip("/") + CHAT_COMPLETIONS_PATH

        payload: Dict[str, Any] = {
            "model": self.config.model,
            "messages": [m.model_dump() for m in messages],
            "temperature": self.config.temperature,
            "max_tokens": min(self.config.max_tokens, MAX_TOKENS_PER_CALL),
        }
        # Allow callers to override payload fields.
        payload.update(kwargs)

        last_exc: Optional[Exception] = None
        for attempt in range(self.config.max_retries + 1):
            try:
                response = await client.post(url, json=payload)
                if response.status_code in RETRYABLE_STATUS_CODES:
                    raise httpx.HTTPStatusError(
                        "Retryable status %d" % response.status_code,
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()
                data = response.json()
                break
            except (httpx.HTTPStatusError, httpx.TimeoutError, httpx.ConnectError) as exc:
                last_exc = exc
                if attempt < self.config.max_retries:
                    await asyncio.sleep(2.0 * (attempt + 1))
                    continue
                raise LLMConfigurationError(
                    "LLM request failed after %d retries: %s"
                    % (self.config.max_retries, exc),
                    details={
                        "provider": self.config.provider,
                        "model": self.config.model,
                    },
                ) from exc
        else:
            # Should not reach here, but satisfy type checkers.
            raise LLMConfigurationError("LLM request failed without response.")

        try:
            choice = data["choices"][0]
            message = choice.get("message", {})
            content = message.get("content", "")
            usage = data.get("usage", {}) or {}
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMConfigurationError(
                "Malformed LLM response: %s" % exc,
                details={"provider": self.config.provider, "model": self.config.model},
            ) from exc

        return LLMResponse(
            content=content,
            model=self.config.model,
            provider=self.config.provider,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        )

    async def complete_structured(
        self,
        messages: List[LLMMessage],
        response_model: Type[T],
        **kwargs: Any,
    ) -> T:
        """Complete and parse the response into a Pydantic model.

        Instructs the model to return JSON matching the model schema, then
        validates the parsed output. Raises ``LLMConfigurationError`` on
        malformed output.
        """
        schema = response_model.model_json_schema()
        system_instruction = (
            "You are a precise information-extraction assistant. "
            "Return ONLY a valid JSON object that conforms to the provided JSON Schema. "
            "Do not include markdown fences, explanations, or extra text. "
            "Schema: " + json.dumps(schema)
        )

        all_messages = [LLMMessage(role="system", content=system_instruction)] + messages

        response = await self.complete(all_messages, **kwargs)
        raw = response.content.strip()

        # Strip accidental markdown fences if present.
        if raw.startswith("```"):
            raw = raw.split("```", 2)
            if len(raw) == 3:
                raw = raw[1]
                # Remove optional language tag line.
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMConfigurationError(
                "LLM returned malformed JSON: %s" % exc,
                details={
                    "provider": self.config.provider,
                    "model": self.config.model,
                    "raw_prefix": raw[:200],
                },
            ) from exc

        try:
            return response_model.model_validate(data)
        except Exception as exc:
            raise LLMConfigurationError(
                "LLM output failed schema validation: %s" % exc,
                details={
                    "provider": self.config.provider,
                    "model": self.config.model,
                    "raw_prefix": raw[:200],
                },
            ) from exc


class LLMFactory:
    """Builds LLM clients from settings. Lazily initialized."""

    def __init__(self) -> None:
        self._client: Optional[BaseLLMClient] = None
        self._config: Optional[LLMConfig] = None

    def _load_config(self) -> LLMConfig:
        settings = get_settings()
        return LLMConfig(
            provider=settings.llm_provider,
            model=settings.llm_model,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            timeout_seconds=settings.llm_request_timeout_seconds,
        )

    def create_client(self, config: Optional[LLMConfig] = None) -> BaseLLMClient:
        """Create (and cache) an LLM client from settings or an explicit config."""
        if config is None:
            config = self._load_config()
        self._config = config

        provider = config.provider.lower()
        if provider in ("openrouter", "deepseek"):
            client: BaseLLMClient = OpenRouterLLMClient(config)
        else:
            client = OpenRouterLLMClient(config)  # OpenRouter-compatible fallback

        self._client = client
        logger.info(
            "LLM client created (provider=%s, model=%s, configured=%s)",
            config.provider,
            config.model,
            config.is_configured,
        )
        return client

    def get_client(self) -> BaseLLMClient:
        """Return the cached client, creating it from settings if needed."""
        if self._client is None:
            return self.create_client()
        return self._client

    def is_configured(self) -> bool:
        """Whether the current configuration has an API key."""
        config = self._config or self._load_config()
        return config.is_configured


# Singleton factory. Client is NOT created at import time.
llm_factory = LLMFactory()


def get_llm_client() -> BaseLLMClient:
    """Dependency/helper returning the configured LLM client (lazy)."""
    return llm_factory.get_client()


__all__ = [
    "LLMMessage",
    "LLMResponse",
    "LLMConfig",
    "BaseLLMClient",
    "OpenRouterLLMClient",
    "LLMFactory",
    "llm_factory",
    "get_llm_client",
    "CHAT_COMPLETIONS_PATH",
    "RETRYABLE_STATUS_CODES",
    "MAX_TOKENS_PER_CALL",
]
