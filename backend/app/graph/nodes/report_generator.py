"""report_generator node: real AI-powered Report Generation Agent (Phase 2G).

Replaces the deterministic mock report_generator_mock. This node invokes the
ReportGeneratorAgent which consumes validated research and Phase 2F strategic analysis,
generating:
- 14-section client-ready StrategicReport (Structured JSON)
- Professional GitHub-Flavored Markdown
- Publication-quality business intelligence PDF with page numbering and running headers

Artifacts are saved into organization-scoped, path-traversal protected storage,
and the structured report dictionary is persisted inside the encrypted research record.
"""

from typing import Any, Dict, Optional

from app.agents.report_generator import ReportGeneratorAgent
from app.core.config import get_settings
from app.core.database import db
from app.core.logging import get_logger
from app.graph.nodes.base import run_node
from app.graph.state import ResearchState
from app.repositories.report import ReportRepository

logger = get_logger("app.graph.nodes.report_generator")


async def _persist_report(
    *,
    research_id: str,
    organization_id: str,
    report_dict: Dict[str, Any],
    pdf_bytes: bytes,
    markdown_text: str,
) -> None:
    """Persist report JSON and binary/text artifacts with tenant isolation."""
    async for session in db.get_session():
        report_repo = ReportRepository(session)
        await report_repo.save_report(
            research_id=research_id,
            organization_id=organization_id,
            report_data=report_dict,
            pdf_bytes=pdf_bytes,
            markdown_text=markdown_text,
        )
        await session.commit()
        break


async def _report_generator(state: ResearchState) -> dict:
    """Run the Report Generator Agent and return state update."""
    if not state.company_name:
        raise ValueError("company_name is required to generate a report.")

    organization_id = state.organization_id or get_settings().default_organization_id
    research_id = state.research_id

    agent = ReportGeneratorAgent()
    report, markdown_text, pdf_bytes = await agent.generate_report(state)
    report_dict = report.model_dump(mode="json")

    # Persist report and artifacts to storage
    if research_id:
        try:
            await _persist_report(
                research_id=research_id,
                organization_id=organization_id,
                report_dict=report_dict,
                pdf_bytes=pdf_bytes,
                markdown_text=markdown_text,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Report persistence failed research_id=%s error=%s",
                research_id,
                exc,
            )

    return {
        "final_report": report_dict,
        "_metadata_details": {
            "report_id": report.metadata.report_id,
            "overall_confidence": report.metadata.overall_confidence,
            "formats": [f.value for f in report.metadata.formats],
            "pdf_size_bytes": len(pdf_bytes),
            "markdown_length": len(markdown_text),
        },
    }


async def report_generator(state: ResearchState) -> dict:
    """Execute real Report Generator Agent LangGraph node."""
    return await run_node(
        node_name="report_generator",
        state=state,
        node_fn=_report_generator,
        mock=False,
    )


__all__ = ["report_generator", "_report_generator", "_persist_report"]
