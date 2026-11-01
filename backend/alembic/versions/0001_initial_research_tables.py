"""Initial research tables.

Revision: 0001_initial_research_tables
Revises:
Create Date: 2026-11-01

Preparation migration for the PostgreSQL + pgvector backend. It is designed to
run only once DATABASE_URL is configured and a live PostgreSQL instance is
available. Until then, the application degrades gracefully without a database.

Tables:
- researches: one row per research run, storing the research_id and status.
- research_artifacts: JSONB artifacts produced by graph nodes (plan, profile,
  competitors, report, etc.).
- research_evidence: validated evidence items with an optional pgvector
  embedding column (created only when the pgvector extension is available).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

try:
    from pgvector.sqlalchemy import Vector

    HAS_PGVECTOR = True
except Exception:  # pragma: no cover - pgvector optional until PG provisioned
    HAS_PGVECTOR = False

# revision identifiers, used by Alembic.
revision: str = "0001_initial_research_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "researches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("research_id", sa.String(length=64), nullable=False),
        sa.Column("organization_id", sa.String(length=128), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=False),
        sa.Column("research_question", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=True),
        sa.Column("results", sa.JSON(), nullable=True),
        sa.Column("errors", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("research_id", name="uq_researches_research_id"),
    )
    op.create_index("ix_researches_organization_id", "researches", ["organization_id"])
    op.create_index("ix_researches_status", "researches", ["status"])

    op.create_table(
        "research_artifacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("research_id", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["research_id"],
            ["researches.research_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_research_artifacts_research_id", "research_artifacts", ["research_id"]
    )

    # Evidence table with optional pgvector embedding column.
    evidence_columns = [
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("research_id", sa.String(length=64), nullable=False),
        sa.Column("evidence_id", sa.String(length=64), nullable=False),
        sa.Column("claim", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("validated", sa.Boolean(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["research_id"],
            ["researches.research_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    ]
    if HAS_PGVECTOR:
        # 1536-dim embeddings (DeepSeek/OpenRouter embedding default).
        evidence_columns.append(sa.Column("embedding", Vector(1536), nullable=True))

    op.create_table("research_evidence", *evidence_columns)
    op.create_index(
        "ix_research_evidence_research_id", "research_evidence", ["research_id"]
    )


def downgrade() -> None:
    op.drop_table("research_evidence")
    op.drop_table("research_artifacts")
    op.drop_table("researches")
