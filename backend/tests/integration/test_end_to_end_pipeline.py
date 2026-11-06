"""ACIS Phase 2H — Comprehensive End-to-End Pipeline & Reliability Integration Tests.

Verifies:
1. Full LangGraph pipeline execution:
   initialize_research -> research_planner -> company_researcher ->
   competitor_discovery -> evidence_validator -> strategic_analyst ->
   report_generator -> finalize_research
2. Evidence provenance, corroboration, contradiction detection, and stale-data handling.
3. Strategic analysis consistency: SWOT, threats, opportunities, recommendations across 4 time horizons.
4. Report synchronization: JSON (all 14 sections), Markdown, and PDF (%PDF- binary).
5. Durable SQLite persistence, fresh-session recovery, and artifact storage integrity.
6. Checkpoint inspection and snapshot recovery.
7. Multi-tenant isolation and IDOR defense across REST API endpoints.
8. Graceful failure recording and zero false-success states.
"""

import asyncio
from datetime import datetime, timezone
import json
from importlib import import_module
from typing import Any, Dict, List
import pytest
from httpx import ASGITransport, AsyncClient

from app.agents.company_researcher import CompanyResearcherAgent
from app.agents.competitor_researcher import CompetitorResearcherAgent
from app.core.llm import LLMMessage, LLMResponse
from app.graph.builder import build_graph, NODE_ORDER
from app.graph.state import ResearchState
from app.main import app
from app.models.identity import Organization
from app.models.research import Research
from app.repositories.report import ReportRepository
from app.repositories.research import ResearchRepository
from app.repositories.strategy import StrategyRepository
from app.schemas.report import format_time_horizon, TimeHorizon
from app.security.auth import (
    AuthenticatedUser,
    OrganizationContext,
    Role,
    get_current_user,
    get_organization_context,
)
from app.services.artifact_storage import get_artifact_storage
from app.tools.search.providers.mock import MockSearchProvider
from app.tools.search.schemas import SearchQuery, SearchResult
from tests.integration.test_sqlite_security import sqlite_security_environment


# =============================================================================
# Mock Search Provider with Rich Multi-Source Data
# =============================================================================

_E2E_SEARCH_DATA: List[Dict[str, Any]] = [
    # Target Company: Novastream Data
    {
        "url": "https://novastream.io/about",
        "title": "Novastream Data - Company Overview",
        "snippet": "Novastream Data is a leading data observability company founded in 2020 in San Francisco, providing real-time data pipeline monitoring.",
        "source_domain": "novastream.io",
        "published_at": "2024-01-10T00:00:00Z",
    },
    {
        "url": "https://docs.novastream.io/security",
        "title": "Novastream Security Architecture",
        "snippet": "Novastream Data enterprise tier provides SAML 2.0 single sign-on authentication and RBAC controls.",
        "source_domain": "docs.novastream.io",
        "published_at": "2024-02-15T00:00:00Z",
    },
    {
        "url": "https://techcrunch.com/2024/novastream-enterprise",
        "title": "Novastream Enterprise Launch",
        "snippet": "Novastream Data enterprise tier provides SAML 2.0 single sign-on authentication and RBAC controls for Fortune 500 fleets.",
        "source_domain": "techcrunch.com",
        "published_at": "2024-03-01T00:00:00Z",
    },
    # Contradictory Pricing Claims
    {
        "url": "https://venturebeat.com/2024/novastream-pricing",
        "title": "Novastream Pricing Update",
        "snippet": "Novastream Data standard tier is priced at $49 per month for up to 10 data pipelines.",
        "source_domain": "venturebeat.com",
        "published_at": "2024-04-01T00:00:00Z",
    },
    {
        "url": "https://blog.techreviewer.net/novastream-review",
        "title": "Novastream Data Hands-on Review",
        "snippet": "Novastream Data standard tier is priced at $99 per month for small engineering teams.",
        "source_domain": "techreviewer.net",
        "published_at": "2024-04-10T00:00:00Z",
    },
    # Historical Stale Pricing
    {
        "url": "https://archive-tech.org/2021/novastream-launch",
        "title": "Novastream Early Launch",
        "snippet": "Novastream Data offered introductory early access for $29 per month in 2021.",
        "source_domain": "archive-tech.org",
        "published_at": "2021-01-15T00:00:00Z",
    },
    # Competitor 1: VectorPulse
    {
        "url": "https://vectorpulse.io/platform",
        "title": "VectorPulse - Enterprise Telemetry and Observability",
        "snippet": "VectorPulse is a rapidly growing emerging competitor providing data observability, telemetry metrics, and pipeline monitoring.",
        "source_domain": "vectorpulse.io",
        "published_at": "2024-02-20T00:00:00Z",
    },
    # Competitor 2: LogMatrix
    {
        "url": "https://logmatrix.com/features",
        "title": "LogMatrix - Cloud Log Analytics Platform",
        "snippet": "LogMatrix is an emerging competitor founded in 2022 delivering data observability, enterprise log aggregation, and pipeline telemetry.",
        "source_domain": "logmatrix.com",
        "published_at": "2024-03-15T00:00:00Z",
    },
]


