"""Typed LangGraph state for a research run.

Uses a Pydantic model so the state is validated at every transition. ``Annotated``
list fields with ``operator.add`` reducers accumulate values across nodes
(e.g. competitors, evidence, errors) instead of being overwritten.

The state is the single source of truth passed between all graph nodes.
"""

from datetime import datetime, timezone
from typing import Any, Annotated, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Self

import operator


class ResearchState(BaseModel):
    """Typed state carried through the research LangGraph."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Identifiers
    research_id: str
    organization_id: Optional[str] = None

    # Input
    company_name: str
    industry: str
    research_question: str

    # Graph-produced artifacts
    research_plan: Optional[Dict[str, Any]] = None
    company_profile: Optional[Dict[str, Any]] = None
    search_results: Annotated[List[Dict[str, Any]], operator.add] = Field(
        default_factory=list
    )
    competitors: Annotated[List[Dict[str, Any]], operator.add] = Field(
        default_factory=list
    )
    product_intelligence: Optional[Dict[str, Any]] = None
    market_intelligence: Optional[Dict[str, Any]] = None
    evidence: Annotated[List[Dict[str, Any]], operator.add] = Field(
        default_factory=list
    )
    validation_results: Optional[Dict[str, Any]] = None
    strategic_analysis: Optional[Dict[str, Any]] = None
    final_report: Optional[Dict[str, Any]] = None

    # Review / status
    review_status: str = "pending"
    reviewer_feedback: Optional[str] = None

    # Errors & execution tracking
    errors: Annotated[List[Dict[str, Any]], operator.add] = Field(
        default_factory=list
    )
    execution_metadata: Annotated[List[Dict[str, Any]], operator.add] = Field(
        default_factory=list
    )

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def mark_updated(self) -> Self:
        """Refresh the updated_at timestamp and return self."""
        self.updated_at = datetime.now(timezone.utc)
        return self

    def add_node_metadata(
        self,
        *,
        node_name: str,
        status: str,
        started_at: str,
        completed_at: str,
        duration_ms: float,
        mock: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> Self:
        """Append execution metadata for a node (uses the list reducer)."""
        entry = {
            "node_name": node_name,
            "status": status,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_ms": duration_ms,
            "mock": mock,
            "details": details or {},
        }
        # Append via the reducer field so LangGraph's operator.add combines it.
        self.execution_metadata = self.execution_metadata + [entry]  # type: ignore[assignment]
        self.mark_updated()
        return self

    def add_error(
        self, *, node_name: str, error: str, details: Optional[Dict[str, Any]] = None
    ) -> Self:
        """Append a recorded error (never suppresses the fact a node failed)."""
        entry = {
            "node_name": node_name,
            "error": error,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.errors = self.errors + [entry]  # type: ignore[assignment]
        self.mark_updated()
        return self


__all__ = ["ResearchState"]
