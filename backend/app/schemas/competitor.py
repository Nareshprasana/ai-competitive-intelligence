"""Pydantic schemas for competitor profiles and qualification."""

from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CompetitorType(str, Enum):
    """Classification of a competitor relative to the researched company."""

    DIRECT = "direct"
    INDIRECT = "indirect"
    EMERGING = "emerging"
    SUBSTITUTE = "substitute"


class QualificationFactor(str, Enum):
    """Named factor used in the transparent qualification scoring model."""

    PRODUCT_SIMILARITY = "product_similarity"
    SERVICE_SIMILARITY = "service_similarity"
    CUSTOMER_OVERLAP = "customer_overlap"
    PROBLEM_SPACE_OVERLAP = "problem_space_overlap"
    GEOGRAPHIC_OVERLAP = "geographic_overlap"
    BUSINESS_MODEL_SIMILARITY = "business_model_similarity"
    MARKET_POSITIONING = "market_positioning"


class CompetitorEvidenceItem(BaseModel):
    """A single piece of evidence supporting a competitor qualification claim."""

    model_config = ConfigDict(str_strip_whitespace=True)

    claim: str = Field(..., min_length=1, description="The factual claim.")
    source_url: str = Field(..., description="Source URL where the claim was found.")
    source_title: Optional[str] = Field(
        default=None, description="Title of the source page."
    )
    source_domain: str = Field(..., description="Registered domain of the source URL.")
    evidence_type: str = Field(
        default="other", description="Type of evidence source."
    )
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Editorial confidence (0-1), not statistical certainty.",
    )
    verification_status: str = Field(
        default="unverified", description="Verification status."
    )
    raw_snippet: Optional[str] = Field(
        default=None, description="Retrieved text supporting this claim."
    )

    @field_validator("source_url")
    @classmethod
    def _validate_source_url(cls, value: str) -> str:
        value = value.strip()
        parsed = urlsplit(value)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            raise ValueError("source_url must be a valid http/https URL")
        return value


class CompetitorProfile(BaseModel):
    """Structured competitor profile produced by the Competitor Discovery Agent.

    Every competitor has a documented classification. Unavailable information
    is represented as None or empty lists, never fabricated.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    competitor_id: str = Field(..., min_length=1, description="Unique competitor identifier.")
    company_name: str = Field(..., min_length=1, description="Competitor company name.")
    website: Optional[str] = Field(default=None, description="Official website URL.")
    competitor_type: CompetitorType
    company_description: Optional[str] = Field(
        default=None, description="Plain-language competitor description."
    )
    products_and_services: List[str] = Field(
        default_factory=list, description="Competitor products and services."
    )
    target_customers: List[str] = Field(
        default_factory=list, description="Competitor target customer segments."
    )
    geographic_markets: List[str] = Field(
        default_factory=list, description="Competitor geographic markets."
    )
    competitive_strengths: List[str] = Field(
        default_factory=list, description="Observed competitive strengths."
    )
    competitive_weaknesses: List[str] = Field(
        default_factory=list, description="Observed competitive weaknesses."
    )
    overlap_explanation: Optional[str] = Field(
        default=None, description="Why this company is a competitor (evidence-backed)."
    )
    qualification_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Transparent qualification score (0-1), not statistical certainty.",
    )
    qualification_factors: Dict[str, float] = Field(
        default_factory=dict,
        description="Observed factor values (0-1); weights are documented in the scoring model.",
    )
    evidence: List[CompetitorEvidenceItem] = Field(
        default_factory=list, description="Evidence supporting qualification claims."
    )
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Overall confidence in the classification (0-1).",
    )
    verification_status: str = Field(
        default="unverified", description="Verification status of the classification."
    )
    judgment_notes: Optional[str] = Field(
        default=None,
        description="Analytical judgments separate from evidence-backed observations.",
    )
    unknown_information: List[str] = Field(
        default_factory=list,
        description="Information that is unknown or not publicly verified.",
    )
    source_references: List[str] = Field(
        default_factory=list, description="Source URLs used to build the profile."
    )

    @field_validator("website")
    @classmethod
    def _validate_website(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        parsed = urlsplit(v)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            raise ValueError("website must be an http/https URL")
        return v

    @field_validator("qualification_factors")
    @classmethod
    def _validate_factor_values(cls, values: Dict[str, float]) -> Dict[str, float]:
        if any(not 0.0 <= value <= 1.0 for value in values.values()):
            raise ValueError("qualification factor values must be between 0 and 1")
        return values


class CompetitorCollection(BaseModel):
    """A collection of competitor profiles for a research run."""

    model_config = ConfigDict(str_strip_whitespace=True)

    research_id: str
    items: List[CompetitorProfile] = Field(default_factory=list)

    def add(self, competitor: CompetitorProfile) -> None:
        self.items.append(competitor)

    def by_type(self, competitor_type: str) -> List[CompetitorProfile]:
        return [c for c in self.items if c.competitor_type == competitor_type]

    def by_domain(self, domain: str) -> List[CompetitorProfile]:
        return [
            c
            for c in self.items
            if c.website
            and urlsplit(c.website).hostname
            and urlsplit(c.website).hostname.lower() == domain.lower()
        ]

    def sorted_by_score(self) -> List[CompetitorProfile]:
        return sorted(self.items, key=lambda c: c.qualification_score, reverse=True)


__all__ = [
    "CompetitorProfile",
    "CompetitorCollection",
    "CompetitorType",
    "QualificationFactor",
    "CompetitorEvidenceItem",
]
