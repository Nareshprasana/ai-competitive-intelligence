"""Environment-based application configuration using Pydantic Settings.

All configuration is read from environment variables (and an optional ``.env``
file). No secrets are hardcoded. Values that are missing in production should
degrade gracefully rather than crash the application at import time.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = Field(default="ai-competitive-intelligence")
    app_version: str = Field(default="0.1.0")
    app_env: str = Field(default="development")
    debug: bool = Field(default=True)

    # --- API ---
    api_v1_str: str = Field(default="/api/v1")

    # --- CORS (restricted by default) ---
    backend_cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # --- Security ---
    secret_key: str = Field(default="dev-secret-do-not-use-in-production")
    max_request_size_mb: int = Field(default=4)

    # --- LLM (provider-independent, OpenRouter-compatible) ---
    llm_provider: str = Field(default="openrouter")
    llm_model: str = Field(default="deepseek/deepseek-chat")
    openrouter_api_key: Optional[str] = Field(default=None)
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1")
    llm_temperature: float = Field(default=0.2)
    llm_max_tokens: int = Field(default=2048)
    llm_request_timeout_seconds: int = Field(default=30)

    # --- Database (PostgreSQL + pgvector) ---
    database_url: Optional[str] = Field(default=None)
    database_test_url: Optional[str] = Field(default=None)

    # --- Organization / tenant isolation (future auth/RBAC) ---
    default_organization_id: str = Field(default="org-dev")

    # --- Search provider (company research agent) ---
    search_provider: str = Field(
        default="mock", description="Search provider: 'mock' or 'duckduckgo'."
    )
    search_max_queries: int = Field(
        default=8, ge=1, description="Maximum search queries per research run."
    )
    search_max_pages: int = Field(
        default=10, ge=1, description="Maximum pages fetched per research run."
    )
    competitor_max_candidates: int = Field(
        default=15, ge=1, le=100,
        description="Maximum competitor candidates evaluated per research run.",
    )
    competitor_max_search_queries: int = Field(
        default=6, ge=1, le=20,
        description="Maximum additional searches for competitor discovery.",
    )
    competitor_max_tokens: int = Field(
        default=2048, ge=256, le=4096,
        description="Maximum LLM output tokens for competitor extraction.",
    )
    duckduckgo_base_url: str = Field(
        default="https://html.duckduckgo.com/html/",
        description="DuckDuckGo HTML endpoint.",
    )

    @property
    def is_llm_configured(self) -> bool:
        """True only when an API key is explicitly provided."""
        return bool(self.openrouter_api_key)

    @property
    def is_database_configured(self) -> bool:
        """True only when a database URL is explicitly provided."""
        return bool(self.database_url)

    @property
    def search_provider_is_mock(self) -> bool:
        """True when using the deterministic mock search provider (no network)."""
        return self.search_provider.lower() == "mock"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings accessor. Safe to call repeatedly."""
    return Settings()


def get_settings_uncached() -> Settings:
    """Fresh settings instance (useful in tests)."""
    return Settings()


if __name__ == "__main__":  # pragma: no cover - manual sanity check
    s = get_settings()
    print(s.model_dump_json(indent=2))
