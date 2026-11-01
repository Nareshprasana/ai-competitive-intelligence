"""Company profiles and evidence claims tables.

Revision: 0002_company_profiles
Revises: 0001_initial_research_tables
Create Date: 2026-11-01

Adds persistent storage for company profiles and evidence claims produced by
the Company Research Agent (Phase 2A).

Tables:
- company_profiles: structured company profiles (JSON) with organization
  ownership for tenant isolation.
- evidence_claims: evidence items supporting company profile claims, with full
  provenance metadata and foreign key to company_profiles.

Organization-level isolation is enforced via organization_id indexes and
server-side query filtering in the repository layer.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_company_profiles"
down_revision: Union[str, None] = "0001_initial_research_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "company_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=True),
        sa.Column("profile", sa.JSON(), nullable=True),
        sa.Column("website", sa.String(length=512), nullable=True),
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
        sa.UniqueConstraint("company_id", name="uq_company_profiles_company_id"),
    )
    op.create_index("ix_company_profiles_org", "company_profiles", ["organization_id"])
    op.create_index(
        "ix_company_profiles_name", "company_profiles", ["company_name"]
    )

    op.create_table(
        "evidence_claims",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("evidence_id", sa.String(length=64), nullable=False),
        sa.Column(
            "company_profile_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["company_profile_id"],
            ["company_profiles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evidence_id", name="uq_evidence_claims_evidence_id"),
    )
    op.create_index("ix_evidence_claims_org", "evidence_claims", ["organization_id"])
    op.create_index(
        "ix_evidence_claims_profile", "evidence_claims", ["company_profile_id"]
    )
    op.create_index(
        "ix_evidence_claims_domain", "evidence_claims", ["source_domain"]
    )


def downgrade() -> None:
    op.drop_index("ix_evidence_claims_domain", table_name="evidence_claims")
    op.drop_index("ix_evidence_claims_profile", table_name="evidence_claims")
    op.drop_index("ix_evidence_claims_org", table_name="evidence_claims")
    op.drop_table("evidence_claims")
    op.drop_index("ix_company_profiles_name", table_name="company_profiles")
    op.drop_index("ix_company_profiles_org", table_name="company_profiles")
    op.drop_table("company_profiles")
