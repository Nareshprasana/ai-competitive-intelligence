"""SQLAlchemy repository for persistent intelligence reports and artifact retrieval (Phase 2G).

Enforces server-side organization tenant isolation on all report lookups,
updates encrypted research results, and coordinates artifact retrieval.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ResearchError
from app.core.logging import get_logger
from app.models.research import Research
from app.services.artifact_storage import get_artifact_storage

logger = get_logger("app.repositories.report")


class ReportRepository:
    """Database and artifact access for competitive intelligence reports."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._storage = get_artifact_storage()

    async def save_report(
        self,
        *,
        research_id: str,
        organization_id: str,
        report_data: Dict[str, Any],
        pdf_bytes: Optional[bytes] = None,
        markdown_text: Optional[str] = None,
    ) -> bool:
        """Persist report JSON inside research record and store binary/text artifacts.

        Enforces tenant isolation by verifying organization ownership.
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
                    "Research record not found for report save research_id=%s org_id=%s",
                    research_id,
                    organization_id,
                )
                return False

            report_id = report_data.get("metadata", {}).get("report_id", f"rpt-{research_id}")

            artifact_refs: Dict[str, str] = {}
            if pdf_bytes:
                pdf_key = self._storage.save_bytes(
                    organization_id=organization_id,
                    artifact_name=f"{report_id}.pdf",
                    content=pdf_bytes,
                )
                artifact_refs["pdf"] = pdf_key

            if markdown_text:
                md_key = self._storage.save_text(
                    organization_id=organization_id,
                    artifact_name=f"{report_id}.md",
                    text=markdown_text,
                )
                artifact_refs["markdown"] = md_key

            if "metadata" in report_data:
                report_data["metadata"]["artifact_references"] = artifact_refs

            existing_results = dict(record.results or {})
            existing_results["final_report"] = report_data
            record.results = existing_results

            await self._session.flush()
            logger.info(
                "Persisted report report_id=%s research_id=%s org_id=%s",
                report_id,
                research_id,
                organization_id,
            )
            return True
        except Exception as exc:  # noqa: BLE001
            await self._session.rollback()
            logger.error(
                "Failed to save report research_id=%s error=%s",
                research_id,
                exc,
            )
            raise ResearchError(
                "Failed to save report.",
                details={"research_id": research_id},
            ) from exc

    async def get_report_json(
        self, research_id: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve structured report JSON, strictly isolated by organization_id."""
        stmt = select(Research).where(
            Research.research_id == research_id,
            Research.organization_id == organization_id,
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None or not record.results:
            return None
        return record.results.get("final_report")

    async def get_report_pdf(
        self, research_id: str, organization_id: str
    ) -> Optional[bytes]:
        """Retrieve binary PDF artifact, strictly verifying organization ownership."""
        report_data = await self.get_report_json(research_id, organization_id)
        if not report_data:
            return None
        report_id = report_data.get("metadata", {}).get("report_id", f"rpt-{research_id}")
        return self._storage.read_bytes(organization_id, f"{report_id}.pdf")

    async def get_report_markdown(
        self, research_id: str, organization_id: str
    ) -> Optional[str]:
        """Retrieve Markdown artifact, strictly verifying organization ownership."""
        report_data = await self.get_report_json(research_id, organization_id)
        if not report_data:
            return None
        report_id = report_data.get("metadata", {}).get("report_id", f"rpt-{research_id}")
        return self._storage.read_text(organization_id, f"{report_id}.md")


__all__ = ["ReportRepository"]
