"""SQLAlchemy ORM models for persistent research records.

Tables:
- ``researches``: one row per research run. Stores the research_id, status,
  review_status, full results JSON, errors JSON, and timestamps. Owned by an
  ``organization_id`` for tenant isolation (server-side enforced).

pgvector is NOT used for storage in Phase 1.5 (the extension is not available
on this Windows PostgreSQL). The ``results`` and ``errors`` columns are JSONB,
which keeps the design simple and dependency-light. The Alembic migration
(0001_initial_research_tables) is pgvector-ready should vector columns be
added later.
"""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Research(Base):
    """A persistent competitive-intelligence research run."""

    __tablename__ = "researches"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    research_id: Mapped[str] = mapped_column(
        sa.String(64), unique=True, index=True, nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        sa.String(128), index=True, nullable=False
    )
    company_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    industry: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    research_question: Mapped[str] = mapped_column(sa.Text, nullable=False)
    status: Mapped[str] = mapped_column(sa.String(32), index=True, nullable=False)
    review_status: Mapped[str | None] = mapped_column(sa.String(32), nullable=True)
    # Full structured result produced by the LangGraph workflow.
    results: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    # Errors recorded by any failed graph node.
    errors: Mapped[list | None] = mapped_column(sa.JSON, nullable=True)
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Research research_id={self.research_id!r} status={self.status!r}>"

    __table_args__ = (
        # Composite index for the most common lookup: org + status.
        sa.Index("ix_researches_org_status", "organization_id", "status"),
        sa.UniqueConstraint(
            "research_id",
            "organization_id",
            name="uq_researches_research_org",
        ),
    )


__all__ = ["Research"]