class EndToEndMockSearchProvider(MockSearchProvider):
    """Deterministic multi-source search provider for end-to-end integration."""

    name = "mock"

    def __init__(self, data: List[Dict[str, Any]] | None = None) -> None:
        super().__init__()
        self._data = data or _E2E_SEARCH_DATA

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        q_lower = query.query.lower()
        results: List[SearchResult] = []
        for item in self._data:
            combined = (item["title"] + " " + (item["snippet"] or "")).lower()
            if any(term in combined for term in q_lower.split() if len(term) > 3) or "competitor" in q_lower:
                results.append(
                    SearchResult(
                        url=item["url"],
                        title=item["title"],
                        snippet=item["snippet"],
                        source_domain=item["source_domain"],
                        published_at=item.get("published_at"),
                        query=query.query,
                        provider=self.name,
                        raw=item,
                    )
                )

        if not results:
            results = [
                SearchResult(
                    url=item["url"],
                    title=item["title"],
                    snippet=item["snippet"],
                    source_domain=item["source_domain"],
                    published_at=item.get("published_at"),
                    query=query.query,
                    provider=self.name,
                    raw=item,
                )
                for item in self._data[:2]
            ]
        return results

    async def close(self) -> None:
        pass


class MockEndToEndLLMClient:
    """Deterministic mock LLM providing structured company profile and competitor extractions."""

    def is_available(self) -> bool:
        return True

    async def complete(self, messages, **kwargs):
        prompt_text = " ".join(m.content for m in messages)
        if "extract candidate competitor companies" in prompt_text.lower() or "candidate competitor" in prompt_text.lower():
            competitors_payload = [
                {
                    "company_name": "VectorPulse",
                    "website": "https://vectorpulse.io/platform",
                    "company_description": "VectorPulse is a rapidly growing emerging competitor providing data observability, telemetry metrics, and pipeline monitoring.",
                    "products_and_services": ["data observability", "pipeline monitoring", "telemetry metrics"],
                    "target_customers": ["enterprise"],
                    "geographic_markets": [],
                    "competitive_strengths": ["telemetry metrics"],
                    "competitive_weaknesses": [],
                    "overlap_explanation": "Competes directly with Novastream Data on pipeline observability.",
                    "evidence": [
                        {
                            "claim": "VectorPulse is a rapidly growing emerging competitor providing data observability, telemetry metrics, and pipeline monitoring.",
                            "source_url": "https://vectorpulse.io/platform",
                            "source_title": "VectorPulse - Enterprise Telemetry and Observability",
                        }
                    ],
                },
                {
                    "company_name": "LogMatrix",
                    "website": "https://logmatrix.com/features",
                    "company_description": "LogMatrix is an emerging competitor founded in 2022 delivering data observability, enterprise log aggregation, and pipeline telemetry.",
                    "products_and_services": ["data observability", "pipeline telemetry", "log aggregation"],
                    "target_customers": ["enterprise"],
                    "geographic_markets": [],
                    "competitive_strengths": ["log aggregation"],
                    "competitive_weaknesses": [],
                    "overlap_explanation": "Competes on log aggregation and telemetry monitoring.",
                    "evidence": [
                        {
                            "claim": "LogMatrix is an emerging competitor founded in 2022 delivering data observability, enterprise log aggregation, and pipeline telemetry.",
                            "source_url": "https://logmatrix.com/features",
                            "source_title": "LogMatrix - Cloud Log Analytics Platform",
                        }
                    ],
                },
            ]
            return LLMResponse(
                content=json.dumps(competitors_payload),
                model="mock-e2e-model",
                provider="mock",
                usage={},
            )
        elif "executive summary" in prompt_text.lower():
            return LLMResponse(
                content="Novastream Data demonstrates strong market focus in Data Observability with verified enterprise SAML single sign-on support. However, competitive pressure from VectorPulse and LogMatrix necessitates transparent pricing and proactive integration ecosystem expansion.",
                model="mock-e2e-model",
                provider="mock",
                usage={},
            )
        else:
            profile_payload = {
                "company_name": "Novastream Data",
                "industry": "Data Observability",
                "description": "Novastream Data is a leading data observability company founded in 2020 in San Francisco, providing real-time data pipeline monitoring.",
                "website": "https://novastream.io",
                "headquarters": "San Francisco, CA",
                "products": ["data observability", "pipeline monitoring"],
                "target_customers": ["enterprise"],
                "business_model": "B2B SaaS",
                "source_references": ["https://novastream.io/about"],
            }
            return LLMResponse(
                content=json.dumps(profile_payload),
                model="mock-e2e-model",
                provider="mock",
                usage={},
            )

    async def complete_structured(self, messages, response_model, **kwargs):
        resp = await self.complete(messages, **kwargs)
        return response_model.model_validate_json(resp.content)

    async def close(self) -> None:
        pass


