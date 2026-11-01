"""Competitor profiles and evidence tables.

Revision: 0003_competitors
Revises: 0002_company_profiles
Create Date: 2026-11-01

Adds persistent storage for competitor profiles and evidence claims produced by
the Competitor Discovery Agent (Phase 2B).

Tables:
- competitors: structured competitor profiles (JSON) with organization
  ownership and research-context scoping for tenant isolation.
- competitor_evidence: evidence items supporting competitor qualification
  claims, with full provenance metadata and foreign key to competitors.

A unique constraint prevents duplicate competitor records for the same company
within the same organization and research context.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003_competitors"
down_revision: Union[str, None] = "0002_company_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_researches_research_org",
        "researches",
        ["research_id", "organization_id"],
    )
    op.create_table(
        "competitors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("competitor_id", sa.String(length=64), nullable=False),
        sa.Column("research_id", sa.String(length=64), nullable=False),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("company_key", sa.String(length=255), nullable=False),
        sa.Column("website", sa.String(length=512), nullable=True),
        sa.Column("website_key", sa.String(length=255), nullable=True),
        sa.Column("competitor_type", sa.String(length=32), nullable=False),
        sa.Column("company_description", sa.Text(), nullable=True),
        sa.Column("profile", sa.JSON(), nullable=True),
        sa.Column("qualification_score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("verification_status", sa.String(length=32), nullable=False),
        sa.Column("source_references", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
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
    )
    op.create_index("ix_competitors_org", "competitors", ["organization_id"])
    op.create_index("ix_competitors_research", "competitors", ["research_id"])
    op.create_index("ix_competitors_type", "competitors", ["competitor_type"])

    op.create_table(
        "competitor_evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("evidence_id", sa.String(length=64), nullable=False),
        sa.Column("competitor_id", sa.String(length=64), nullable=False),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("research_id", sa.String(length=64), nullable=False),
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
        sa.Column("claim", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=1024), nullable=False),
        sa.Column("source_title", sa.String(length=512), nullable=True),
        sa.Column("source_domain", sa.String(length=255), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "retrieved_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("verification_status", sa.String(length=32), nullable=False),
        sa.Column("raw_snippet", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evidence_id", name="uq_competitor_evidence_evidence_id"),
    )
    op.create_index("ix_competitor_evidence_org", "competitor_evidence", ["organization_id"])
    op.create_index(
        "ix_competitor_evidence_research", "competitor_evidence", ["research_id"]
    )
    op.create_index(
        "ix_competitor_evidence_competitor",
        "competitor_evidence",
        ["competitor_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_competitor_evidence_competitor", table_name="competitor_evidence")
    op.drop_index("ix_competitor_evidence_research", table_name="competitor_evidence")
    op.drop_index("ix_competitor_evidence_org", table_name="competitor_evidence")
    op.drop_table("competitor_evidence")
    op.drop_index("ix_competitors_type", table_name="competitors")
    op.drop_index("ix_competitors_research", table_name="competitors")
    op.drop_index("ix_competitors_org", table_name="competitors")
    op.drop_table("competitors")
    op.drop_constraint(
        "uq_researches_research_org",
        "researches",
        type_="unique",
    )
