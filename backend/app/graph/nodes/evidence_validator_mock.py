"""evidence_validator_mock node: deterministic mock evidence + validation."""

from app.graph.nodes.base import run_node
from app.graph.state import ResearchState


async def _evidence_validator(state: ResearchState) -> dict:
    evidence = [
        {
            "evidence_id": "ev-1",
            "claim": f"{state.company_name} operates in the {state.industry} market.",
            "source": "company_researcher_mock",
            "validated": True,
            "confidence": 0.9,
            "note": "Deterministic mock evidence; not independently verified.",
        },
        {
            "evidence_id": "ev-2",
            "claim": "Three direct competitors were identified.",
            "source": "competitor_discovery_mock",
            "validated": True,
            "confidence": 0.85,
            "note": "Deterministic mock evidence; not independently verified.",
        },
    ]
    validation_results = {
        "evidence_count": len(evidence),
        "validated_count": sum(1 for e in evidence if e["validated"]),
        "average_confidence": round(sum(e["confidence"] for e in evidence) / len(evidence), 2),
        "status": "validated_mock",
        "note": "Deterministic mock validation (Phase 1).",
    }
    return {
        "evidence": evidence,
        "validation_results": validation_results,
        "_metadata_details": {"evidence_count": len(evidence)},
    }


async def evidence_validator_mock(state: ResearchState) -> dict:
    """Return deterministic mock evidence and validation results (not real validation)."""
    if not state.research_question:
        raise ValueError("research_question is required to validate evidence.")
    return await run_node(
        node_name="evidence_validator_mock",
        state=state,
        node_fn=_evidence_validator,
        mock=True,
    )