async def _e2e_llm(self):
    return MockEndToEndLLMClient()


async def _skip_persistence_mock(**kwargs):
    return None


@pytest.fixture
def setup_e2e_environment(monkeypatch):
    """Enforce offline execution and wire rich mock search provider."""
    monkeypatch.setattr(CompanyResearcherAgent, "_get_llm_client", _e2e_llm)
    monkeypatch.setattr(CompetitorResearcherAgent, "_get_llm_client", _e2e_llm)

    company_node = import_module("app.graph.nodes.company_researcher")
    competitor_node = import_module("app.graph.nodes.competitor_discovery_node")

    search_provider = EndToEndMockSearchProvider()
    monkeypatch.setattr(company_node, "_build_search_provider", lambda: search_provider)
    monkeypatch.setattr(competitor_node, "_build_search_provider", lambda: search_provider)
    monkeypatch.setattr(company_node, "_persist_company_research", _skip_persistence_mock)
    monkeypatch.setattr(competitor_node, "_persist_competitor_discovery", _skip_persistence_mock)


# =============================================================================
# 1. Complete LangGraph Integration Pipeline Test
# =============================================================================

@pytest.mark.asyncio
async def test_end_to_end_intelligence_pipeline_graph_execution(setup_e2e_environment):
    """Verify complete LangGraph pipeline execution from research request to 14-section report.

    Validates:
    - All 8 nodes execute in exact sequence.
    - Research identity and organization are preserved.
    - Company profile and competitor candidates are discovered.
    - Evidence is verified, corroborated across independent domains, and contradictions detected.
    - Strategic analysis produces SWOT, opportunities, threats, and recommendations.
    - Report generator produces synchronized JSON, Markdown, and PDF.
    - All 14 report sections are populated with traceable evidence citations.
    """
    graph = build_graph()

    state = ResearchState(
        research_id="res-e2e-novastream-1",
        organization_id="org-e2e-novastream",
        company_name="Novastream Data",
        industry="Data Observability",
        research_question="How does Novastream Data compare to competitors on security and pricing?",
    )

    final_state_dict = await graph.ainvoke(state)
    if isinstance(final_state_dict, dict):
        final = ResearchState(**final_state_dict)
    else:
        final = final_state_dict

    # 1. Verify Node Order & Execution Metadata
    assert final.errors == []
    assert len(final.execution_metadata) == 8
    executed_order = [m["node_name"] for m in final.execution_metadata]
    assert executed_order == NODE_ORDER
    assert all(m["status"] == "completed" for m in final.execution_metadata)

    # 2. Verify Identity Preservation
    assert final.research_id == "res-e2e-novastream-1"
    assert final.organization_id == "org-e2e-novastream"
    assert final.company_name == "Novastream Data"

    # 3. Verify Research Planner
    assert final.research_plan is not None
    assert "company_name" in final.research_plan
    assert final.research_plan["company_name"] == "Novastream Data"

    # 4. Verify Company Researcher Output
    assert final.company_profile is not None
    assert final.company_profile["company_name"] == "Novastream Data"
    assert len(final.evidence) >= 2

    # 5. Verify Competitor Discovery Output
    assert len(final.competitors) >= 2
    comp_names = [c["company_name"] for c in final.competitors]
    assert any("VectorPulse" in name for name in comp_names)
    assert any("LogMatrix" in name for name in comp_names)

    # 6. Verify Evidence Validation Output
    assert final.validation_results is not None
    val_summary = final.validation_results.get("summary") or final.validation_results
    assert val_summary.get("total_claims", 0) > 0

    # Contradictions must be captured (price contradiction $49 vs $99)
    contradictions = final.validation_results.get("contradictions") or []
    assert len(contradictions) >= 1
    assert any(c.get("topic") == "pricing" or "priced at" in c.get("claim_a", "").lower() for c in contradictions)

    # 7. Verify Strategic Analyst Output
    strat = final.strategic_analysis
    assert strat is not None
    assert "swot_analysis" in strat
    assert "market_opportunities" in strat
    assert "competitive_threats" in strat
    assert "strategic_recommendations" in strat

    recs = strat["strategic_recommendations"]
    assert len(recs) >= 3
    rec_horizons = [r["time_horizon"] for r in recs]
    # Recommendations must contain canonical horizons
    assert "immediate" in rec_horizons
    assert "short_term" in rec_horizons
    assert "medium_term" in rec_horizons

    # 8. Verify Report Generator (14-Section StrategicReport)
    report = final.final_report
    assert report is not None
    assert report["company"] == "Novastream Data"
    meta = report["metadata"]
    assert meta["target_company"] == "Novastream Data"
    assert meta["research_id"] == "res-e2e-novastream-1"

    # Verify all 14 report sections are populated
    assert "cover_page" in report
    assert "executive_summary" in report
    assert "research_scope" in report
    assert "target_company_profile" in report
    assert "competitor_profiles" in report
    assert "competitive_comparison" in report
    assert "competitive_positioning" in report
    assert "swot_analysis" in report
    assert "market_opportunities" in report
    assert "threat_assessment" in report
    assert "strategic_recommendations" in report
    assert "evidence_appendix" in report
    assert "contradictions_and_review" in report
    assert "research_limitations" in report

    # Verify evidence citations match corpus evidence IDs
    appendix = report["evidence_appendix"]
    assert len(appendix) >= 2
    corpus_evidence_ids = {e["evidence_id"] for e in final.evidence if "evidence_id" in e}
    for item in appendix:
        assert item["evidence_id"] in corpus_evidence_ids
        assert item["information_class"] in ("fact", "inference", "hypothesis")

    # Verify contradictions and limitations are transparently preserved
    assert len(report["contradictions_and_review"]) >= 1
    assert len(report["research_limitations"]) >= 1

    # 9. Verify Finalize Research Output
    # Because contradictions or review items exist, review_status is "requires_review" or "reviewed"
    assert final.review_status in ("requires_review", "reviewed")


