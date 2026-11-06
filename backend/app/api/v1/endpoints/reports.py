"""Report generation and export endpoints (Phase 2G).

Provides:
- GET  /api/v1/research/{research_id}/report          - Structured report JSON
- GET  /api/v1/research/{research_id}/report/pdf      - Publication-quality PDF download
- GET  /api/v1/research/{research_id}/report/markdown - Markdown export
- POST /api/v1/research/{research_id}/report          - Generate/refresh report
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from fastapi.responses import PlainTextResponse

from app.core.database import db
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.repositories.report import ReportRepository
from app.repositories.research import ResearchRepository
from app.security.auth import (
    OrganizationContext,
    Permission,
    require_permission,
)

logger = get_logger("app.api.v1.endpoints.reports")

router = APIRouter()


@router.get(
    "/{research_id}/report",
    summary="Get structured competitive intelligence report JSON",
    response_model=Dict[str, Any],
)
async def get_report_json_endpoint(
    context: OrganizationContext = Depends(
        require_permission(Permission.VIEW_STRATEGY_REPORTS)
    ),
    research_id: str = Path(..., min_length=1, description="Research run identifier"),
) -> Dict[str, Any]:
    """Retrieve structured JSON report for a research run with tenant isolation."""
    async for session in db.get_session():
        report_repo = ReportRepository(session)
        report_data = await report_repo.get_report_json(
            research_id=research_id,
            organization_id=context.organization_id,
        )
        if not report_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found for this research run.",
            )
        return report_data
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database session unavailable.")


@router.get(
    "/{research_id}/report/pdf",
    summary="Download publication-quality PDF report",
)
async def download_report_pdf_endpoint(
    context: OrganizationContext = Depends(
        require_permission(Permission.VIEW_STRATEGY_REPORTS)
    ),
    research_id: str = Path(..., min_length=1, description="Research run identifier"),
) -> Response:
    """Download the publication-ready PDF binary with safe content disposition headers."""
    async for session in db.get_session():
        report_repo = ReportRepository(session)
        pdf_bytes = await report_repo.get_report_pdf(
            research_id=research_id,
            organization_id=context.organization_id,
        )
        if not pdf_bytes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF report artifact not found for this research run.",
            )
        filename = f"report-{research_id}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/pdf",
                "X-Content-Type-Options": "nosniff",
            },
        )
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database session unavailable.")


@router.get(
    "/{research_id}/report/markdown",
    summary="Get report in standard Markdown format",
    response_class=PlainTextResponse,
)
async def get_report_markdown_endpoint(
    context: OrganizationContext = Depends(
        require_permission(Permission.VIEW_STRATEGY_REPORTS)
    ),
    research_id: str = Path(..., min_length=1, description="Research run identifier"),
) -> PlainTextResponse:
    """Retrieve the Markdown export of the report."""
    async for session in db.get_session():
        report_repo = ReportRepository(session)
        md_text = await report_repo.get_report_markdown(
            research_id=research_id,
            organization_id=context.organization_id,
        )
        if not md_text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Markdown report artifact not found for this research run.",
            )
        return PlainTextResponse(
            content=md_text,
            media_type="text/markdown; charset=utf-8",
        )
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database session unavailable.")


__all__ = ["router"]
