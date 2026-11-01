"""Pydantic schemas for the research API.

Used for request validation and response serialization. Keeps the transport
layer separate from the internal LangGraph state.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResearchRequest(BaseModel):
    """Request to start a competitive-intelligence research run."""

    model_config = ConfigDict(str_strip_whitespace=True)

    company_name: str = Field(
        ..., min_length=1, max_length=200, description="Name of the company to research."
    )
    industry: str = Field(
        ..., min_length=1, max_length=200, description="Industry the company operates in."
    )
    research_question: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="The specific competitive question to answer.",
    )
    organization_id: Optional[str] = Field(
        default=None,
        description="Owning organization (future tenant isolation). Defaults to settings.default_organization_id.",
    )

    @field_validator("company_name", "industry", "research_question")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("field must not be empty")
        return v


class NodeExecutionMetadata(BaseModel):
    """Metadata recorded for each graph node execution."""

    node_name: str
    status: str  # "completed" | "failed"
    started_at: str
    completed_at: str
    duration_ms: float
    mock: bool = True
    details: Dict[str, Any] = Field(default_factory=dict)


class ResearchResult(BaseModel):
    """Structured result returned by a completed research run."""

    model_config = ConfigDict(str_strip_whitespace=True)

    research_id: str
    status: str  # "completed" | "failed" | "in_progress"
    company_name: str
    industry: str
    research_question: str
    organization_id: Optional[str] = None
    research_plan: Optional[Dict[str, Any]] = None
    company_profile: Optional[Dict[str, Any]] = None
    competitors: List[Dict[str, Any]] = Field(default_factory=list)
    product_intelligence: Optional[Dict[str, Any]] = None
    market_intelligence: Optional[Dict[str, Any]] = None
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    validation_results: Optional[Dict[str, Any]] = None
    strategic_analysis: Optional[Dict[str, Any]] = None
    review_status: str = "pending"
    reviewer_feedback: Optional[str] = None
    final_report: Optional[Dict[str, Any]] = None
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    execution_metadata: List[NodeExecutionMetadata] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ResearchResponse(BaseModel):
    """Response to POST /api/v1/research."""

    research_id: str
    status: str
    message: str
    results: Optional[ResearchResult] = None


class ResearchStatusResponse(BaseModel):
    """Response to GET /api/v1/research/{research_id}."""

    research_id: str
    status: str
    results: Optional[ResearchResult] = None


__all__ = [
    "ResearchRequest",
    "ResearchResponse",
    "ResearchStatusResponse",
    "ResearchResult",
    "NodeExecutionMetadata",
]
