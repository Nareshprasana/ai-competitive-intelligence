"""Tests for the typed ResearchState (graph/state.py)."""

from app.graph.state import ResearchState


def test_state_required_fields():
    state = ResearchState(
        research_id="res-1",
        company_name="Acme",
        industry="AI",
        research_question="What is the market?",
    )
    assert state.research_id == "res-1"
    assert state.company_name == "Acme"
    assert state.review_status == "pending"
    assert state.competitors == []
    assert state.errors == []


def test_state_rejects_extra_fields():
    try:
        ResearchState(
            research_id="res-1",
            company_name="Acme",
            industry="AI",
            research_question="q",
            not_a_field="nope",
        )
        assert False, "expected validation error for extra field"
    except Exception:
        pass


def test_state_add_node_metadata_and_error():
    state = ResearchState(
        research_id="res-1",
        company_name="Acme",
        industry="AI",
        research_question="q",
    )
    state.add_node_metadata(
        node_name="test_node",
        status="completed",
        started_at="t0",
        completed_at="t1",
        duration_ms=5.0,
    )
    assert len(state.execution_metadata) == 1
    assert state.execution_metadata[0]["node_name"] == "test_node"
    assert state.execution_metadata[0]["status"] == "completed"

    state.add_error(node_name="test_node", error="boom")
    assert len(state.errors) == 1
    assert state.errors[0]["error"] == "boom"
