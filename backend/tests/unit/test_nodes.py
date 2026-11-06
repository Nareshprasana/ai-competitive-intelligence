"""Tests for individual graph nodes (graph/nodes/).

Nodes return partial state dicts (the LangGraph update pattern). Each test
merges the update back into a base ResearchState to inspect results.
"""

import asyncio

from app.graph.nodes import (
    initialize_research,
    research_planner,
    evidence_validator,
    evidence_validator_mock,
    strategic_analyst,
    strategic_analyst_mock,
    report_generator_mock,
    finalize_research,
)
from app.graph.nodes.company_researcher_mock import company_researcher_mock
from app.graph.nodes.competitor_discovery_mock import competitor_discovery_mock
from app.graph.state import ResearchState


def _base_state(**overrides):
    data = dict(
        research_id="res-1",
        organization_id="org-dev",
        company_name="Acme Corp",
        industry="AI Software",
        research_question="Pricing vs competitors?",
    )
    data.update(overrides)
    return ResearchState(**data)


def _run(node_fn, state):
    result = asyncio.run(node_fn(state))
    if isinstance(result, dict):
        merged = {**state.model_dump(), **result}
        return ResearchState(**merged)
    return result


def test_initialize_research():
    state = _run(initialize_research, _base_state())
    assert state.research_id == "res-1"
    assert state.review_status == "started"
    md = state.execution_metadata[0]
    assert md["node_name"] == "initialize_research"
    assert md["status"] == "completed"
    assert state.errors == []


def test_research_planner():
    state = _run(research_planner, _base_state())
    assert state.research_plan is not None
    assert state.research_plan["company_name"] == "Acme Corp"
    assert len(state.research_plan["steps"]) == 8


def test_company_researcher_mock():
    state = _run(company_researcher_mock, _base_state())
    assert state.company_profile is not None
    assert state.company_profile["company_name"] == "Acme Corp"
    assert state.company_profile["mock"] is True


def test_competitor_discovery_mock():
    state = _run(competitor_discovery_mock, _base_state())
    assert len(state.competitors) == 3
    assert all(c["industry"] == "AI Software" for c in state.competitors)


def test_evidence_validator_mock():
    state = _run(evidence_validator_mock, _base_state())
    assert len(state.evidence) == 2
    assert state.validation_results is not None
    assert state.validation_results["status"] == "validated_mock"


def test_evidence_validator_real_node():
    base = _base_state()
    base.evidence = [
        {
            "evidence_id": "ev-real-1",
            "claim": "Acme is in AI Software",
            "source_url": "https://sec.gov/edgar/data/acme",
            "source_domain": "sec.gov",
            "raw_snippet": "Acme Corp develops AI Software.",
            "published_at": "2026-01-01T00:00:00Z",
        }
    ]
    state = _run(evidence_validator, base)
    assert len(state.evidence) == 1
    assert state.validation_results is not None
    assert state.validation_results["total_claims"] == 1
    assert state.validation_results["verified_count"] == 1
    assert state.evidence[0]["verification_status"] == "verified"


def test_strategic_analyst_mock():
    state = _base_state()
    # Pre-populate competitors as competitor_discovery_mock would have done.
    state.competitors = [
        {"competitor_id": "comp-1", "name": "Competitor A", "industry": state.industry}
    ]
    state = _run(strategic_analyst_mock, state)
    assert state.strategic_analysis is not None
    assert len(state.strategic_analysis["opportunities"]) >= 1
    assert len(state.strategic_analysis["threats"]) >= 1


def test_strategic_analyst_real_node():
    state = _base_state()
    state.company_profile = {
        "products": ["Acme AI Core", "Acme Vision"],
        "target_customers": ["Enterprise Analytics"],
        "geographical_presence": ["North America", "Europe"],
    }
    state.competitors = [
        {
            "competitor_id": "comp-beta",
            "company_name": "Beta Labs",
            "competitor_type": "direct",
            "products_and_services": ["Beta Platform"],
            "competitive_strengths": ["Enterprise sales"],
            "competitive_weaknesses": ["Legacy codebase"],
        }
    ]
    state.evidence = [
        {
            "evidence_id": "ev-1",
            "research_id": "res-1",
            "claim": "Acme Corp launched Acme AI Core in North America.",
            "source_url": "https://acme.com/launch",
            "source_domain": "acme.com",
            "confidence": 0.9,
            "verification_status": "verified",
        }
    ]
    state = _run(strategic_analyst, state)
    assert state.strategic_analysis is not None
    assert state.strategic_analysis["target_company"] == "Acme Corp"
    assert len(state.strategic_analysis["competitor_comparisons"]) == 1
    assert len(state.strategic_analysis["swot_analysis"]["strengths"]) >= 1
    assert len(state.strategic_analysis["strategic_recommendations"]) >= 1
    assert state.strategic_analysis["overall_confidence"] > 0.0


def test_report_generator_mock():
    state = _run(report_generator_mock, _base_state())
    assert state.final_report is not None
    assert state.final_report["company"] == "Acme Corp"
    assert state.final_report["mock"] is True


def test_finalize_research_success_no_errors():
    state = _run(finalize_research, _base_state())
    assert state.review_status == "reviewed"


def test_nodes_record_execution_metadata():
    state = _run(company_researcher_mock, _base_state())
    md = state.execution_metadata[0]
    assert md["status"] == "completed"
    assert md["mock"] is True
    assert "duration_ms" in md
    assert md["node_name"] == "company_researcher_mock"
