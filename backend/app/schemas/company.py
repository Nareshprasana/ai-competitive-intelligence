"""Pydantic schemas for company profiles and related structured data."""

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CompanySize(BaseModel):
    """Company size estimate."""

    model_config = ConfigDict(str_strip_whitespace=True)

    employees_min: Optional[int] = Field(
        default=None, ge=0, description="Minimum employee count."
    )
    employees_max: Optional[int] = Field(
        default=None, ge=0, description="Maximum employee count."
    )
    label: Optional[str] = Field(
        default=None, description="Human-readable size label (e.g. '11-50')."
    )

    @field_validator("employees_max")
    @classmethod
    def _max_gte_min(cls, v: Optional[int], info: Any) -> Optional[int]:
        if v is not None and info.data.get("employees_min") is not None:
            if v < info.data["employees_min"]:
                raise ValueError("employees_max must be >= employees_min")
        return v


class CompanyProfile(BaseModel):
    """Structured company profile produced by the Company Research Agent.

    All fields are optional: unavailable information is represented as None or
    empty lists, never fabricated.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    company_name: str = Field(..., min_length=1, description="Company name.")
    industry: Optional[str] = Field(default=None, description="Industry classification.")
    description: Optional[str] = Field(
        default=None, description="Plain-language company description."
    )
    history: Optional[str] = Field(
        default=None, description="Company history where publicly documented."
    )
    headquarters: Optional[str] = Field(
        default=None, description="Headquarters location."
    )
    geographical_presence: List[str] = Field(
        default_factory=list, description="Geographic markets / presence locations."
    )
    founders: List[str] = Field(
        default_factory=list, description="Founders where publicly documented."
    )
    leadership: List[str] = Field(
        default_factory=list, description="Key leadership team members."
    )
    products: List[str] = Field(
        default_factory=list, description="Products and services."
    )
    business_model: Optional[str] = Field(
        default=None, description="How the company makes money."
    )
    target_customers: List[str] = Field(
        default_factory=list, description="Target customer segments."
    )
    size: Optional[CompanySize] = Field(default=None, description="Company size estimate.")
    website: Optional[str] = Field(default=None, description="Official website URL.")
    financial_info: Optional[str] = Field(
        default=None, description="Publicly available financial information."
    )
    recent_developments: List[str] = Field(
        default_factory=list, description="Recent company developments."
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
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("website must be an http/https URL")
        return v


__all__ = ["CompanyProfile", "CompanySize"]
