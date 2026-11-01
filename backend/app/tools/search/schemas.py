"""Search result and query schemas for the search provider abstraction."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SearchResult(BaseModel):
    """A single normalized search result."""

    model_config = ConfigDict(str_strip_whitespace=True)

    url: str = Field(..., description="Resolved URL of the result.")
    title: str = Field(..., description="Page title or result title.")
    snippet: Optional[str] = Field(
        default=None, description="Search snippet / short description."
    )
    source_domain: str = Field(..., description="Registered domain of the URL.")
    published_at: Optional[datetime] = Field(
        default=None, description="Publication date when discoverable."
    )
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the result was retrieved.",
    )
    query: str = Field(..., description="Search query that produced this result.")
    provider: str = Field(..., description="Search provider name.")
    raw: Dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific raw result data."
    )

    @field_validator("url")
    @classmethod
    def _validate_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("url must not be empty")
        return v.strip()

    @field_validator("source_domain")
    @classmethod
    def _validate_domain(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("source_domain must not be empty")
        return v.strip().lower()


class SearchQuery(BaseModel):
    """A generated search query with tracking metadata."""

    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(..., min_length=1, description="The search query text.")
    purpose: str = Field(
        ..., description="Why this query was generated (e.g. 'company_overview')."
    )
    priority: int = Field(
        default=1, ge=1, le=5, description="Query priority (1=highest)."
    )
    executed: bool = Field(default=False, description="Whether the query has been run.")
    results: List[SearchResult] = Field(
        default_factory=list, description="Results returned for this query."
    )


__all__ = ["SearchResult", "SearchQuery"]