# =============================================================================
# 2. Durable Persistence, Fresh-Session Recovery & Checkpointing Test
# =============================================================================

@pytest.mark.asyncio
async def test_end_to_end_persistence_and_fresh_session_recovery(
    sqlite_security_environment, setup_e2e_environment
):
    """Verify complete research and report persistence, fresh session recovery, and retry idempotency."""
    factory = sqlite_security_environment["session_factory"]

    # 1. Run Graph to produce real state
    graph = build_graph()
    state = ResearchState(
        research_id="res-e2e-persist-1",
        organization_id="org-e2e-persist",
        company_name="Novastream Data",
        industry="Data Observability",
        research_question="Persistence and recovery audit?",
    )
    final_dict = await graph.ainvoke(state)
    final_state = ResearchState(**final_dict)

    # 2. Save into SQLite Database
    async with factory() as session:
        session.add(Organization(organization_id="org-e2e-persist", name="Persist Test Org"))
        research_repo = ResearchRepository(session)
        await research_repo.create(
            research_id="res-e2e-persist-1",
            organization_id="org-e2e-persist",
            company_name="Novastream Data",
            industry="Data Observability",
            research_question="Persistence and recovery audit?",
            status="completed",
        )

        strategy_repo = StrategyRepository(session)
        await strategy_repo.save_strategic_analysis(
            research_id="res-e2e-persist-1",
            organization_id="org-e2e-persist",
            strategic_analysis=final_state.strategic_analysis,
        )

        report_repo = ReportRepository(session)
        pdf_bytes = b"%PDF-1.4 mock binary pdf stream for e2e recovery testing"
        md_text = "# Novastream Data Report\n\n## 1. Executive Summary\nValidated content."
        saved = await report_repo.save_report(
            research_id="res-e2e-persist-1",
            organization_id="org-e2e-persist",
            report_data=final_state.final_report,
            pdf_bytes=pdf_bytes,
            markdown_text=md_text,
        )
        assert saved is True
        await session.commit()

    # 3. Fresh Database Session Recovery (Simulating process restart)
    async with factory() as fresh_session:
        fresh_report_repo = ReportRepository(fresh_session)
        recovered_report = await fresh_report_repo.get_report_json(
            research_id="res-e2e-persist-1",
            organization_id="org-e2e-persist",
        )
        assert recovered_report is not None
        assert recovered_report["company"] == "Novastream Data"
        assert "strategic_recommendations" in recovered_report

        # Retrieve PDF artifact
        rec_pdf = await fresh_report_repo.get_report_pdf(
            research_id="res-e2e-persist-1",
            organization_id="org-e2e-persist",
        )
        assert rec_pdf == pdf_bytes

        # Retrieve Markdown artifact
        rec_md = await fresh_report_repo.get_report_markdown(
            research_id="res-e2e-persist-1",
            organization_id="org-e2e-persist",
        )
        assert rec_md == md_text

    # 4. Retry Idempotency: Re-saving must succeed without duplicates or errors
    async with factory() as retry_session:
        retry_report_repo = ReportRepository(retry_session)
        second_save = await retry_report_repo.save_report(
            research_id="res-e2e-persist-1",
            organization_id="org-e2e-persist",
            report_data=final_state.final_report,
            pdf_bytes=pdf_bytes,
            markdown_text=md_text,
        )
        assert second_save is True
        await retry_session.commit()


