"""SQLAlchemy repository for persistent strategic analysis records (Phase 2F).

Provides tenant-isolated persistence and retrieval of strategic analysis results
stored inside encrypted research result containers.
"""

from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResearchError
from app.core.logging import get_logger
from app.models.research import Research

logger = get_logger("app.repositories.strategy")


class StrategyRepository:
    """Database access for strategic intelligence with organization isolation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_strategic_analysis(
        self,
        *,
        research_id: str,
        organization_id: str,
        strategic_analysis: Dict[str, Any],
        review_status: Optional[str] = None,
    ) -> bool:
        """Persist strategic analysis results inside the encrypted research record.

        Enforces tenant isolation by matching both research_id and organization_id.
        """
        try:
            stmt = select(Research).where(
                Research.research_id == research_id,
                Research.organization_id == organization_id,
            )
            result = await self._session.execute(stmt)
            record = result.scalar_one_or_none()
            if record is None:
                logger.warning(
                    "Research record not found for strategic analysis research_id=%s org_id=%s",
                    research_id,
                    organization_id,
                )
                return False

            existing_results = dict(record.results or {})
            existing_results["strategic_analysis"] = strategic_analysis
            record.results = existing_results

            if review_status:
                record.review_status = review_status

            await self._session.flush()
            return True
        except Exception as exc:  # noqa: BLE001
            await self._session.rollback()
            logger.error(
                "Failed to persist strategic analysis research_id=%s error=%s",
                research_id,
                exc,
            )
            raise ResearchError(
                "Failed to save strategic analysis.",
                details={"research_id": research_id},
            ) from exc

    async def get_strategic_analysis(
        self, research_id: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve strategic analysis, strictly isolated by organization_id."""
        stmt = select(Research).where(
            Research.research_id == research_id,
            Research.organization_id == organization_id,
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None or not record.results:
            return None
        return record.results.get("strategic_analysis")


__all__ = ["StrategyRepository"]
