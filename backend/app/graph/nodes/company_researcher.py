"""company_researcher node: real AI-powered Company Research Agent.

Replaces the deterministic mock company_researcher_mock. This node invokes the
CompanyResearcherAgent which searches external sources, extracts a structured
company profile via an LLM (OpenRouter / DeepSeek), attaches evidence with
provenance, and persists results to PostgreSQL.

If the LLM or search provider is not configured, the node degrades gracefully
to a search-snippet-based profile (clearly marked as unverified) and never
fabricates citations.
"""

from typing import Optional

from app.agents.company_researcher import CompanyResearcherAgent
from app.core.config import get_settings
from app.core.database import db
from app.core.logging import get_logger
from app.graph.nodes.base import run_node
from app.graph.state import ResearchState
from app.tools.search.providers.mock import MockSearchProvider
from app.tools.search.providers.duckduckgo import DuckDuckGoProvider

logger = get_logger("app.graph.nodes.company_researcher")


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


async def _company_researcher(state: ResearchState) -> dict:
    """Run the Company Research Agent and merge results into state."""
    if not state.company_name:
        raise ValueError("company_name is required for company research.")

    organization_id = state.organization_id or get_settings().default_organization_id
    research_id = state.research_id

    search_provider = _build_search_provider()
    agent = CompanyResearcherAgent(search_provider)

    try:
        result = await agent.research(
            company_name=state.company_name,
            industry=state.industry,
            research_question=state.research_question,
            research_id=research_id,
            organization_id=organization_id,
        )

        company_profile = result.get("company_profile")
        evidence = result.get("evidence", [])

        # Persist to PostgreSQL when configured.
        persistence_status = "skipped"
        if db.is_available:
            try:
                await _persist_company_research(
                    research_id=research_id,
                    organization_id=organization_id,
                    company_name=state.company_name,
                    industry=state.industry,
                    company_profile=company_profile,
                    evidence=evidence,
                )
                persistence_status = "completed"
            except Exception as exc:  # noqa: BLE001 - log but don't fail graph
                logger.warning(
                    "Company research persistence failed research_id=%s error_type=%s",
                    research_id,
                    type(exc).__name__,
                )

        details = result.get("_metadata_details", {})
        details["mock"] = False
        details["persistence_status"] = persistence_status

        return {
            "company_profile": company_profile,
            "evidence": evidence,
            "search_results": result.get("search_results", []),
            "_metadata_details": details,
        }
    finally:
        await agent.close()


async def _persist_company_research(
    *,
    research_id: str,
    organization_id: str,
    company_name: str,
    industry: str,
    company_profile: Optional[dict],
    evidence: list,
) -> None:
    """Persist company profile and evidence claims to PostgreSQL."""
    from app.repositories.company import CompanyRepository
    from app.repositories.evidence import EvidenceRepository

    async for session in db.get_session():
        company_repo = CompanyRepository(session)
        evidence_repo = EvidenceRepository(session)

        # Derive a deterministic company_id from the company name.
        company_id = "comp-" + __import__("hashlib").sha256(
            company_name.encode()
        ).hexdigest()[:16]

        # Create or update the company profile.
        existing = await company_repo.get_by_id(company_id, organization_id)
        if existing is None:
            await company_repo.create(
                company_id=company_id,
                organization_id=organization_id,
                company_name=company_name,
                industry=industry,
                profile=company_profile,
                website=(company_profile or {}).get("website"),
                source_references=(company_profile or {}).get("source_references", []),
            )
        else:
            await company_repo.update_profile(
                company_id=company_id,
                organization_id=organization_id,
                profile=company_profile,
                website=(company_profile or {}).get("website"),
                source_references=(company_profile or {}).get("source_references", []),
            )

        profile_row = await company_repo.get_by_id(company_id, organization_id)
        profile_db_id = profile_row["id"] if profile_row else None

        # Persist evidence claims.
        for ev in evidence:
            await evidence_repo.create(
                evidence_id=ev.get("evidence_id", f"ev-{research_id}-00000"),
                company_profile_id=profile_db_id or 0,
                organization_id=organization_id,
                claim=ev.get("claim", ""),
                source_url=ev.get("source_url", ""),
                source_title=ev.get("source_title"),
                source_domain=ev.get("source_domain", ""),
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


async def company_researcher(state: ResearchState) -> dict:
    """Run the real Company Research Agent node.

    Updates ``company_profile`` and ``evidence`` state fields. Execution
    metadata and errors are handled by ``run_node``.
    """
    return await run_node(
        node_name="company_researcher",
        state=state,
        node_fn=_company_researcher,
        mock=False,
    )