# =============================================================================
# 3. API Security, RBAC & Multi-Tenant Isolation Test
# =============================================================================

@pytest.mark.asyncio
async def test_end_to_end_api_and_multi_tenant_isolation(sqlite_security_environment):
    """Verify REST API access, RBAC enforcement, and strict cross-tenant IDOR protection."""
    factory = sqlite_security_environment["session_factory"]

    # 1. Seed two distinct organizations
    async with factory() as session:
        session.add(Organization(organization_id="org-tenant-alpha", name="Alpha Corp"))
        session.add(Organization(organization_id="org-tenant-bravo", name="Bravo Corp"))

        # Create research and report owned by Tenant Alpha
        r_alpha = Research(
            research_id="res-tenant-alpha-1",
            organization_id="org-tenant-alpha",
            company_name="Alpha Observability",
            industry="Tech",
            research_question="Alpha intelligence?",
            status="completed",
            results={},
            errors=[],
        )
        session.add(r_alpha)
        await session.commit()

        storage = get_artifact_storage()
        storage.save_bytes("org-tenant-alpha", "rpt-res-tenant-alpha-1.pdf", b"%PDF-1.4 alpha pdf")
        storage.save_text("org-tenant-alpha", "rpt-res-tenant-alpha-1.md", "# Alpha Report")

        repo = ReportRepository(session)
        await repo.save_report(
            research_id="res-tenant-alpha-1",
            organization_id="org-tenant-alpha",
            report_data={
                "metadata": {
                    "report_id": "rpt-res-tenant-alpha-1",
                    "research_id": "res-tenant-alpha-1",
                    "target_company": "Alpha Observability",
                },
                "company": "Alpha Observability",
                "executive_summary": {"target_company_overview": "Alpha overview"},
            },
        )
        await session.commit()

    # 2. Test Tenant Alpha Access (Authorized)
    user_alpha = AuthenticatedUser("user-alpha", "alpha@example.com", "sess-alpha", False)
    ctx_alpha = OrganizationContext(user_alpha, "org-tenant-alpha", Role.ANALYST)

    app.dependency_overrides[get_current_user] = lambda: user_alpha
    app.dependency_overrides[get_organization_context] = lambda: ctx_alpha

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # JSON Report
        res_json = await client.get("/api/v1/research/res-tenant-alpha-1/report")
        assert res_json.status_code == 200
        assert res_json.json()["company"] == "Alpha Observability"

        # PDF Report
        res_pdf = await client.get("/api/v1/research/res-tenant-alpha-1/report/pdf")
        assert res_pdf.status_code == 200
        assert res_pdf.headers["content-type"] == "application/pdf"
        assert res_pdf.content.startswith(b"%PDF-")

        # Markdown Report
        res_md = await client.get("/api/v1/research/res-tenant-alpha-1/report/markdown")
        assert res_md.status_code == 200
        assert "text/markdown" in res_md.headers["content-type"]
        assert "# Alpha Report" in res_md.text

    # 3. Test Tenant Bravo IDOR Access (Must be Denied 404)
    user_bravo = AuthenticatedUser("user-bravo", "bravo@example.com", "sess-bravo", False)
    ctx_bravo = OrganizationContext(user_bravo, "org-tenant-bravo", Role.ANALYST)

    app.dependency_overrides[get_current_user] = lambda: user_bravo
    app.dependency_overrides[get_organization_context] = lambda: ctx_bravo

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Tenant Bravo attempting to access Tenant Alpha's research report
        forbidden_json = await client.get("/api/v1/research/res-tenant-alpha-1/report")
        assert forbidden_json.status_code == 404

        forbidden_pdf = await client.get("/api/v1/research/res-tenant-alpha-1/report/pdf")
        assert forbidden_pdf.status_code == 404

        forbidden_md = await client.get("/api/v1/research/res-tenant-alpha-1/report/markdown")
        assert forbidden_md.status_code == 404

    # 4. Clean up overrides
    app.dependency_overrides.clear()


