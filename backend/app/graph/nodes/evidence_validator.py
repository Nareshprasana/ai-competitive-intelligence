"""evidence_validator node: real AI-powered Evidence Validation Agent.

Replaces the deterministic mock evidence_validator_mock. This node invokes the
EvidenceValidatorAgent which normalizes collected evidence, evaluates source
credibility, assesses evidence freshness by category, detects cross-source
contradictions, scores confidence deterministically, and produces structured,
traceable validation results and a human review queue.

If the database is available, updated verification statuses, confidence scores,
full validation summary, and human review items are durably persisted to
storage with tenant isolation.
"""

from typing import Optional

from app.agents.evidence_validator import EvidenceValidatorAgent
from app.core.config import get_settings
from app.core.database import db
from app.core.logging import get_logger
from app.graph.nodes.base import run_node
from app.graph.state import ResearchState

logger = get_logger("app.graph.nodes.evidence_validator")


async def _persist_evidence_validation(
    *,
    research_id: str,
    organization_id: str,
    evidence: list,
    validation_results: dict,
) -> None:
    """Persist updated evidence verification statuses, confidence, and full validation results."""
    from app.repositories.competitor import CompetitorEvidenceRepository
    from app.repositories.evidence import EvidenceRepository
    from app.repositories.research import ResearchRepository

    async for session in db.get_session():
        evidence_repo = EvidenceRepository(session)
        competitor_evidence_repo = CompetitorEvidenceRepository(session)
        research_repo = ResearchRepository(session)

        for ev in evidence:
            ev_id = ev.get("evidence_id")
            status = ev.get("verification_status", "unverified")
            conf = ev.get("confidence", 0.5)
            if not ev_id:
                continue

            # Update company profile evidence claim if present
            updated = await evidence_repo.update_status(
                evidence_id=ev_id,
                organization_id=organization_id,
                verification_status=status,
                confidence=conf,
            )
            if not updated:
                # Update competitor evidence claim if present
                await competitor_evidence_repo.update_status(
                    evidence_id=ev_id,
                    organization_id=organization_id,
                    verification_status=status,
                    confidence=conf,
                )

        # Durably persist full validation summary and human review queue in research run
        research_row = await research_repo.get_by_id(research_id, organization_id)
        if research_row:
            existing_results = dict(research_row.get("results") or {})
            existing_results["validation_results"] = validation_results
            existing_results["evidence"] = evidence

            review_queue = validation_results.get("human_review_queue") or []
            contradictions = validation_results.get("contradictions") or []
            new_review_status = (
                "requires_review"
                if (len(review_queue) > 0 or len(contradictions) > 0)
                else (research_row.get("review_status") or "reviewed")
            )

            await research_repo.update_status(
                research_id=research_id,
                organization_id=organization_id,
                status=research_row["status"],
                review_status=new_review_status,
                results=existing_results,
            )

        await session.commit()
        break


async def _evidence_validator(state: ResearchState) -> dict:
    """Run the Evidence Validation Agent and merge validation results into state."""
    if not state.research_question:
        raise ValueError("research_question is required to validate evidence.")

    organization_id = state.organization_id or get_settings().default_organization_id
    research_id = state.research_id

    # Extract target company domain if available from company profile
    company_domain = None
    if state.company_profile:
        website = state.company_profile.get("website") or ""
        if website:
            company_domain = website

    agent = EvidenceValidatorAgent()

    try:
        result = await agent.validate_state(state, company_domain=company_domain)

        updated_evidence = result.get("evidence", [])
        validation_results = result.get("validation_results", {})

        persistence_status = "skipped"
        if db.is_available:
            try:
                await _persist_evidence_validation(
                    research_id=research_id,
                    organization_id=organization_id,
                    evidence=updated_evidence,
                    validation_results=validation_results,
                )
                persistence_status = "completed"
            except Exception as exc:  # noqa: BLE001 - log but don't fail graph
                logger.warning(
                    "Evidence validation persistence failed research_id=%s error_type=%s",
                    research_id,
                    type(exc).__name__,
                )
                persistence_status = "failed"

        details = result.get("_metadata_details", {})
        details["mock"] = False
        details["persistence_status"] = persistence_status

        return {
            "evidence": updated_evidence,
            "validation_results": validation_results,
            "_metadata_details": details,
        }
    finally:
        await agent.close()


async def evidence_validator(state: ResearchState) -> dict:
    """Run the real Evidence Validation Agent node.

    Updates ``evidence`` (with resolved statuses) and ``validation_results``
    (with full structured summary and human review queue).
    """
    return await run_node(
        node_name="evidence_validator",
        state=state,
        node_fn=_evidence_validator,
        mock=False,
    )


__all__ = ["evidence_validator"]
