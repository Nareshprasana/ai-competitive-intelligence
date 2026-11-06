"""Repository for persistent competitor records.

All queries enforce organization ownership server-side. Prevents duplicate
competitor records for the same company within the same organization and
research context via a database unique constraint.
"""

from datetime import datetime
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResearchError
from app.core.logging import get_logger
from app.models.competitor import Competitor, CompetitorEvidence

logger = get_logger("app.repositories.competitor")


def _company_key(company_name: str) -> str:
    return re.sub(r"[\W_]", "", company_name.casefold()) or company_name.casefold()


def _website_key(website: Optional[str]) -> Optional[str]:
    if not website:
        return None
    host = (urlsplit(website).hostname or "").casefold().rstrip(".")
    return host[4:] if host.startswith("www.") else host or None


class CompetitorRepository:
    """Database-backed competitor access with organization isolation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        competitor_id: str,
        research_id: str,
        organization_id: str,
        company_name: str,
        website: Optional[str] = None,
        competitor_type: str = "substitute",
        company_description: Optional[str] = None,
        profile: Optional[Dict[str, Any]] = None,
        qualification_score: float = 0.0,
        confidence: float = 0.5,
        verification_status: str = "unverified",
        source_references: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Insert a new competitor record.

        Raises ``ResearchError`` on database failure, including duplicate
        competitor for the same organization/research/company_name.
        """
        try:
            record = Competitor(
                competitor_id=competitor_id,
                research_id=research_id,
                organization_id=organization_id,
                company_name=company_name,
                company_key=_company_key(company_name),
                website_key=_website_key(website),
                website=website,
                competitor_type=competitor_type,
                company_description=company_description,
                profile=profile or {},
                qualification_score=qualification_score,
                confidence=confidence,
                verification_status=verification_status,
                source_references=source_references or [],
            )
            self._session.add(record)
            await self._session.flush()
            await self._session.refresh(record)
            return self._to_dict(record)
        except Exception as exc:
            await self._session.rollback()
            logger.error(
                "Competitor persistence failed competitor_id=%s error_type=%s",
                competitor_id,
                type(exc).__name__,
            )
            raise ResearchError(
                "Failed to persist competitor.",
                details={"competitor_id": competitor_id},
            ) from exc

    async def get_by_id(
        self, competitor_id: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch a competitor record by ID, restricted to one organization."""
        stmt = select(Competitor).where(
            Competitor.competitor_id == competitor_id,
            Competitor.organization_id == organization_id,
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        return self._to_dict(record) if record is not None else None

    async def get_by_company(
        self,
        research_id: str,
        organization_id: str,
        company_name: str,
        website: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Fetch a competitor using its normalized name within the owning scope."""
        identity_filters = [Competitor.company_key == _company_key(company_name)]
        if _website_key(website):
            identity_filters.append(
                Competitor.website_key == _website_key(website)
            )
        stmt = select(Competitor).where(
            Competitor.research_id == research_id,
            Competitor.organization_id == organization_id,
            or_(*identity_filters),
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        return self._to_dict(record) if record is not None else None

    async def update_profile(
        self,
        *,
        competitor_id: str,
        organization_id: str,
        research_id: str,
        company_name: str,
        website: Optional[str],
        competitor_type: str,
        company_description: Optional[str],
        profile: Dict[str, Any],
        qualification_score: float,
        confidence: float,
        verification_status: str,
        source_references: List[str],
    ) -> Dict[str, Any]:
        stmt = select(Competitor).where(
            Competitor.competitor_id == competitor_id,
            Competitor.organization_id == organization_id,
            Competitor.research_id == research_id,
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            raise ResearchError(
                "Competitor not found in the requested organization and research."
            )
        record.company_name = company_name
        record.company_key = _company_key(company_name)
        record.website = website
        record.website_key = _website_key(website)
        record.competitor_type = competitor_type
        record.company_description = company_description
        record.profile = profile
        record.qualification_score = qualification_score
        record.confidence = confidence
        record.verification_status = verification_status
        record.source_references = source_references
        await self._session.flush()
        await self._session.refresh(record)
        return self._to_dict(record)

    async def list_by_research(
        self, research_id: str, organization_id: str
    ) -> List[Dict[str, Any]]:
        """List competitors for a research run, restricted to one organization."""
        stmt = (
            select(Competitor)
            .where(
                Competitor.research_id == research_id,
                Competitor.organization_id == organization_id,
            )
            .order_by(Competitor.qualification_score.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_dict(record) for record in result.scalars().all()]

    async def list_by_organization(
        self, organization_id: str, *, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List competitors for one organization (newest first)."""
        stmt = (
            select(Competitor)
            .where(Competitor.organization_id == organization_id)
            .order_by(Competitor.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_dict(record) for record in result.scalars().all()]

    async def organization_has_competitor(
        self, competitor_id: str, organization_id: str
    ) -> bool:
        """True only when the organization owns the competitor record."""
        record = await self.get_by_id(competitor_id, organization_id)
        return record is not None

    @staticmethod
    def _to_dict(record: Competitor) -> Dict[str, Any]:
        return {
            "id": record.id,
            "competitor_id": record.competitor_id,
            "research_id": record.research_id,
            "organization_id": record.organization_id,
            "company_name": record.company_name,
            "website": record.website,
            "competitor_type": record.competitor_type,
            "company_description": record.company_description,
            "profile": record.profile,
            "qualification_score": record.qualification_score,
            "confidence": record.confidence,
            "verification_status": record.verification_status,
            "source_references": record.source_references or [],
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        }


class CompetitorEvidenceRepository:
    """Database-backed competitor evidence access with organization isolation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        evidence_id: str,
        competitor_id: str,
        organization_id: str,
        research_id: str,
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
            record = CompetitorEvidence(
                evidence_id=evidence_id,
                competitor_id=competitor_id,
                organization_id=organization_id,
                research_id=research_id,
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
                "Competitor evidence persistence failed evidence_id=%s error_type=%s",
                evidence_id,
                type(exc).__name__,
            )
            raise ResearchError(
                "Failed to persist competitor evidence.",
                details={"evidence_id": evidence_id},
            ) from exc

    async def get_by_id(
        self, evidence_id: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        stmt = select(CompetitorEvidence).where(
            CompetitorEvidence.evidence_id == evidence_id,
            CompetitorEvidence.organization_id == organization_id,
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        return self._to_dict(record) if record is not None else None

    async def list_by_competitor(
        self, competitor_id: str, organization_id: str
    ) -> List[Dict[str, Any]]:
        """List evidence claims for a competitor, restricted to one organization."""
        stmt = select(CompetitorEvidence).where(
            CompetitorEvidence.competitor_id == competitor_id,
            CompetitorEvidence.organization_id == organization_id,
        )
        result = await self._session.execute(stmt)
        return [self._to_dict(record) for record in result.scalars().all()]

    async def update_status(
        self,
        evidence_id: str,
        organization_id: str,
        *,
        verification_status: str,
        confidence: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        stmt = select(CompetitorEvidence).where(
            CompetitorEvidence.evidence_id == evidence_id,
            CompetitorEvidence.organization_id == organization_id,
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        record.verification_status = verification_status
        if confidence is not None:
            record.confidence = confidence
        await self._session.flush()
        await self._session.refresh(record)
        return self._to_dict(record)

    @staticmethod
    def _to_dict(record: CompetitorEvidence) -> Dict[str, Any]:
        return {
            "id": record.id,
            "evidence_id": record.evidence_id,
            "competitor_id": record.competitor_id,
            "organization_id": record.organization_id,
            "research_id": record.research_id,
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


__all__ = ["CompetitorRepository", "CompetitorEvidenceRepository"]
