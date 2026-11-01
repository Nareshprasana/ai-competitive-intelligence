"""Pydantic schemas for evidence and provenance tracking."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvidenceType(str):
    """Type of evidence source."""

    OFFICIAL_WEBSITE = "official_website"
    INVESTOR_RELATIONS = "investor_relations"
    REGULATORY_FILING = "regulatory_filing"
    PRESS_RELEASE = "press_release"
    NEWS_ARTICLE = "news_article"
    PUBLIC_DATABASE = "public_database"
    OTHER = "other"


class VerificationStatus(str):
    """Verification status of an evidence claim."""

    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    CONFLICTING = "conflicting"
    UNVERIFIED = "unverified"


class Evidence(BaseModel):
    """A single piece of evidence supporting a factual claim.

    Every extracted claim must be traceable to a source. Confidence is an
    editorial assessment, not statistical certainty.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    evidence_id: str = Field(..., min_length=1, description="Unique evidence identifier.")
    research_id: str = Field(..., min_length=1, description="Owning research run ID.")
    company_id: Optional[str] = Field(
        default=None, description="Company identifier where available."
    )
    claim: str = Field(..., min_length=1, description="The factual claim.")
    source_url: str = Field(..., description="Source URL where the claim was found.")
    source_title: Optional[str] = Field(
        default=None, description="Title of the source page."
    )
    source_domain: str = Field(..., description="Registered domain of the source URL.")
    published_at: Optional[datetime] = Field(
        default=None, description="Publication date of the source, if discoverable."
    )
    retrieved_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the evidence was retrieved.",
    )
    evidence_type: str = Field(
        default=EvidenceType.OTHER, description="Type of evidence source."
    )
    confidence: float = Field(
        default=0.5, description="Editorial confidence (0-1), not statistical certainty."
    )
    verification_status: str = Field(
        default=VerificationStatus.UNVERIFIED, description="Verification status."
    )
    raw_snippet: Optional[str] = Field(
        default=None, description="Original source snippet text."
    )

    @field_validator("source_url")
    @classmethod
    def _validate_source_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("source_url must not be empty")
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("source_url must be an http/https URL")
        return v

    @field_validator("confidence", mode="before")
    @classmethod
    def _confidence_not_certainty(cls, v: float) -> float:
        """Confidence is editorial, not statistical. Clamp to [0, 1]."""
        return max(0.0, min(1.0, float(v)))


class EvidenceCollection(BaseModel):
    """A collection of evidence items for a research run."""

    model_config = ConfigDict(str_strip_whitespace=True)

    research_id: str
    items: List[Evidence] = Field(default_factory=list)

    def add(self, evidence: Evidence) -> None:
        self.items.append(evidence)

    def by_status(self, status: str) -> List[Evidence]:
        return [e for e in self.items if e.verification_status == status]

    def by_domain(self, domain: str) -> List[Evidence]:
        return [e for e in self.items if e.source_domain == domain.lower()]


__all__ = ["Evidence", "EvidenceCollection", "EvidenceType", "VerificationStatus"]