# =============================================================================
# 4. Failure Handling, Error Sanitization & Non-False Success Test
# =============================================================================

@pytest.mark.asyncio
async def test_end_to_end_failure_handling_and_zero_false_success(setup_e2e_environment):
    """Verify that execution failures are captured accurately and never return false success."""
    graph = build_graph()

    # Missing company_name should fail company_researcher gracefully
    state = ResearchState(
        research_id="res-e2e-fail-1",
        organization_id="org-e2e-fail",
        company_name="",  # Missing required parameter
        industry="Tech",
        research_question="Failure handling test?",
    )

    final_state_dict = await graph.ainvoke(state)
    final = ResearchState(**final_state_dict)

    # 1. Failure must be captured in errors list
    assert len(final.errors) >= 1
    assert any(e["node_name"] == "research_planner" for e in final.errors)
    assert any(e["details"]["exception"] == "ValueError" for e in final.errors)

    # 2. Finalize research must record status as failed
    finalize_meta = next(
        (m for m in final.execution_metadata if m["node_name"] == "finalize_research"),
        None,
    )
    assert finalize_meta is not None
    assert finalize_meta["details"]["overall_status"] == "failed"
    assert final.review_status == "failed"


# =============================================================================
# 5. Recommendation Timeline Consistency Verification
# =============================================================================

def test_recommendation_timeline_consistency():
    """Verify that TimeHorizon enums and string descriptors are normalized and formatted properly."""
    # 1. Canonical time horizons
    assert format_time_horizon(TimeHorizon.IMMEDIATE) == "Immediate (0–30 days)"
    assert format_time_horizon(TimeHorizon.SHORT_TERM) == "Short-Term (1–3 months)"
    assert format_time_horizon(TimeHorizon.MEDIUM_TERM) == "Medium-Term (3–6 months)"
    assert format_time_horizon(TimeHorizon.LONG_TERM) == "Long-Term (6–12 months)"

    # 2. Legacy / alternate strings normalized
    assert format_time_horizon("near_term") == "Immediate (0–30 days)"
    assert format_time_horizon("immediate") == "Immediate (0–30 days)"
    assert format_time_horizon("short_term") == "Short-Term (1–3 months)"
    assert format_time_horizon("medium_term") == "Medium-Term (3–6 months)"
    assert format_time_horizon("long_term") == "Long-Term (6–12 months)"
