"""Pydantic schemas for evidence and provenance tracking."""

from datetime import datetime, timezone
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
    UNVERIFIED = "unverified"
    CONTRADICTED = "contradicted"
    CONFLICTING = "conflicting"
    STALE = "stale"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"


class SourceCredibilityTier(str):
    """Transparent source credibility classification tiers."""

    OFFICIAL_WEBSITE = "official_website"
    REGULATORY_FILING = "regulatory_filing"
    OFFICIAL_DOCUMENTATION = "official_documentation"
    INDUSTRY_PUBLICATION = "industry_publication"
    REPUTABLE_NEWS = "reputable_news"
    RESEARCH_REPORT = "research_report"
    THIRD_PARTY_DIRECTORY = "third_party_directory"
    BLOG_OPINION = "blog_opinion"
    UNVERIFIED_SOCIAL = "unverified_social"
    OTHER = "other"


class SourceCredibilityAssessment(BaseModel):
    """Credibility assessment for a source."""

    model_config = ConfigDict(str_strip_whitespace=True)

    source_domain: str
    source_url: str
    tier: str = Field(default=SourceCredibilityTier.OTHER)
    credibility_score: float = Field(ge=0.0, le=1.0)
    is_primary: bool = False
    explanation: str


class FreshnessAssessment(BaseModel):
    """Freshness evaluation for an evidence claim."""

    model_config = ConfigDict(str_strip_whitespace=True)

    category: str = Field(default="general")
    published_at: Optional[datetime] = None
    retrieved_at: datetime
    age_days: Optional[int] = None
    is_stale: bool = False
    freshness_score: float = Field(ge=0.0, le=1.0)
    explanation: str


class ClaimEvidenceMatch(BaseModel):
    """Match assessment between a claim and a specific piece of evidence."""

    model_config = ConfigDict(str_strip_whitespace=True)

    evidence_id: str
    match_type: str = Field(
        ...,
        description=(
            "directly_supports | partially_supports | contradicts | "
            "insufficient | unrelated"
        ),
    )
    relevance_score: float = Field(ge=0.0, le=1.0)
    explanation: str


class ContradictionRecord(BaseModel):
    """A detected contradiction between two pieces of evidence."""

    model_config = ConfigDict(str_strip_whitespace=True)

    contradiction_id: str
    topic: str
    claim_a: str
    evidence_id_a: str
    source_url_a: str
    claim_b: str
    evidence_id_b: str
    source_url_b: str
    severity: str = Field(
        default="medium", description="high | medium | low"
    )
    explanation: str
    requires_human_review: bool = True


class ClaimValidationResult(BaseModel):
    """Structured validation result for a single factual claim."""

    model_config = ConfigDict(str_strip_whitespace=True)

    claim_id: str
    claim: str
    validation_status: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)
    source_credibility_assessments: List[SourceCredibilityAssessment] = Field(
        default_factory=list
    )
    freshness_assessment: FreshnessAssessment
    validation_explanation: str
    missing_evidence: List[str] = Field(default_factory=list)
    human_review_required: bool = False
    human_review_reason: Optional[str] = None
    validated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class HumanReviewItem(BaseModel):
    """Claim flagged for human analyst review."""

    model_config = ConfigDict(str_strip_whitespace=True)

    claim_id: str
    claim_description: str
    validation_status: str
    supporting_sources: List[Dict[str, Any]] = Field(default_factory=list)
    contradicting_sources: List[Dict[str, Any]] = Field(default_factory=list)
    reason_for_review: str
    missing_information: List[str] = Field(default_factory=list)
    confidence_explanation: str


class ValidationSummary(BaseModel):
    """Comprehensive validation summary for a research run."""

    model_config = ConfigDict(str_strip_whitespace=True)

    research_id: str
    total_claims: int
    verified_count: int
    partially_verified_count: int
    unverified_count: int
    contradicted_count: int
    stale_count: int
    requires_human_review_count: int
    average_confidence: float
    status: str
    claim_results: List[ClaimValidationResult] = Field(default_factory=list)
    contradictions: List[ContradictionRecord] = Field(default_factory=list)
    human_review_queue: List[HumanReviewItem] = Field(default_factory=list)
    validated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


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
        default_factory=lambda: datetime.now(timezone.utc),
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


__all__ = [
    "ClaimEvidenceMatch",
    "ClaimValidationResult",
    "ContradictionRecord",
    "Evidence",
    "EvidenceCollection",
    "EvidenceType",
    "FreshnessAssessment",
    "HumanReviewItem",
    "SourceCredibilityAssessment",
    "SourceCredibilityTier",
    "ValidationSummary",
    "VerificationStatus",
]
