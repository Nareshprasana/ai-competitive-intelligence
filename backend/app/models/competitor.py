"""SQLAlchemy ORM models for competitor profiles and evidence.

Tables:
- ``competitors``: one row per competitor identified for a research run.
  Stores the structured CompetitorProfile JSON plus indexed queryable fields.
  Owned by an ``organization_id`` for tenant isolation and linked to a
  ``research_id`` for research-context scoping.
- ``competitor_evidence``: one row per evidence item supporting a competitor
  qualification claim. Links back to a ``competitors`` row via
  ``competitor_id`` and carries full provenance metadata.
"""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.research import Research  # noqa: F401 - register research table
from app.security.crypto import EncryptedJSON, EncryptedText


class Competitor(Base):
    """Persistent competitor profile discovered during research."""

    __tablename__ = "competitors"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    competitor_id: Mapped[str] = mapped_column(
        sa.String(64), index=True, nullable=False
    )
    research_id: Mapped[str] = mapped_column(
        sa.String(64), index=True, nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        sa.String(128),
        sa.ForeignKey("organizations.organization_id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    company_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    company_key: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    website: Mapped[str | None] = mapped_column(sa.String(512), nullable=True)
    website_key: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    competitor_type: Mapped[str] = mapped_column(
        sa.String(32), index=True, nullable=False
    )
    company_description: Mapped[str | None] = mapped_column(
        EncryptedText("competitors.company_description"), nullable=True
    )
    profile: Mapped[dict | None] = mapped_column(
        EncryptedJSON("competitors.profile"), nullable=True
    )
    qualification_score: Mapped[float] = mapped_column(sa.Float, nullable=False)
    confidence: Mapped[float] = mapped_column(sa.Float, nullable=False)
    verification_status: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    source_references: Mapped[list | None] = mapped_column(
        EncryptedJSON("competitors.source_references"), nullable=True
    )
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    research: Mapped["Research"] = relationship(
        "Research",
    )

    # One-to-many: a competitor can have many evidence claims.
    evidence: Mapped[list["CompetitorEvidence"]] = relationship(
        "CompetitorEvidence",
        back_populates="competitor",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # Prevent duplicate competitor records for the same company within the
        # same organization and research context.
        sa.UniqueConstraint(
            "research_id",
            "organization_id",
            "company_key",
            name="uq_competitors_research_org_company_key",
        ),
        sa.UniqueConstraint(
            "research_id",
            "organization_id",
            "website_key",
            name="uq_competitors_research_org_website_key",
        ),
        sa.UniqueConstraint(
            "competitor_id",
            "organization_id",
            "research_id",
            name="uq_competitors_id_org_research",
        ),
        sa.ForeignKeyConstraint(
            ["research_id", "organization_id"],
            ["researches.research_id", "researches.organization_id"],
            name="fk_competitors_research_owner",
            ondelete="CASCADE",
        ),
        sa.Index("ix_competitors_org", "organization_id"),
        sa.Index("ix_competitors_research", "research_id"),
        sa.Index("ix_competitors_type", "competitor_type"),
    )


class CompetitorEvidence(Base):
    """Persistent evidence claim supporting a competitor qualification."""

    __tablename__ = "competitor_evidence"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    evidence_id: Mapped[str] = mapped_column(
        sa.String(64), nullable=False
    )
    competitor_id: Mapped[str] = mapped_column(
        sa.String(64), index=True, nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        sa.String(128),
        sa.ForeignKey("organizations.organization_id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    research_id: Mapped[str] = mapped_column(
        sa.String(64), index=True, nullable=False
    )
    claim: Mapped[str] = mapped_column(
        EncryptedText("competitor_evidence.claim"), nullable=False
    )
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
    raw_snippet: Mapped[str | None] = mapped_column(
        EncryptedText("competitor_evidence.raw_snippet"), nullable=True
    )

    competitor: Mapped["Competitor"] = relationship(
        "Competitor",
        back_populates="evidence",
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "evidence_id", name="uq_competitor_evidence_evidence_id"
        ),
        sa.ForeignKeyConstraint(
            ["competitor_id", "organization_id", "research_id"],
            [
                "competitors.competitor_id",
                "competitors.organization_id",
                "competitors.research_id",
            ],
            name="fk_competitor_evidence_owner",
            ondelete="CASCADE",
        ),
        sa.Index("ix_competitor_evidence_org", "organization_id"),
        sa.Index("ix_competitor_evidence_research", "research_id"),
        sa.Index("ix_competitor_evidence_competitor", "competitor_id"),
    )


__all__ = ["Competitor", "CompetitorEvidence"]
