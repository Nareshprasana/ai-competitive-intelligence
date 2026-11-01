"""SQLAlchemy ORM models for company profiles and evidence.

Tables:
- ``company_profiles``: one row per researched company. Stores the structured
  CompanyProfile JSON plus indexed queryable fields. Owned by an
  ``organization_id`` for tenant isolation.
- ``evidence_claims``: one row per evidence item supporting a company profile
  claim. Each row links back to a ``company_profiles`` row via
  ``company_profile_id`` and carries full provenance metadata.
"""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CompanyProfile(Base):
    """Persistent structured company profile."""

    __tablename__ = "company_profiles"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[str] = mapped_column(
        sa.String(64), unique=True, index=True, nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        sa.String(128), index=True, nullable=False
    )
    company_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    profile: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    website: Mapped[str | None] = mapped_column(sa.String(512), nullable=True)
    source_references: Mapped[list | None] = mapped_column(sa.JSON, nullable=True)
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    # One-to-many: a company profile can have many evidence claims.
    evidence: Mapped[list["EvidenceClaim"]] = relationship(
        "EvidenceClaim", back_populates="profile", cascade="all, delete-orphan"
    )

    __table_args__ = (
        sa.Index("ix_company_profiles_org", "organization_id"),
        sa.Index("ix_company_profiles_name", "company_name"),
    )


class EvidenceClaim(Base):
    """Persistent evidence claim supporting a company profile."""

    __tablename__ = "evidence_claims"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    evidence_id: Mapped[str] = mapped_column(
        sa.String(64), unique=True, index=True, nullable=False
    )
    company_profile_id: Mapped[int] = mapped_column(
        sa.ForeignKey("company_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    organization_id: Mapped[str] = mapped_column(
        sa.String(128), index=True, nullable=False
    )
    claim: Mapped[str] = mapped_column(sa.Text, nullable=False)
    source_url: Mapped[str] = mapped_column(sa.String(1024), nullable=False)
    source_title: Mapped[str | None] = mapped_column(sa.String(512), nullable=True)
    source_domain: Mapped[str] = mapped_column(sa.String(255), index=True, nullable=False)
    published_at: Mapped[sa.DateTime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    retrieved_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    evidence_type: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(sa.Float, nullable=False)
    verification_status: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    raw_snippet: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    profile: Mapped["CompanyProfile"] = relationship(
        "CompanyProfile", back_populates="evidence"
    )

    __table_args__ = (
        sa.Index("ix_evidence_claims_org", "organization_id"),
        sa.Index("ix_evidence_claims_profile", "company_profile_id"),
    )


__all__ = ["CompanyProfile", "EvidenceClaim"]
