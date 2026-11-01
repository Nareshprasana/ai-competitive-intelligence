"""competitor_discovery node: real AI-powered Competitor Discovery Agent.

Replaces the deterministic mock competitor_discovery_mock. This node invokes the
CompetitorResearcherAgent which searches external sources, extracts candidate
competitors via an LLM (OpenRouter / DeepSeek), qualifies them with a
transparent scoring model, attaches evidence with provenance, and persists
results to PostgreSQL.

If the LLM or search provider is not configured, the node degrades gracefully
to a heuristic/fallback discovery (clearly marked as unverified) and never
fabricates citations.
"""

import hashlib
from urllib.parse import urlsplit

from app.agents.competitor_researcher import CompetitorResearcherAgent
from app.agents.base import AgentBudget
from app.core.config import get_settings
from app.core.database import db
from app.core.logging import get_logger
from app.graph.nodes.base import run_node
from app.graph.state import ResearchState
from app.tools.search.providers.mock import MockSearchProvider
from app.tools.search.providers.duckduckgo import DuckDuckGoProvider

logger = get_logger("app.graph.nodes.competitor_discovery")


def _build_search_provider():
    """Build the configured search provider.

    Defaults to the deterministic mock provider (no network, no credits) unless
    settings.search_provider is set to 'duckduckgo'.
    """
    settings = get_settings()
    if settings.search_provider.lower() == "duckduckgo":
        return DuckDuckGoProvider(
            base_url=settings.duckduckgo_base_url,
            max_results=settings.search_max_queries,
        )
    return MockSearchProvider()


async def _competitor_discovery(state: ResearchState) -> dict:
    """Run the Competitor Discovery Agent and merge results into state."""
    if not state.company_name:
        raise ValueError("company_name is required for competitor discovery.")

    organization_id = state.organization_id or get_settings().default_organization_id
    research_id = state.research_id
    settings = get_settings()

    # Reuse the company profile produced by the company_researcher node.
    company_profile = state.company_profile or {}

    search_provider = _build_search_provider()
    agent = CompetitorResearcherAgent(
        search_provider,
        budget=AgentBudget(
            max_search_queries=min(
                settings.competitor_max_search_queries, settings.search_max_queries
            ),
            max_pages_fetched=settings.search_max_pages,
            max_tokens_per_llm_call=settings.competitor_max_tokens,
        ),
        max_candidates=settings.competitor_max_candidates,
    )

    try:
        result = await agent.discover(
            company_name=state.company_name,
            industry=state.industry,
            research_question=state.research_question,
            research_id=research_id,
            organization_id=organization_id,
            company_profile=company_profile,
            prior_evidence=state.evidence,
            prior_search_results=state.search_results,
        )

        competitors = result.get("competitors", [])
        evidence = result.get("evidence", [])

        persistence_status = "skipped"
        if db.is_available:
            try:
                await _persist_competitor_discovery(
                    research_id=research_id,
                    organization_id=organization_id,
                    competitors=competitors,
                )
                persistence_status = "completed"
            except Exception as exc:  # noqa: BLE001 - log but don't fail graph
                logger.warning(
                    "Failed to persist competitor discovery %s: %s",
                    research_id,
                    exc,
                )
                persistence_status = "failed"

        details = result.get("_metadata_details", {})
        details["mock"] = False
        details["persistence_status"] = persistence_status

        return {
            "competitors": competitors,
            "evidence": evidence,
            "_metadata_details": details,
        }
    finally:
        await agent.close()


async def _persist_competitor_discovery(
    *,
    research_id: str,
    organization_id: str,
    competitors: list,
) -> None:
    """Persist competitor profiles and evidence claims to PostgreSQL."""
    from app.repositories.competitor import (
        CompetitorEvidenceRepository,
        CompetitorRepository,
    )

    async for session in db.get_session():
        competitor_repo = CompetitorRepository(session)
        evidence_repo = CompetitorEvidenceRepository(session)

        for comp in competitors:
            comp_id = comp.get("competitor_id", f"comp-{research_id}-000")

            # Derive a deterministic competitor_id if not already set.
            if not comp_id or comp_id == f"comp-{research_id}-000":
                comp_id = "comp-" + hashlib.sha256(
                    (research_id + comp.get("company_name", "")).encode()
                ).hexdigest()[:16]

            existing = await competitor_repo.get_by_company(
                research_id,
                organization_id,
                comp.get("company_name", ""),
                comp.get("website"),
            )
            if existing is None:
                await competitor_repo.create(
                    competitor_id=comp_id,
                    research_id=research_id,
                    organization_id=organization_id,
                    company_name=comp.get("company_name", ""),
                    website=comp.get("website"),
                    competitor_type=comp.get("competitor_type", "substitute"),
                    company_description=comp.get("company_description"),
                    profile=comp,
                    qualification_score=comp.get("qualification_score", 0.0),
                    confidence=comp.get("confidence", 0.5),
                    verification_status=comp.get(
                        "verification_status", "unverified"
                    ),
                    source_references=comp.get("source_references", []),
                )
            else:
                comp_id = existing["competitor_id"]
                await competitor_repo.update_profile(
                    competitor_id=comp_id,
                    organization_id=organization_id,
                    research_id=research_id,
                    company_name=comp.get("company_name", ""),
                    website=comp.get("website"),
                    competitor_type=comp.get("competitor_type", "substitute"),
                    company_description=comp.get("company_description"),
                    profile=comp,
                    qualification_score=comp.get("qualification_score", 0.0),
                    confidence=comp.get("confidence", 0.5),
                    verification_status=comp.get(
                        "verification_status", "unverified"
                    ),
                    source_references=comp.get("source_references", []),
                )

            # Persist evidence claims.
            for ev in comp.get("evidence", []):
                source_url = ev.get("source_url", "")
                source_domain = ev.get("source_domain") or (
                    urlsplit(source_url).hostname or ""
                )
                evidence_id = "cev-" + hashlib.sha256(
                    (
                        organization_id
                        + research_id
                        + comp_id
                        + source_url
                        + ev.get("claim", "")
                    ).encode()
                ).hexdigest()[:24]
                if await evidence_repo.get_by_id(evidence_id, organization_id):
                    continue
                await evidence_repo.create(
                    evidence_id=evidence_id,
                    competitor_id=comp_id,
                    organization_id=organization_id,
                    research_id=research_id,
                    claim=ev.get("claim", ""),
                    source_url=source_url,
                    source_title=ev.get("source_title"),
                    source_domain=source_domain,
                    published_at=ev.get("published_at"),
                    evidence_type=ev.get("evidence_type", "other"),
                    confidence=ev.get("confidence", 0.5),
                    verification_status=ev.get(
                        "verification_status", "unverified"
                    ),
                    raw_snippet=ev.get("raw_snippet"),
                )

        await session.commit()
        break


async def competitor_discovery(state: ResearchState) -> dict:
    """Run the real Competitor Discovery Agent node.

    Updates ``competitors`` and ``evidence`` state fields. Execution metadata
    and errors are handled by ``run_node``.
    """
    return await run_node(
        node_name="competitor_discovery",
        state=state,
        node_fn=_competitor_discovery,
        mock=False,
    )
