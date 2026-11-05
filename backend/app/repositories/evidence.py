"""Repository for persistent evidence claim records.

All queries enforce organization ownership server-side.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResearchError
from app.core.logging import get_logger
from app.models.company import EvidenceClaim

logger = get_logger("app.repositories.evidence")


class EvidenceRepository:
    """Database-backed evidence claim access with organization isolation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        evidence_id: str,
        company_profile_id: int,
        organization_id: str,
        claim: str,
        source_url: str,
        source_title: Optional[str] = None,
        source_domain: str = "",
        published_at: Optional[datetime] = None,
        evidence_type: str = "other",
        confidence: float = 0.5,
        verification_status: str = "unverified",
        raw_snippet: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            record = EvidenceClaim(
                evidence_id=evidence_id,
                company_profile_id=company_profile_id,
                organization_id=organization_id,
                claim=claim,
                source_url=source_url,
                source_title=source_title,
                source_domain=source_domain,
                published_at=published_at,
                evidence_type=evidence_type,
                confidence=confidence,
                verification_status=verification_status,
                raw_snippet=raw_snippet,
            )
            self._session.add(record)
            await self._session.flush()
            await self._session.refresh(record)
            return self._to_dict(record)
        except Exception as exc:
            await self._session.rollback()
            logger.error(
                "Evidence persistence failed evidence_id=%s error_type=%s",
                evidence_id,
                type(exc).__name__,
            )
            raise ResearchError(
                "Failed to persist evidence claim.",
                details={"evidence_id": evidence_id},
            ) from exc

    async def get_by_id(
        self, evidence_id: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        stmt = select(EvidenceClaim).where(
            EvidenceClaim.evidence_id == evidence_id,
            EvidenceClaim.organization_id == organization_id,
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        return self._to_dict(record) if record is not None else None

    async def list_by_profile(
        self, company_profile_id: int, organization_id: str
    ) -> List[Dict[str, Any]]:
        stmt = select(EvidenceClaim).where(
            EvidenceClaim.company_profile_id == company_profile_id,
            EvidenceClaim.organization_id == organization_id,
        )
        result = await self._session.execute(stmt)
        return [self._to_dict(record) for record in result.scalars().all()]

    async def list_by_organization(
        self, organization_id: str, *, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        stmt = (
            select(EvidenceClaim)
            .where(EvidenceClaim.organization_id == organization_id)
            .order_by(EvidenceClaim.retrieved_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_dict(record) for record in result.scalars().all()]

    @staticmethod
    def _to_dict(record: EvidenceClaim) -> Dict[str, Any]:
        return {
            "id": record.id,
            "evidence_id": record.evidence_id,
            "company_profile_id": record.company_profile_id,
            "organization_id": record.organization_id,
            "claim": record.claim,
            "source_url": record.source_url,
            "source_title": record.source_title,
            "source_domain": record.source_domain,
            "published_at": record.published_at.isoformat() if record.published_at else None,
            "retrieved_at": record.retrieved_at.isoformat() if record.retrieved_at else None,
            "evidence_type": record.evidence_type,
            "confidence": record.confidence,
            "verification_status": record.verification_status,
            "raw_snippet": record.raw_snippet,
        }


__all__ = ["EvidenceRepository"]
