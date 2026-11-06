"""Pydantic schemas for the Strategic Analyst Agent (Phase 2F).

Defines strongly-typed data structures for:
- Strategic company profiles
- Multi-dimensional competitor comparisons
- Competitive positioning & vulnerability analysis
- Structured SWOT analysis (Strengths, Weaknesses, Opportunities, Threats)
- Market opportunities with qualitative impact and feasibility
- Competitive threats with severity, likelihood, and mitigations
- Actionable strategic recommendations with time horizons and metrics
- Evidence gaps, unresolved contradictions, and human review dependencies
- Strict separation of facts, inferences, and hypotheses
- Deterministic, explainable confidence scoring
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InformationClass(str, Enum):
    """Classification of analytical statements by degree of empirical support."""

    FACT = "fact"  # Directly supported by verified evidence
    INFERENCE = "inference"  # Derived conclusion logically synthesized from multiple facts
    HYPOTHESIS = "hypothesis"  # Plausible hypothesis requiring additional empirical validation


class FeatureAvailability(str, Enum):
    """Explicit state of competitor or company capabilities."""

    AVAILABLE = "available"
    NOT_AVAILABLE_SUPPORTED_BY_EVIDENCE = "not_available_supported_by_evidence"
    UNKNOWN = "unknown"
    PARTIALLY_AVAILABLE = "partially_available"
    CONFLICTING_EVIDENCE = "conflicting_evidence"


class StrategicPriority(str, Enum):
    """Action priority classification for strategic recommendations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TimeHorizon(str, Enum):
    """Strategic execution timeframes."""

    IMMEDIATE = "immediate"  # 0 - 30 days
    SHORT_TERM = "short_term"  # 1 - 3 months
    MEDIUM_TERM = "medium_term"  # 3 - 6 months
    LONG_TERM = "long_term"  # 6 - 12 months


class StrategicImpact(str, Enum):
    """Qualitative strategic impact level."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ThreatSeverity(str, Enum):
    """Severity classification for external threats."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ThreatLikelihood(str, Enum):
    """Likelihood assessment for competitive threats."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StrategicCompanyProfile(BaseModel):
    """Evidence-backed strategic summary of the target company."""

    model_config = ConfigDict(str_strip_whitespace=True)

    company_name: str = Field(..., min_length=1)
    core_business_model: Optional[str] = None
    main_products_and_services: List[str] = Field(default_factory=list)
    target_customer_segments: List[str] = Field(default_factory=list)
    geographic_positioning: List[str] = Field(default_factory=list)
    pricing_strategy: Optional[str] = None
    differentiating_capabilities: List[str] = Field(default_factory=list)
    market_positioning: Optional[str] = None
    key_dependencies: List[str] = Field(default_factory=list)
    competitive_advantages: List[str] = Field(default_factory=list)
    known_limitations: List[str] = Field(default_factory=list)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    information_class: InformationClass = InformationClass.FACT
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class DimensionComparison(BaseModel):
    """Comparison along a specific strategic dimension."""

    model_config = ConfigDict(str_strip_whitespace=True)

    dimension: str = Field(..., description="e.g. products_and_services, pricing, geography, etc.")
    target_company_value: Optional[str] = None
    competitor_value: Optional[str] = None
    availability_status: FeatureAvailability = FeatureAvailability.UNKNOWN
    comparison_notes: str = Field(default="")
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    information_class: InformationClass = InformationClass.INFERENCE
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class CompetitorComparison(BaseModel):
    """Structured comparison between the target company and a competitor."""

    model_config = ConfigDict(str_strip_whitespace=True)

    competitor_id: str = Field(..., min_length=1)
    competitor_name: str = Field(..., min_length=1)
    competitor_type: str = Field(default="direct")  # direct, indirect, emerging, substitute
    comparison_dimensions: List[DimensionComparison] = Field(default_factory=list)
    observed_strengths: List[str] = Field(default_factory=list)
    observed_weaknesses: List[str] = Field(default_factory=list)
    differentiation_summary: str = Field(default="")
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class CompetitivePositioning(BaseModel):
    """Macro positioning analysis across the competitive landscape."""

    model_config = ConfigDict(str_strip_whitespace=True)

    direct_competitors: List[str] = Field(default_factory=list)
    indirect_competitors: List[str] = Field(default_factory=list)
    potential_substitutes: List[str] = Field(default_factory=list)
    differentiation_opportunities: List[str] = Field(default_factory=list)
    competitive_overlap: List[str] = Field(default_factory=list)
    positioning_gaps: List[str] = Field(default_factory=list)
    strategic_advantages: List[str] = Field(default_factory=list)
    competitive_vulnerabilities: List[str] = Field(default_factory=list)
    rationales: Dict[str, str] = Field(default_factory=dict)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class SWOTItem(BaseModel):
    """A single SWOT element backed by evidence or qualified inference."""

    model_config = ConfigDict(str_strip_whitespace=True)

    item_id: str = Field(..., min_length=1)
    category: str = Field(..., description="strength | weakness | opportunity | threat")
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    strategic_impact: StrategicImpact = StrategicImpact.MEDIUM
    explanation: str = Field(default="")
    relevant_assumptions: List[str] = Field(default_factory=list)
    information_class: InformationClass = InformationClass.INFERENCE

    @field_validator("category")
    @classmethod
    def _validate_category(cls, v: str) -> str:
        cat = v.lower().strip()
        if cat not in {"strength", "weakness", "opportunity", "threat"}:
            raise ValueError(f"Invalid SWOT category: {v}")
        return cat


class SWOTAnalysis(BaseModel):
    """Complete evidence-backed SWOT matrix."""

    model_config = ConfigDict(str_strip_whitespace=True)

    strengths: List[SWOTItem] = Field(default_factory=list)
    weaknesses: List[SWOTItem] = Field(default_factory=list)
    opportunities: List[SWOTItem] = Field(default_factory=list)
    threats: List[SWOTItem] = Field(default_factory=list)
    overall_summary: str = Field(default="")


class MarketOpportunity(BaseModel):
    """An identified commercial or product market opportunity."""

    model_config = ConfigDict(str_strip_whitespace=True)

    opportunity_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    market_or_customer_need: str = Field(..., min_length=1)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    opportunity_rationale: str = Field(..., min_length=1)
    potential_business_impact: str = Field(..., min_length=1)
    implementation_complexity: StrategicImpact = StrategicImpact.MEDIUM
    time_horizon: TimeHorizon = TimeHorizon.SHORT_TERM
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    risks_and_assumptions: List[str] = Field(default_factory=list)
    information_class: InformationClass = InformationClass.INFERENCE


class CompetitiveThreat(BaseModel):
    """A strategic competitive or market threat."""

    model_config = ConfigDict(str_strip_whitespace=True)

    threat_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    severity: ThreatSeverity = ThreatSeverity.MEDIUM
    likelihood: ThreatLikelihood = ThreatLikelihood.MEDIUM
    impact: str = Field(..., min_length=1)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    risks_and_mitigations: List[str] = Field(default_factory=list)
    information_class: InformationClass = InformationClass.INFERENCE


class StrategicRecommendation(BaseModel):
    """An actionable, prioritized strategic recommendation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    recommendation_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    strategic_objective: str = Field(..., min_length=1)
    supporting_analysis: str = Field(default="")
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    expected_business_impact: str = Field(..., min_length=1)
    priority: StrategicPriority = StrategicPriority.HIGH
    implementation_difficulty: StrategicImpact = StrategicImpact.MEDIUM
    time_horizon: TimeHorizon = TimeHorizon.SHORT_TERM
    risks: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    information_class: InformationClass = InformationClass.INFERENCE


