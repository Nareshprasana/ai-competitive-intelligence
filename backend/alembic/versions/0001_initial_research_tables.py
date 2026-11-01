"""Initial research tables.

Revision: 0001_initial_research_tables
Revises:
Create Date: 2026-11-01

Preparation migration for the PostgreSQL + pgvector backend. It is designed to
run only once DATABASE_URL is configured and a live PostgreSQL instance is
available. Until then, the application degrades gracefully without a database.

Tables:
- researches: one row per research run, storing the research_id, status,
  review_status, full results JSON, errors JSON, and timestamps. Owned by an
  organization_id for tenant isolation (server-side enforced).

LangGraph checkpoint state is stored in dedicated checkpoints/checkpoint_writes
tables created at runtime by AsyncPostgresSaver.setup() (separate from business
records). pgvector is not required for this migration; the extension is a
prerequisite for future vector/semantic-search columns.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

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
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=False),
        sa.Column("research_question", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=True),
        sa.Column("results", sa.JSON(), nullable=True),
        sa.Column("errors", sa.JSON(), nullable=True),
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
        sa.UniqueConstraint("research_id", name="uq_researches_research_id"),
    )
    op.create_index("ix_researches_organization_id", "researches", ["organization_id"])
    op.create_index("ix_researches_status", "researches", ["status"])
    op.create_index(
        "ix_researches_org_status", "researches", ["organization_id", "status"]
    )


def downgrade() -> None:
    op.drop_index("ix_researches_org_status", table_name="researches")
    op.drop_index("ix_researches_status", table_name="researches")
    op.drop_index("ix_researches_organization_id", table_name="researches")
    op.drop_table("researches")
