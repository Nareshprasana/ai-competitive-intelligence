"""SQLAlchemy repository for persistent research records.

All queries enforce organization ownership server-side: a caller must supply the
owning ``organization_id`` and every query filters by it. Client-supplied
organization identifiers are never trusted as authorization evidence; they are
treated as the *intended* owner and verified at write time.

The repository never leaks ORM models to callers; it returns plain-dict
representations that the service layer converts into Pydantic schemas.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ResearchError
from app.core.logging import get_logger
from app.models.research import Research

logger = get_logger("app.repositories.research")


class ResearchRepository:
    """Database-backed research record access with organization isolation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        research_id: str,
        organization_id: str,
        company_name: str,
        industry: str,
        research_question: str,
        status: str,
        review_status: Optional[str] = None,
        results: Optional[Dict[str, Any]] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Insert a new research record.

        Raises ``ResearchError`` on database failure. Organization ownership is
        enforced by storing the supplied ``organization_id`` on the record.
        """
        try:
            record = Research(
                research_id=research_id,
                organization_id=organization_id,
                company_name=company_name,
                industry=industry,
                research_question=research_question,
                status=status,
                review_status=review_status,
                results=results,
                errors=errors or [],
            )
            self._session.add(record)
            await self._session.flush()
            await self._session.refresh(record)
            return self._to_dict(record)
        except Exception as exc:  # noqa: BLE001 - translate DB failures cleanly
            await self._session.rollback()
            logger.error(
                "Research persistence failed research_id=%s error_type=%s",
                research_id,
                type(exc).__name__,
            )
            raise ResearchError(
                "Failed to persist research record.",
                details={"research_id": research_id},
            ) from exc

    async def get_by_id(
        self, research_id: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch a research record by ID, restricted to one organization.

        Returns ``None`` when no record matches — callers treat this as
        not-found rather than leaking cross-organization data.
        """
        stmt = select(Research).where(
            Research.research_id == research_id,
            Research.organization_id == organization_id,
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        return self._to_dict(record) if record is not None else None

    async def update_status(
        self,
        *,
        research_id: str,
        organization_id: str,
        status: str,
        review_status: Optional[str] = None,
        results: Optional[Dict[str, Any]] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update an existing research record, restricted to one organization.

        Returns ``None`` when no matching record exists for the organization.
        """
        stmt = select(Research).where(
            Research.research_id == research_id,
            Research.organization_id == organization_id,
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None

        record.status = status
        if review_status is not None:
            record.review_status = review_status
        if results is not None:
            record.results = results
        if errors is not None:
            record.errors = errors
        record.updated_at = datetime.now(timezone.utc)

        try:
            await self._session.flush()
            await self._session.refresh(record)
            return self._to_dict(record)
        except Exception as exc:  # noqa: BLE001 - translate DB failures cleanly
            await self._session.rollback()
            logger.error(
                "Research update failed research_id=%s error_type=%s",
                research_id,
                type(exc).__name__,
            )
            raise ResearchError(
                "Failed to update research record.",
                details={"research_id": research_id},
            ) from exc

    async def list_by_organization(
        self, organization_id: str, *, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List research records for one organization (newest first)."""
        stmt = (
            select(Research)
            .where(Research.organization_id == organization_id)
            .order_by(Research.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_dict(record) for record in result.scalars().all()]

    async def organization_has_record(
        self, research_id: str, organization_id: str
    ) -> bool:
        """True only when the organization owns the research record."""
        record = await self.get_by_id(research_id, organization_id)
        return record is not None

    @staticmethod
    def _to_dict(record: Research) -> Dict[str, Any]:
        return {
            "id": record.id,
            "research_id": record.research_id,
            "organization_id": record.organization_id,
            "company_name": record.company_name,
            "industry": record.industry,
            "research_question": record.research_question,
            "status": record.status,
            "review_status": record.review_status,
            "results": record.results,
            "errors": record.errors or [],
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        }


__all__ = ["ResearchRepository"]
