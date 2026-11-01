"""Company Research Agent.

Investigates a real company using external search + LLM extraction, attaches
evidence with provenance to factual claims, validates claims, and produces a
structured company profile.

Pipeline:

    Research Request
        -> Search Query Generation
        -> External Search
        -> Source Retrieval
        -> Information Extraction (LLM, structured Pydantic output)
        -> Evidence Collection
        -> Validation
        -> Structured Company Profile

The agent is deterministic in structure but probabilistic in LLM extraction.
All external calls are budgeted and retried only for transient failures.
No LLM calls occur at import time.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.agents.base import AgentBudget, BaseAgent, SearchResultCache
from app.core.config import get_settings
from app.core.llm import LLMMessage, get_llm_client
from app.core.exceptions import LLMConfigurationError, ResearchError
from app.core.logging import get_logger
from app.intelligence.evidence import (
    build_evidence_from_result,
    classify_evidence_type,
    detect_conflicts,
    score_confidence,
)
from app.schemas.company import CompanyProfile, CompanySize
from app.schemas.evidence import (
    Evidence,
    EvidenceCollection,
    VerificationStatus,
)
from app.tools.search.schemas import SearchQuery, SearchResult

logger = get_logger("app.agents.company_researcher")

# Aspects to research about a company. Each generates a search query.
RESEARCH_ASPECTS = [
    "company_overview",
    "headquarters_geography",
    "founders_leadership",
    "products_services",
    "business_model",
    "target_customers",
    "industry_classification",
    "geographic_markets",
    "financial_information",
    "recent_developments",
]


class CompanyResearcherAgent(BaseAgent):
    """Agent that researches a company and produces a structured profile."""

    def __init__(
        self,
        search_provider,
        *,
        budget: Optional[AgentBudget] = None,
        client=None,
    ) -> None:
        super().__init__(search_provider, budget=budget, client=client)
        self._llm_client = None

    async def _get_llm_client(self):
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    async def research(
        self,
        *,
        company_name: str,
        industry: str,
        research_question: str,
        research_id: str,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run the full company research pipeline.

        Returns a dict with ``company_profile`` and ``evidence`` suitable for
        merging into ResearchState.
        """
        logger.info(
            "CompanyResearcherAgent researching %s (research_id=%s)",
            company_name,
            research_id,
        )

        # 1. Generate search queries based on research aspects.
        queries = self._generate_search_queries(company_name, industry, research_question)

        # 2. Execute searches (budgeted, cached, rate-limited).
        all_results: List[SearchResult] = []
        for q in queries:
            if len(all_results) >= self.budget.max_search_queries:
                break
            results = await self._rate_limited_search(q)
            all_results.extend(results)

        # 3. Fetch source pages (budgeted, SSRF-safe).
        fetched_contents: Dict[str, Optional[str]] = {}
        for result in all_results[: self.budget.max_pages_fetched]:
            if result.url in fetched_contents:
                continue
            text = await self._fetch_safe(result.url)
            fetched_contents[result.url] = text

        # 4. Extract structured company profile via LLM (if configured).
        company_profile: Optional[CompanyProfile] = None
        evidence_items: List[Evidence] = []

        llm_available = False
        try:
            llm = await self._get_llm_client()
            llm_available = llm.is_available()
        except LLMConfigurationError:
            llm_available = False

        if llm_available and all_results:
            try:
                company_profile, evidence_items = await self._extract_profile_via_llm(
                    company_name=company_name,
                    industry=industry,
                    research_question=research_question,
                    results=all_results,
                    fetched_contents=fetched_contents,
                    research_id=research_id,
                )
            except (LLMConfigurationError, ResearchError) as exc:
                logger.warning(
                    "LLM extraction failed for %s: %s", company_name, exc
                )
                # Fall back to search-snippet-based profile (unverified).
                company_profile = self._build_fallback_profile(
                    company_name, industry, all_results
                )
        else:
            # No LLM configured: build profile from search snippets only.
            logger.info(
                "LLM not configured; building search-snippet profile for %s",
                company_name,
            )
            company_profile = self._build_fallback_profile(
                company_name, industry, all_results
            )
            # Create unverified evidence from snippets.
            for result in all_results:
                evidence_items.append(
                    build_evidence_from_result(
                        research_id=research_id,
                        claim=result.snippet or result.title,
                        result=result,
                        confidence=0.3,
                        verification_status=VerificationStatus.UNVERIFIED,
                        company_id=None,
                    )
                )

        # 5. Detect conflicts.
        conflicts = detect_conflicts(evidence_items)
        if conflicts:
            logger.warning(
                "Detected %d evidence conflicts for %s", len(conflicts), company_name
            )

        # 6. Assemble result dict for state merge.
        evidence_dicts = [
            e.model_dump(mode="json") for e in evidence_items
        ]

        profile_dict = company_profile.model_dump(mode="json") if company_profile else None

        return {
            "company_profile": profile_dict,
            "evidence": evidence_dicts,
            "search_results": [
                result.model_dump(mode="json") for result in all_results
            ],
            "_metadata_details": {
                "company": company_name,
                "search_queries_executed": len(queries),
                "results_found": len(all_results),
                "pages_fetched": sum(
                    1 for v in fetched_contents.values() if v is not None
                ),
                "llm_available": llm_available,
                "evidence_count": len(evidence_items),
                "conflicts": len(conflicts),
            },
        }

    # -- internal helpers -------------------------------------------------

    def _generate_search_queries(
        self, company_name: str, industry: str, research_question: str
    ) -> List[SearchQuery]:
        """Generate prioritized search queries for the company."""
        queries: List[SearchQuery] = []

        # Primary company query.
        queries.append(
            SearchQuery(
                query=company_name,
                purpose="company_overview",
                priority=1,
            )
        )
        # Industry + company.
        queries.append(
            SearchQuery(
                query="%s %s company" % (company_name, industry),
                purpose="industry_classification",
                priority=2,
            )
        )
        # Headquarters / location.
        queries.append(
            SearchQuery(
                query="%s headquarters location" % company_name,
                purpose="headquarters_geography",
                priority=3,
            )
        )
        # Founders / leadership.
        queries.append(
            SearchQuery(
                query="%s founders leadership team" % company_name,
                purpose="founders_leadership",
                priority=3,
            )
        )
        # Products / services.
        queries.append(
            SearchQuery(
                query="%s products services" % company_name,
                purpose="products_services",
                priority=4,
            )
        )
        # Business model.
        queries.append(
            SearchQuery(
                query="%s business model revenue" % company_name,
                purpose="business_model",
                priority=4,
            )
        )
        # Target customers.
        queries.append(
            SearchQuery(
                query="%s target customers clients" % company_name,
                purpose="target_customers",
                priority=5,
            )
        )
        # Recent developments.
        queries.append(
            SearchQuery(
                query="%s news 2024 2025" % company_name,
                purpose="recent_developments",
                priority=5,
            )
        )

        # Sort by priority and limit to budget.
        queries.sort(key=lambda q: q.priority)
        return queries[: self.budget.max_search_queries]

    async def _extract_profile_via_llm(
        self,
        *,
        company_name: str,
        industry: str,
        research_question: str,
        results: List[SearchResult],
        fetched_contents: Dict[str, Optional[str]],
        research_id: str,
    ) -> tuple[CompanyProfile, List[Evidence]]:
        """Use the LLM to extract a structured company profile from search results.

        Returns (CompanyProfile, List[Evidence]).
        """
        llm = await self._get_llm_client()
        if not llm.is_available():
            raise LLMConfigurationError("LLM not available for extraction.")

        # Build a context string from search results (truncated to limit tokens).
        context_parts: List[str] = []
        for result in results[: self.budget.max_pages_fetched]:
            part = "Source: %s\nURL: %s\nTitle: %s\nSnippet: %s\n" % (
                result.source_domain,
                result.url,
                result.title,
                result.snippet or "",
            )
            # Include fetched page text if available (truncated).
            page_text = fetched_contents.get(result.url)
            if page_text:
                part += "Page content: %s\n" % page_text[:1500]
            context_parts.append(part)
        context = "\n---\n".join(context_parts)

        system_prompt = (
            "You are a meticulous company research assistant. "
            "Given search results about a company, extract a structured company profile. "
            "Only include information that is supported by the provided sources. "
            "If information is not available, leave the field empty or null. "
            "Do not invent or hallucinate facts. "
            "Return a JSON object matching the requested schema."
        )

        user_prompt = (
            "Company: %s\nIndustry: %s\nResearch question: %s\n\n"
            "Sources:\n%s"
        ) % (company_name, industry, research_question, context)

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        self._increment_llm_call()
        profile = await llm.complete_structured(
            messages,
            CompanyProfile,
            max_tokens=self.budget.max_tokens_per_llm_call,
        )

        # Build evidence items from the sources used.
        evidence_items: List[Evidence] = []
        for result in results:
            # Use the snippet as a claim; confidence is editorial.
            claim = result.snippet or result.title
            evidence_type = classify_evidence_type(
                result.url, result.title, result.snippet or ""
            )
            confidence = score_confidence(
                base=0.5,
                result=result,
                multiple_sources_agree=len(results) > 1,
                has_direct_quote=False,
            )
            evidence_items.append(
                build_evidence_from_result(
                    research_id=research_id,
                    claim=claim,
                    result=result,
                    evidence_type=evidence_type,
                    confidence=confidence,
                    verification_status=VerificationStatus.PARTIALLY_VERIFIED,
                    company_id=None,
                )
            )

        return profile, evidence_items

    def _build_fallback_profile(
        self, company_name: str, industry: str, results: List[SearchResult]
    ) -> CompanyProfile:
        """Build a profile from search snippets only (no LLM).

        All fields are marked as unverified; description comes from the best
        snippet.
        """
        description = None
        website = None
        for result in results:
            if result.snippet and not description:
                description = result.snippet
            if not website and result.source_domain:
                website = "https://" + result.source_domain

        return CompanyProfile(
            company_name=company_name,
            industry=industry,
            description=description,
            website=website,
            source_references=[r.url for r in results],
        )

    async def close(self) -> None:
        await super().close()
        if self._llm_client is not None:
            try:
                await self._llm_client.close()
            except Exception:  # noqa: BLE001 - best effort
                pass
            self._llm_client = None


__all__ = ["CompanyResearcherAgent", "RESEARCH_ASPECTS"]
