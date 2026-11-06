"""Pydantic schemas for the Report Generation Agent (Phase 2G).

Defines strongly-typed structures for:
- Report metadata and client confidentiality
- 14 distinct structured report sections
- Evidence citations and provenance appendix
- Traceable fact/inference/hypothesis classifications
- Multi-format generation references (JSON, Markdown, PDF)
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.strategy import (
    CompetitivePositioning,
    CompetitiveThreat,
    CompetitorComparison,
    EvidenceGap,
    InformationClass,
    MarketOpportunity,
    StrategicCompanyProfile,
    StrategicPriority,
    StrategicRecommendation,
    SWOTAnalysis,
    TimeHorizon,
)


class ReportFormat(str, Enum):
    """Supported report export formats."""

    JSON = "json"
    MARKDOWN = "markdown"
    PDF = "pdf"


class ConfidentialityClassification(str, Enum):
    """Confidentiality tier for intelligence reports."""

    CONFIDENTIAL = "CONFIDENTIAL - FOR CLIENT USE ONLY"
    INTERNAL_RESTRICTED = "INTERNAL RESTRICTED"
    PROPRIETARY = "PROPRIETARY AND PRIVILEGED"


class ReportMetadata(BaseModel):
    """Report header and provenance metadata."""

    model_config = ConfigDict(str_strip_whitespace=True)

    report_id: str = Field(..., min_length=1)
    research_id: str = Field(..., min_length=1)
    organization_id: str = Field(..., min_length=1)
    target_company: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    version: str = Field(default="1.0")
    confidentiality: str = Field(default=ConfidentialityClassification.CONFIDENTIAL.value)
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: str = Field(default="completed")
    formats: List[ReportFormat] = Field(
        default_factory=lambda: [ReportFormat.JSON, ReportFormat.MARKDOWN, ReportFormat.PDF]
    )
    overall_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    client_name: Optional[str] = None
    executive_summary_preview: str = Field(default="")
    artifact_references: Dict[str, str] = Field(default_factory=dict)


class EvidenceCitationItem(BaseModel):
    """A single cited piece of evidence within the report appendix."""

    model_config = ConfigDict(str_strip_whitespace=True)

    evidence_id: str
    claim: str
    source_name: str
    source_url: str
    source_domain: str
    published_at: Optional[Union[datetime, str]] = None
    retrieved_at: Optional[Union[datetime, str]] = None
    verification_status: str
    confidence_score: float
    information_class: InformationClass = InformationClass.FACT
    referenced_in_sections: List[str] = Field(default_factory=list)


class ContradictionReportItem(BaseModel):
    """A detected contradiction surfaced transparently in the report."""

    model_config = ConfigDict(str_strip_whitespace=True)

    contradiction_id: str
    topic: str
    claim_a: str
    source_url_a: str
    claim_b: str
    source_url_b: str
    severity: str
    explanation: str
    confidence_impact: str
    required_action: str


class ResearchLimitationItem(BaseModel):
    """An established limitation or blind spot in the research scope."""

    model_config = ConfigDict(str_strip_whitespace=True)

    topic: str
    description: str
    impact: str
    remediation_recommendation: str


class ExecutiveSummary(BaseModel):
    """Section 2: Decision-maker executive summary."""

    model_config = ConfigDict(str_strip_whitespace=True)

    target_company_overview: str
    main_competitive_findings: List[str] = Field(default_factory=list)
    key_competitor_developments: List[str] = Field(default_factory=list)
    major_advantages: List[str] = Field(default_factory=list)
    major_weaknesses: List[str] = Field(default_factory=list)
    key_opportunities: List[str] = Field(default_factory=list)
    key_threats: List[str] = Field(default_factory=list)
    top_recommendations: List[str] = Field(default_factory=list)
    overall_evidence_confidence: float
    narrative: str = Field(default="")


class ResearchScopeMethodology(BaseModel):
    """Section 3: Scope, criteria, and analytical methodology."""

    model_config = ConfigDict(str_strip_whitespace=True)

    research_objectives: str
    target_company: str
    competitors_examined: List[str] = Field(default_factory=list)
    research_categories: List[str] = Field(default_factory=list)
    collection_methodology: str
    validation_methodology: str
    confidence_scoring_methodology: str
    known_limitations_overview: str


class StrategicReport(BaseModel):
    """Complete 14-section Competitive Intelligence Report output."""

    model_config = ConfigDict(str_strip_whitespace=True)

    metadata: ReportMetadata
    company: Optional[str] = None
    cover_page: Dict[str, Any]
    executive_summary: ExecutiveSummary
    research_scope: ResearchScopeMethodology
    target_company_profile: StrategicCompanyProfile
    competitor_profiles: List[Dict[str, Any]] = Field(default_factory=list)
    competitive_comparison: List[CompetitorComparison] = Field(default_factory=list)
    competitive_positioning: CompetitivePositioning
    swot_analysis: SWOTAnalysis
    market_opportunities: List[MarketOpportunity] = Field(default_factory=list)
    threat_assessment: List[CompetitiveThreat] = Field(default_factory=list)
    strategic_recommendations: List[StrategicRecommendation] = Field(default_factory=list)
    evidence_appendix: List[EvidenceCitationItem] = Field(default_factory=list)
    contradictions_and_review: List[ContradictionReportItem] = Field(default_factory=list)
    research_limitations: List[ResearchLimitationItem] = Field(default_factory=list)
    generation_metadata: Dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "ReportFormat",
    "ConfidentialityClassification",
    "ReportMetadata",
    "EvidenceCitationItem",
    "ContradictionReportItem",
    "ResearchLimitationItem",
    "ExecutiveSummary",
    "ResearchScopeMethodology",
    "StrategicReport",
]
