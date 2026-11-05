"""Environment-based application configuration using Pydantic Settings.

All configuration is read from environment variables (and an optional ``.env``
file). No secrets are hardcoded. Values that are missing in production should
degrade gracefully rather than crash the application at import time.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, SecretStr, field_validator, model_validator
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
    max_request_size_mb: int = Field(default=4)
    auth_jwt_signing_key: SecretStr = Field(
        default=SecretStr(""), validation_alias="AUTH_JWT_SIGNING_KEY"
    )
    auth_email_lookup_key: SecretStr = Field(
        default=SecretStr(""), validation_alias="AUTH_EMAIL_LOOKUP_KEY"
    )
    auth_access_token_minutes: int = Field(default=10, ge=1, le=60)
    auth_refresh_token_days: int = Field(default=30, ge=1, le=90)
    auth_cookie_secure: bool = Field(default=False)
    data_encryption_keys: SecretStr = Field(
        default=SecretStr(""), validation_alias="DATA_ENCRYPTION_KEYS"
    )
    data_encryption_active_key_id: str = Field(
        default="", validation_alias="DATA_ENCRYPTION_ACTIVE_KEY_ID"
    )
    api_rate_limit_requests: int = Field(default=120, ge=1)
    auth_rate_limit_requests: int = Field(default=20, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)

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

    # --- Organization / tenant defaults ---
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

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.app_env.lower() != "production":
            return self
        if self.debug:
            raise ValueError("DEBUG must be false in production.")
        if len(self.auth_jwt_signing_key.get_secret_value()) < 32:
            raise ValueError(
                "AUTH_JWT_SIGNING_KEY must contain at least 32 characters in production."
            )
        if len(self.auth_email_lookup_key.get_secret_value()) < 32:
            raise ValueError(
                "AUTH_EMAIL_LOOKUP_KEY must contain at least 32 characters in production."
            )
        if not self.auth_cookie_secure:
            raise ValueError("AUTH_COOKIE_SECURE must be true in production.")
        if "*" in self.backend_cors_origins:
            raise ValueError("Wildcard CORS origins are not allowed in production.")
        if not self.backend_cors_origins or any(
            "localhost" in origin or "127.0.0.1" in origin
            for origin in self.backend_cors_origins
        ):
            raise ValueError(
                "Production CORS origins must be explicitly configured public origins."
            )
        if not self.database_url:
            raise ValueError("DATABASE_URL is required in production.")
        return self


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