class EvidenceGap(BaseModel):
    """An identified gap in intelligence requiring further investigation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    gap_id: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    impact_on_analysis: str = Field(default="")
    recommended_further_research: str = Field(default="")


class StrategicAnalysisResult(BaseModel):
    """Complete, traceable strategic analysis output for ACIS Phase 2F."""

    model_config = ConfigDict(str_strip_whitespace=True)

    research_id: str = Field(..., min_length=1)
    organization_id: Optional[str] = None
    target_company: str = Field(..., min_length=1)
    analysis_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    company_profile: StrategicCompanyProfile
    competitor_comparisons: List[CompetitorComparison] = Field(default_factory=list)
    competitive_positioning: CompetitivePositioning
    swot_analysis: SWOTAnalysis
    market_opportunities: List[MarketOpportunity] = Field(default_factory=list)
    competitive_threats: List[CompetitiveThreat] = Field(default_factory=list)
    strategic_recommendations: List[StrategicRecommendation] = Field(default_factory=list)
    evidence_gaps: List[EvidenceGap] = Field(default_factory=list)
    unresolved_contradictions: List[Dict[str, Any]] = Field(default_factory=list)
    human_review_dependencies: List[Dict[str, Any]] = Field(default_factory=list)
    overall_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    analysis_status: str = Field(default="completed")
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "InformationClass",
    "FeatureAvailability",
    "StrategicPriority",
    "TimeHorizon",
    "StrategicImpact",
    "ThreatSeverity",
    "ThreatLikelihood",
    "StrategicCompanyProfile",
    "DimensionComparison",
    "CompetitorComparison",
    "CompetitivePositioning",
    "SWOTItem",
    "SWOTAnalysis",
    "MarketOpportunity",
    "CompetitiveThreat",
    "StrategicRecommendation",
    "EvidenceGap",
    "StrategicAnalysisResult",
]
