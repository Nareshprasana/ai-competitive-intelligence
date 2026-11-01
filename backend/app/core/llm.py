"""Provider-independent LLM abstraction (OpenRouter-compatible).

Design goals for Phase 1:
- Configurable provider, model, base URL, API key from environment only.
- No hardcoded secrets.
- No initialization at module import time.
- No LLM calls are made during Phase 1. The client is constructed but its
  completion methods raise a clear error if invoked without configuration,
  making it impossible to accidentally consume LLM credits.

Future phases will swap the mock/stub client for a real HTTP client against
OpenRouter (DeepSeek, or any OpenAI-compatible provider).
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.exceptions import LLMConfigurationError
from app.core.logging import get_logger

logger = get_logger("app.core.llm")


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

    provider: str = Field(default="openrouter")
    model: str = Field(default="deepseek/deepseek-chat")
    api_key: Optional[str] = Field(default=None)
    base_url: str = Field(default="https://openrouter.ai/api/v1")
    temperature: float = Field(default=0.2)
    max_tokens: int = Field(default=2048)
    timeout_seconds: int = Field(default=30)

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

    def is_available(self) -> bool:
        return self.config.is_configured


class OpenRouterLLMClient(BaseLLMClient):
    """OpenRouter-compatible LLM client.

    Phase 1: constructed lazily but never invoked by mock agents. Calling
    ``complete`` without configuration raises ``LLMConfigurationError``.
    """

    async def complete(self, messages: List[LLMMessage], **kwargs: Any) -> LLMResponse:
        if not self.config.is_configured:
            raise LLMConfigurationError(
                "LLM is not configured. Set OPENROUTER_API_KEY (or use mock agents) before calling the LLM.",
                details={
                    "provider": self.config.provider,
                    "model": self.config.model,
                    "hint": "In Phase 1, research uses deterministic mock agents; no LLM credits are consumed.",
                },
            )
        # Real HTTP call would go here in a later phase.
        raise LLMConfigurationError(
            "Live LLM calls are disabled in Phase 1. No LLM credits are consumed.",
            details={"provider": self.config.provider, "model": self.config.model},
        )


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
            client = OpenRouterLLMClient(config)
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
]
