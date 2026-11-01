"""Tests for the research service layer (services/research_service.py)."""

import asyncio

from app.schemas.research import ResearchRequest
from app.services.research_service import (
    run_research,
    get_research,
    list_research_ids,
    _research_store,
)


def test_store_starts_empty():
    _research_store.clear()
    assert list_research_ids() == []


async def _submit():
    return await run_research(
        ResearchRequest(
            company_name="Acme Corp",
            industry="AI Software",
            research_question="Pricing vs competitors?",
        )
    )


def test_run_research_returns_structured_result():
    _research_store.clear()
    result = asyncio.run(_submit())
    assert result.research_id.startswith("res-")
    assert result.status == "completed"
    assert result.company_name == "Acme Corp"
    assert result.industry == "AI Software"
    assert result.final_report is not None
    assert result.final_report["company"] == "Acme Corp"
    assert len(result.execution_metadata) == 8
    assert [m.node_name for m in result.execution_metadata] == [
        "initialize_research",
        "research_planner",
        "company_researcher",
        "competitor_discovery_mock",
        "evidence_validator_mock",
        "strategic_analyst_mock",
        "report_generator_mock",
        "finalize_research",
    ]
    assert result.errors == []


def test_get_research_returns_stored_result():
    _research_store.clear()
    result = asyncio.run(_submit())
    fetched = asyncio.run(get_research(result.research_id))
    assert fetched.research_id == result.research_id
    assert fetched.status == "completed"
    assert fetched.results is not None


def test_get_research_missing_raises_not_found():
    _research_store.clear()
    try:
        asyncio.run(get_research("does-not-exist"))
        assert False, "expected NotFoundError"
    except Exception as exc:
        from app.core.exceptions import NotFoundError

        assert isinstance(exc, NotFoundError)
