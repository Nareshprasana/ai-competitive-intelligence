"""Repository for persistent company profile records.

All queries enforce organization ownership server-side.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResearchError
from app.core.logging import get_logger
from app.models.company import CompanyProfile

logger = get_logger("app.repositories.company")


class CompanyRepository:
    """Database-backed company profile access with organization isolation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        company_id: str,
        organization_id: str,
        company_name: str,
        industry: Optional[str] = None,
        profile: Optional[Dict[str, Any]] = None,
        website: Optional[str] = None,
        source_references: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        try:
            record = CompanyProfile(
                company_id=company_id,
                organization_id=organization_id,
                company_name=company_name,
                industry=industry,
                profile=profile or {},
                website=website,
                source_references=source_references or [],
            )
            self._session.add(record)
            await self._session.flush()
            await self._session.refresh(record)
            return self._to_dict(record)
        except Exception as exc:
            await self._session.rollback()
            logger.error(
                "Company profile persistence failed company_id=%s error_type=%s",
                company_id,
                type(exc).__name__,
            )
            raise ResearchError(
                "Failed to persist company profile.",
                details={"company_id": company_id},
            ) from exc

    async def get_by_id(
        self, company_id: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        stmt = select(CompanyProfile).where(
            CompanyProfile.company_id == company_id,
            CompanyProfile.organization_id == organization_id,
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        return self._to_dict(record) if record is not None else None

    async def get_by_name(
        self, company_name: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        stmt = select(CompanyProfile).where(
            CompanyProfile.company_name == company_name,
            CompanyProfile.organization_id == organization_id,
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        return self._to_dict(record) if record is not None else None

    async def list_by_organization(
        self, organization_id: str, *, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        stmt = (
            select(CompanyProfile)
            .where(CompanyProfile.organization_id == organization_id)
            .order_by(CompanyProfile.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_dict(record) for record in result.scalars().all()]

    async def update_profile(
        self,
        *,
        company_id: str,
        organization_id: str,
        profile: Optional[Dict[str, Any]] = None,
        website: Optional[str] = None,
        source_references: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        stmt = select(CompanyProfile).where(
            CompanyProfile.company_id == company_id,
            CompanyProfile.organization_id == organization_id,
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        if profile is not None:
            record.profile = profile
        if website is not None:
            record.website = website
        if source_references is not None:
            record.source_references = source_references
        record.updated_at = datetime.now(timezone.utc)
        try:
            await self._session.flush()
            await self._session.refresh(record)
            return self._to_dict(record)
        except Exception as exc:
            await self._session.rollback()
            logger.error(
                "Company profile update failed company_id=%s error_type=%s",
                company_id,
                type(exc).__name__,
            )
            raise ResearchError(
                "Failed to update company profile.",
                details={"company_id": company_id},
            ) from exc

    @staticmethod
    def _to_dict(record: CompanyProfile) -> Dict[str, Any]:
        return {
            "id": record.id,
            "company_id": record.company_id,
            "organization_id": record.organization_id,
            "company_name": record.company_name,
            "industry": record.industry,
            "profile": record.profile,
            "website": record.website,
            "source_references": record.source_references or [],
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        }


__all__ = ["CompanyRepository"]
