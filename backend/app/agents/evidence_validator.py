"""Evidence Validation Agent for ACIS.

Evaluates collected company and competitor intelligence:
1. Normalizes evidence (metadata cleaning, URL canonicalization, duplicate detection).
2. Assesses source credibility across 9 transparent tiers.
3. Evaluates evidence freshness by claim category (pricing, product specs, history, etc.).
4. Matches claims to evidence and identifies prompt injection / untrusted text.
5. Detects cross-source contradictions and preserves conflicting sides.
6. Computes explainable, deterministic confidence scores.
7. Produces structured, traceable validation results and a human review queue.
8. Supports optional LLM-assisted semantic interpretation with graceful deterministic fallback.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.agents.base import AgentBudget, BaseAgent
from app.core.config import get_settings
from app.core.exceptions import LLMConfigurationError
from app.core.llm import LLMMessage, get_llm_client
from app.core.logging import get_logger
from app.schemas.evidence import (
    ClaimEvidenceMatch,
    ClaimValidationResult,
    ContradictionRecord,
    Evidence,
    FreshnessAssessment,
    HumanReviewItem,
    SourceCredibilityAssessment,
    SourceCredibilityTier,
    ValidationSummary,
    VerificationStatus,
)

logger = get_logger("app.agents.evidence_validator")

# Tracking parameters stripped during URL canonicalization
_TRACKING_QUERY_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "gclid",
        "fbclid",
        "ref",
        "source",
        "campaign",
        "mc_cid",
        "mc_eid",
    }
)

# Prompt injection heuristics in untrusted text
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a|an|the)", re.IGNORECASE),
    re.compile(r"disregard\s+(the\s+)?(above|previous)", re.IGNORECASE),
    re.compile(r"drop\s+table\b", re.IGNORECASE),
    re.compile(r"delete\s+from\b", re.IGNORECASE),
    re.compile(r"override\s+(all\s+)?rules", re.IGNORECASE),
]

# Source domain classification mapping
_GOVERNMENT_DOMAINS = (
    ".gov",
    ".mil",
    "sec.gov",
    "gov.uk",
    "europa.eu",
    "fca.org.uk",
    "justice.gov",
)

_DOCUMENTATION_SUBDOMAINS = (
    "docs.",
    "developer.",
    "developers.",
    "api.",
    "spec.",
    "swagger.",
)

_REPUTABLE_NEWS_DOMAINS = (
    "reuters.com",
    "bloomberg.com",
    "wsj.com",
    "ft.com",
    "nytimes.com",
    "apnews.com",
    "bbc.com",
    "bbc.co.uk",
    "cnbc.com",
    "economist.com",
    "theguardian.com",
)

_RESEARCH_REPORT_DOMAINS = (
    ".edu",
    "statista.com",
    "gartner.com",
    "forrester.com",
    "idc.com",
    "mckinsey.com",
    "bain.com",
    "bcg.com",
    "arxiv.org",
    "nih.gov",
    "researchgate.net",
)

_INDUSTRY_PUBLICATION_DOMAINS = (
    "techcrunch.com",
    "venturebeat.com",
    "zdnet.com",
    "forbes.com",
    "wired.com",
    "arstechnica.com",
    "infoworld.com",
    "theverge.com",
    "cio.com",
)

_DIRECTORY_DOMAINS = (
    "crunchbase.com",
    "pitchbook.com",
    "linkedin.com",
    "zoominfo.com",
    "dealroom.co",
    "g2.com",
    "capterra.com",
    "trustradius.com",
)

_BLOG_DOMAINS = (
    "medium.com",
    "substack.com",
    "wordpress.com",
    "blogger.com",
    "hashnode.dev",
)

_SOCIAL_DOMAINS = (
    "twitter.com",
    "x.com",
    "reddit.com",
    "facebook.com",
    "quora.com",
    "youtube.com",
    "tiktok.com",
    "instagram.com",
)


def _canonicalize_url(url: str) -> str:
    """Normalize a URL by lowercasing domain and stripping tracking query params."""
    if not url:
        return ""
    try:
        parts = urlsplit(url.strip())
        scheme = parts.scheme.lower()
        netloc = parts.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        if (scheme == "https" and netloc.endswith(":443")) or (scheme == "http" and netloc.endswith(":80")):
            netloc = netloc.rsplit(":", 1)[0]
        path = parts.path.rstrip("/") if parts.path != "/" else "/"

        filtered_query = [
            (k, v)
            for k, v in parse_qsl(parts.query, keep_blank_values=False)
            if k.lower() not in _TRACKING_QUERY_PARAMS
        ]
        query = urlencode(filtered_query)
        return urlunsplit((scheme, netloc, path, query, ""))
    except Exception:
        return url.strip()


def _canonical_domain(url_or_domain: str) -> str:
    """Extract registered/canonical domain from URL or domain string."""
    if not url_or_domain:
        return ""
    if "://" in url_or_domain:
        host = urlsplit(url_or_domain).hostname or ""
    else:
        host = urlsplit("http://" + url_or_domain).hostname or url_or_domain
    host = host.lower().strip().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    return host


def _clean_snippet(text: Optional[str]) -> str:
    """Clean snippet text, strip HTML, normalize whitespace, and truncate safely."""
    if not text:
        return ""
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", text)
    # Strip zero-width & non-printable control characters
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u200b-\u200d\ufeff]", "", cleaned)
    # Normalize whitespace
    cleaned = " ".join(cleaned.split())
    # Bound to safe limit (500 chars)
    return cleaned[:500]


def _detect_prompt_injection(text: str) -> bool:
    """Return True if text contains suspicious prompt-injection instructions."""
    if not text:
        return False
    return any(p.search(text) for p in _INJECTION_PATTERNS)


def _detect_claim_category(claim: str) -> str:
    """Classify the claim into a freshness category."""
    text = claim.lower()
    if any(k in text for k in ("price", "pricing", "cost", "per month", "tier", "subscription", "plan", "fee", "$", "usd", "eur")):
        return "pricing"
    if any(k in text for k in ("feature", "spec", "api", "version", "integration", "platform", "supported", "sdk", "specs")):
        return "product_specs"
    if any(k in text for k in ("seed", "series a", "series b", "series c", "series d", "funding", "raised", "valuation", "investor")):
        return "funding"
    if any(k in text for k in ("founded", "founder", "headquarters", "established", "started", "origin", "hq")):
        return "company_history"
    if any(k in text for k in ("trend", "market share", "growth", "forecast", "projection", "cagr", "tam", "industry")):
        return "market_trends"
    return "general"


def _extract_numbers(text: str) -> List[str]:
    """Extract numeric tokens (including currency and percentages) from text."""
    return re.findall(r"\$?\b\d+(?:[\.,]\d+)?%?", text)


def _stem(word: str) -> str:
    """Lightweight suffix stripping for matching word variants."""
    w = word.lower()
    for suffix in ("ing", "ed", "es", "s", "tion", "tions", "ment", "ments", "ers", "er"):
        if w.endswith(suffix) and len(w) - len(suffix) >= 4:
            return w[:-len(suffix)]
    return w


def _tokens(text: str) -> Set[str]:
    """Extract lowercased, stemmed alphanumeric word tokens."""
    words = re.findall(r"\b[a-zA-Z0-9_]{3,}\b", text.lower())
    stop_words = {
        "the", "and", "for", "with", "that", "this", "from", "are", "was",
        "were", "has", "have", "had", "will", "would", "can", "could",
        "which", "who", "whom", "its", "their", "about", "into", "more",
    }
    return {_stem(w) for w in words if w not in stop_words}


class EvidenceValidatorAgent(BaseAgent):
    """Production Evidence Validation Agent."""

    def __init__(
        self,
        search_provider=None,
        *,
        budget: Optional[AgentBudget] = None,
        client=None,
    ) -> None:
        from app.tools.search.providers.mock import MockSearchProvider

        provider = search_provider if search_provider is not None else MockSearchProvider()
        super().__init__(provider, budget=budget, client=client)
        self._llm_client = None

    async def _get_llm_client(self):
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    # -------------------------------------------------------------------------
    # A. Evidence Normalization
    # -------------------------------------------------------------------------

    def normalize_evidence(
        self, items: List[Dict[str, Any] | Evidence]
    ) -> List[Dict[str, Any]]:
        """Normalize evidence items: clean URLs, sanitize snippets, standardize dates,
        and mark duplicate records while preserving complete original provenance.
        """
        normalized_list: List[Dict[str, Any]] = []
        seen_keys: Set[Tuple[str, str]] = set()

        for item in items:
            raw: Dict[str, Any] = item.model_dump() if isinstance(item, Evidence) else dict(item)

            claim = (raw.get("claim") or "").strip()
            source_url = raw.get("source_url") or ""
            canonical_url = _canonicalize_url(source_url)
            domain = raw.get("source_domain") or _canonical_domain(canonical_url)
            canonical_domain = _canonical_domain(domain or canonical_url)

            # Clean and sanitize snippet
            snippet = _clean_snippet(raw.get("raw_snippet"))

            # Normalize published_at
            published_at = raw.get("published_at")
            if isinstance(published_at, str) and published_at.strip():
                try:
                    published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    published_at = None
            if isinstance(published_at, datetime) and published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=timezone.utc)

            # Normalize retrieved_at
            retrieved_at = raw.get("retrieved_at")
            if isinstance(retrieved_at, str) and retrieved_at.strip():
                try:
                    retrieved_at = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    retrieved_at = datetime.now(timezone.utc)
            elif not isinstance(retrieved_at, datetime):
                retrieved_at = datetime.now(timezone.utc)
            if retrieved_at.tzinfo is None:
                retrieved_at = retrieved_at.replace(tzinfo=timezone.utc)

            # Duplicate detection key: normalized claim + canonical URL
            norm_key = (claim.lower(), canonical_url.lower())
            is_duplicate = norm_key in seen_keys
            if not is_duplicate and canonical_url:
                seen_keys.add(norm_key)

            normalized_item = {
                **raw,
                "claim": claim,
                "source_url": source_url,
                "canonical_url": canonical_url,
                "source_domain": domain,
                "canonical_domain": canonical_domain,
                "raw_snippet": snippet,
                "published_at": published_at,
                "retrieved_at": retrieved_at,
                "is_duplicate": is_duplicate,
                "original_evidence_id": raw.get("evidence_id"),
            }
            normalized_list.append(normalized_item)

        return normalized_list

    # -------------------------------------------------------------------------
    # B. Source Credibility Assessment
    # -------------------------------------------------------------------------

    def assess_source_credibility(
        self,
        *,
        source_url: str,
        source_domain: str,
        evidence_type: str = "other",
        company_domain: Optional[str] = None,
    ) -> SourceCredibilityAssessment:
        """Evaluate source credibility across 9 transparent tiers with explainable factors."""
        canonical_domain = _canonical_domain(source_domain or source_url)
        norm_url = source_url.lower()

        # 1. Regulatory filings and government publications
        if (
            canonical_domain.endswith(_GOVERNMENT_DOMAINS)
            or any(sub in norm_url for sub in ("sec.gov", "edgar", "filing", "10-k", "10-q"))
            or evidence_type == "regulatory_filing"
        ):
            return SourceCredibilityAssessment(
                source_domain=canonical_domain,
                source_url=source_url,
                tier=SourceCredibilityTier.REGULATORY_FILING,
                credibility_score=0.95,
                is_primary=True,
                explanation="Official government regulatory filing or statutory financial disclosure.",
            )

        # 2. Official product documentation
        if (
            any(canonical_domain.startswith(sub) for sub in _DOCUMENTATION_SUBDOMAINS)
            or "/docs/" in norm_url
            or "/developer/" in norm_url
            or "/api-docs" in norm_url
        ):
            return SourceCredibilityAssessment(
                source_domain=canonical_domain,
                source_url=source_url,
                tier=SourceCredibilityTier.OFFICIAL_DOCUMENTATION,
                credibility_score=0.88,
                is_primary=True,
                explanation="Official technical documentation or developer portal.",
            )

        # 3. Official company website
        if (
            (company_domain and canonical_domain == _canonical_domain(company_domain))
            or evidence_type == "official_website"
            or any(sub in norm_url for sub in ("/about", "/company", "/investors", "ir."))
        ):
            return SourceCredibilityAssessment(
                source_domain=canonical_domain,
                source_url=source_url,
                tier=SourceCredibilityTier.OFFICIAL_WEBSITE,
                credibility_score=0.90,
                is_primary=True,
                explanation="First-party company website or investor relations portal.",
            )

        # 4. Research reports & academic
        if canonical_domain.endswith(_RESEARCH_REPORT_DOMAINS):
            return SourceCredibilityAssessment(
                source_domain=canonical_domain,
                source_url=source_url,
                tier=SourceCredibilityTier.RESEARCH_REPORT,
                credibility_score=0.85,
                is_primary=False,
                explanation="Independent industry analyst, statistical research, or academic publication.",
            )

        # 5. Reputable news organizations
        if canonical_domain.endswith(_REPUTABLE_NEWS_DOMAINS):
            return SourceCredibilityAssessment(
                source_domain=canonical_domain,
                source_url=source_url,
                tier=SourceCredibilityTier.REPUTABLE_NEWS,
                credibility_score=0.82,
                is_primary=False,
                explanation="Established major news organization with institutional editorial standards.",
            )

        # 6. Reputable industry publications
        if canonical_domain.endswith(_INDUSTRY_PUBLICATION_DOMAINS):
            return SourceCredibilityAssessment(
                source_domain=canonical_domain,
                source_url=source_url,
                tier=SourceCredibilityTier.INDUSTRY_PUBLICATION,
                credibility_score=0.75,
                is_primary=False,
                explanation="Recognized technology or commercial industry trade publication.",
            )

        # 7. Third-party directories
        if canonical_domain.endswith(_DIRECTORY_DOMAINS):
            return SourceCredibilityAssessment(
                source_domain=canonical_domain,
                source_url=source_url,
                tier=SourceCredibilityTier.THIRD_PARTY_DIRECTORY,
                credibility_score=0.65,
                is_primary=False,
                explanation="Third-party commercial directory or software marketplace aggregation.",
            )

        # 8. Blogs and opinion articles
        if (
            canonical_domain.endswith(_BLOG_DOMAINS)
            or canonical_domain.startswith("blog.")
            or "/blog/" in norm_url
        ):
            return SourceCredibilityAssessment(
                source_domain=canonical_domain,
                source_url=source_url,
                tier=SourceCredibilityTier.BLOG_OPINION,
                credibility_score=0.40,
                is_primary=False,
                explanation="Individual blog, newsletter, or unvetted opinion commentary.",
            )

        # 9. Social media and unverified sources
        if canonical_domain.endswith(_SOCIAL_DOMAINS):
            return SourceCredibilityAssessment(
                source_domain=canonical_domain,
                source_url=source_url,
                tier=SourceCredibilityTier.UNVERIFIED_SOCIAL,
                credibility_score=0.25,
                is_primary=False,
                explanation="Unverified social media or public forum posting.",
            )

        # 10. General / Other
        return SourceCredibilityAssessment(
            source_domain=canonical_domain,
            source_url=source_url,
            tier=SourceCredibilityTier.OTHER,
            credibility_score=0.50,
            is_primary=False,
            explanation="General web publication with standard baseline credibility.",
        )

    # -------------------------------------------------------------------------
    # C. Freshness Assessment
    # -------------------------------------------------------------------------

    def assess_freshness(
        self,
        *,
        claim: str,
        published_at: Optional[datetime],
        retrieved_at: datetime,
    ) -> FreshnessAssessment:
        """Evaluate evidence freshness according to claim category thresholds."""
        category = _detect_claim_category(claim)

        if published_at is None:
            return FreshnessAssessment(
                category=category,
                published_at=None,
                retrieved_at=retrieved_at,
                age_days=None,
                is_stale=False,
                freshness_score=0.50,
                explanation="Publication date is missing; freshness cannot be proven without timestamp.",
            )

        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        if retrieved_at.tzinfo is None:
            retrieved_at = retrieved_at.replace(tzinfo=timezone.utc)

        age_days = max(0, (retrieved_at - published_at).days)

        # Category-specific freshness evaluation
        if category == "pricing":
            # Pricing changes quickly: 90 days warning, 180 days stale
            if age_days > 180:
                return FreshnessAssessment(
                    category=category,
                    published_at=published_at,
                    retrieved_at=retrieved_at,
                    age_days=age_days,
                    is_stale=True,
                    freshness_score=0.25,
                    explanation=f"Pricing evidence is {age_days} days old (>180 days threshold); marked stale.",
                )
            if age_days > 90:
                return FreshnessAssessment(
                    category=category,
                    published_at=published_at,
                    retrieved_at=retrieved_at,
                    age_days=age_days,
                    is_stale=False,
                    freshness_score=0.65,
                    explanation=f"Pricing evidence is {age_days} days old; within caution window (>90 days).",
                )
            return FreshnessAssessment(
                category=category,
                published_at=published_at,
                retrieved_at=retrieved_at,
                age_days=age_days,
                is_stale=False,
                freshness_score=0.95,
                explanation=f"Recent pricing evidence ({age_days} days old).",
            )

        if category == "product_specs":
            # Product features/APIs: 180 days warning, 365 days stale
            if age_days > 365:
                return FreshnessAssessment(
                    category=category,
                    published_at=published_at,
                    retrieved_at=retrieved_at,
                    age_days=age_days,
                    is_stale=True,
                    freshness_score=0.30,
                    explanation=f"Product specification evidence is {age_days} days old (>365 days threshold); marked stale.",
                )
            if age_days > 180:
                return FreshnessAssessment(
                    category=category,
                    published_at=published_at,
                    retrieved_at=retrieved_at,
                    age_days=age_days,
                    is_stale=False,
                    freshness_score=0.70,
                    explanation=f"Product specification evidence is {age_days} days old (>180 days caution window).",
                )
            return FreshnessAssessment(
                category=category,
                published_at=published_at,
                retrieved_at=retrieved_at,
                age_days=age_days,
                is_stale=False,
                freshness_score=0.95,
                explanation=f"Recent product specification evidence ({age_days} days old).",
            )

        if category in ("company_history", "funding"):
            # Historical events retain factual validity; age does not make founding date stale
            return FreshnessAssessment(
                category=category,
                published_at=published_at,
                retrieved_at=retrieved_at,
                age_days=age_days,
                is_stale=False,
                freshness_score=0.90,
                explanation=f"Historical/funding record dated {published_at.strftime('%Y-%m-%d')} retains validity.",
            )

        if category == "market_trends":
            if age_days > 730:
                return FreshnessAssessment(
                    category=category,
                    published_at=published_at,
                    retrieved_at=retrieved_at,
                    age_days=age_days,
                    is_stale=True,
                    freshness_score=0.30,
                    explanation=f"Market trend analysis is {age_days} days old (>2 years); marked stale.",
                )
            if age_days > 365:
                return FreshnessAssessment(
                    category=category,
                    published_at=published_at,
                    retrieved_at=retrieved_at,
                    age_days=age_days,
                    is_stale=False,
                    freshness_score=0.65,
                    explanation=f"Market trend analysis is {age_days} days old (>1 year caution window).",
                )
            return FreshnessAssessment(
                category=category,
                published_at=published_at,
                retrieved_at=retrieved_at,
                age_days=age_days,
                is_stale=False,
                freshness_score=0.95,
                explanation=f"Current market analysis ({age_days} days old).",
            )

        # General category fallback
        if age_days > 730:
            return FreshnessAssessment(
                category=category,
                published_at=published_at,
                retrieved_at=retrieved_at,
                age_days=age_days,
                is_stale=True,
                freshness_score=0.40,
                explanation=f"General evidence is {age_days} days old (>2 years); marked stale.",
            )
        freshness_score = max(0.50, round(1.0 - (age_days / 730.0) * 0.5, 2))
        return FreshnessAssessment(
            category=category,
            published_at=published_at,
            retrieved_at=retrieved_at,
            age_days=age_days,
            is_stale=False,
            freshness_score=freshness_score,
            explanation=f"Evidence is {age_days} days old.",
        )

    # -------------------------------------------------------------------------
    # D. Claim-to-Evidence Matching & Prompt Injection Defense
    # -------------------------------------------------------------------------

    def match_claim(
        self,
        *,
        claim: str,
        raw_snippet: Optional[str],
        evidence_id: str,
    ) -> ClaimEvidenceMatch:
        """Evaluate whether a snippet directly, partially, or insufficiently supports a claim,
        while strictly defending against prompt-injection attempts in snippet text.
        """
        snippet = _clean_snippet(raw_snippet)

        if not snippet:
            return ClaimEvidenceMatch(
                evidence_id=evidence_id,
                match_type="insufficient",
                relevance_score=0.20,
                explanation="No source snippet available to substantiate the claim.",
            )

        # Defensive check for prompt injection
        if _detect_prompt_injection(snippet):
            logger.warning(
                "Prompt injection pattern detected in evidence_id=%s; untrusted content ignored.",
                evidence_id,
            )
            return ClaimEvidenceMatch(
                evidence_id=evidence_id,
                match_type="unrelated",
                relevance_score=0.0,
                explanation="Snippet contains adversarial prompt-injection patterns; rejected as untrusted.",
            )

        claim_toks = _tokens(claim)
        snippet_toks = _tokens(snippet)

        if not claim_toks:
            return ClaimEvidenceMatch(
                evidence_id=evidence_id,
                match_type="insufficient",
                relevance_score=0.20,
                explanation="Claim has no substantive keyword tokens.",
            )

        overlap = len(claim_toks.intersection(snippet_toks))
        ratio = overlap / len(claim_toks)

        # Check for numeric alignment if claim mentions numbers (e.g. pricing, metrics)
        claim_nums = _extract_numbers(claim)
        snippet_nums = _extract_numbers(snippet)
        nums_contradicted = False
        if claim_nums and snippet_nums:
            # If claim specifies a number but snippet has a conflicting number in the same context
            if not set(claim_nums).intersection(set(snippet_nums)):
                nums_contradicted = True

        if nums_contradicted and ratio > 0.40:
            return ClaimEvidenceMatch(
                evidence_id=evidence_id,
                match_type="contradicts",
                relevance_score=0.85,
                explanation=(
                    f"Snippet numerical values {snippet_nums} conflict with "
                    f"claim numerical values {claim_nums}."
                ),
            )

        if ratio >= 0.60 or claim.lower() in snippet.lower():
            return ClaimEvidenceMatch(
                evidence_id=evidence_id,
                match_type="directly_supports",
                relevance_score=min(1.0, round(ratio + 0.2, 2)),
                explanation=f"Snippet directly confirms claim keywords ({int(ratio * 100)}% token overlap).",
            )

        if ratio >= 0.30:
            return ClaimEvidenceMatch(
                evidence_id=evidence_id,
                match_type="partially_supports",
                relevance_score=round(ratio, 2),
                explanation=f"Snippet partially mentions relevant concepts ({int(ratio * 100)}% token overlap).",
            )

        return ClaimEvidenceMatch(
            evidence_id=evidence_id,
            match_type="insufficient",
            relevance_score=round(ratio, 2),
            explanation=f"Snippet shows low overlap with claim ({int(ratio * 100)}% token overlap).",
        )

    # -------------------------------------------------------------------------
    # E. Contradiction Detection
    # -------------------------------------------------------------------------

    def detect_contradictions(
        self, normalized_evidence: List[Dict[str, Any]]
    ) -> List[ContradictionRecord]:
        """Detect cross-source contradictions (e.g. conflicting pricing, launch dates, specs)
        and record both sides with their source references.
        """
        contradictions: List[ContradictionRecord] = []
        n = len(normalized_evidence)

        for i in range(n):
            for j in range(i + 1, n):
                item_a, item_b = normalized_evidence[i], normalized_evidence[j]

                # Don't compare identical records
                if item_a.get("original_evidence_id") == item_b.get("original_evidence_id"):
                    continue

                claim_a = item_a.get("claim", "")
                claim_b = item_b.get("claim", "")
                domain_a = item_a.get("canonical_domain", "")
                domain_b = item_b.get("canonical_domain", "")

                cat_a = _detect_claim_category(claim_a)
                cat_b = _detect_claim_category(claim_b)

                # Look for conflicts within the same topical category
                if cat_a != cat_b or cat_a == "general":
                    continue

                toks_a = _tokens(claim_a)
                toks_b = _tokens(claim_b)
                if not toks_a or not toks_b:
                    continue

                # Must be discussing the same entity/topic (overlap in non-numeric keywords)
                common = toks_a.intersection(toks_b)
                if len(common) < 2:
                    continue

                # 1. Numeric conflict check (pricing, dates, headcount)
                nums_a = _extract_numbers(claim_a)
                nums_b = _extract_numbers(claim_b)

                if nums_a and nums_b and nums_a != nums_b:
                    cid = f"contra-{abs(hash(claim_a + claim_b)) % 1000000:06d}"
                    contradictions.append(
                        ContradictionRecord(
                            contradiction_id=cid,
                            topic=cat_a,
                            claim_a=claim_a,
                            evidence_id_a=str(item_a.get("original_evidence_id") or item_a.get("evidence_id")),
                            source_url_a=item_a.get("source_url", ""),
                            claim_b=claim_b,
                            evidence_id_b=str(item_b.get("original_evidence_id") or item_b.get("evidence_id")),
                            source_url_b=item_b.get("source_url", ""),
                            severity="high" if cat_a == "pricing" else "medium",
                            explanation=(
                                f"Discrepancy in {cat_a}: {domain_a} cites {nums_a} "
                                f"while {domain_b} cites {nums_b}."
                            ),
                            requires_human_review=True,
                        )
                    )
                    continue

                # 2. Polar / Negation conflict check (e.g., "supports X" vs "does not support X")
                has_negation_a = any(neg in claim_a.lower() for neg in ("not", "no ", "without", "lacks", "never"))
                has_negation_b = any(neg in claim_b.lower() for neg in ("not", "no ", "without", "lacks", "never"))

                if has_negation_a != has_negation_b and len(common) >= 3:
                    cid = f"contra-{abs(hash(claim_a + claim_b)) % 1000000:06d}"
                    contradictions.append(
                        ContradictionRecord(
                            contradiction_id=cid,
                            topic=cat_a,
                            claim_a=claim_a,
                            evidence_id_a=str(item_a.get("original_evidence_id") or item_a.get("evidence_id")),
                            source_url_a=item_a.get("source_url", ""),
                            claim_b=claim_b,
                            evidence_id_b=str(item_b.get("original_evidence_id") or item_b.get("evidence_id")),
                            source_url_b=item_b.get("source_url", ""),
                            severity="high",
                            explanation=(
                                f"Direct polar contradiction between {domain_a} and {domain_b} "
                                f"regarding {cat_a} capability/status."
                            ),
                            requires_human_review=True,
                        )
                    )

        return contradictions

    # -------------------------------------------------------------------------
    # F. Confidence Scoring
    # -------------------------------------------------------------------------

    def compute_confidence(
        self,
        *,
        credibility_score: float,
        freshness_score: float,
        relevance_score: float,
        independent_domains_count: int,
        contradiction_severity: Optional[str] = None,
        is_primary_source: bool = False,
    ) -> Tuple[float, str]:
        """Compute deterministic confidence score in [0.0, 1.0] with transparent breakdown."""
        # Weighted base components
        # Credibility: 40%, Freshness: 25%, Support/Relevance: 35%
        base = (
            0.40 * credibility_score
            + 0.25 * freshness_score
            + 0.35 * relevance_score
        )

        # Independent sources corroboration bonus
        if independent_domains_count >= 3:
            domain_bonus = 0.20
        elif independent_domains_count == 2:
            domain_bonus = 0.12
        elif is_primary_source:
            domain_bonus = 0.08
        else:
            domain_bonus = 0.0

        # Contradiction severity penalty
        if contradiction_severity == "high":
            contra_penalty = 0.40
        elif contradiction_severity == "medium":
            contra_penalty = 0.25
        elif contradiction_severity == "low":
            contra_penalty = 0.15
        else:
            contra_penalty = 0.0

        raw_score = base + domain_bonus - contra_penalty
        final_score = max(0.0, min(1.0, round(raw_score, 2)))

        breakdown = (
            f"Base: {base:.2f} (cred={credibility_score:.2f}, fresh={freshness_score:.2f}, "
            f"match={relevance_score:.2f}) + IndepDomainsBonus: +{domain_bonus:.2f} "
            f"- ContraPenalty: -{contra_penalty:.2f} = {final_score:.2f}"
        )
        return final_score, breakdown

    # -------------------------------------------------------------------------
    # G. Claim Validation Pipeline
    # -------------------------------------------------------------------------

    async def validate_state(
        self, state: Any, company_domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute full evidence validation across all evidence in state.

        Returns:
            - "evidence": updated evidence list with resolved verification statuses and confidence.
            - "validation_results": full ValidationSummary dictionary.
            - "_metadata_details": execution diagnostics.
        """
        raw_evidence = getattr(state, "evidence", []) or []
        research_id = getattr(state, "research_id", "unknown")

        # 1. Normalize all incoming evidence
        normalized_items = self.normalize_evidence(raw_evidence)

        # 2. Detect cross-source contradictions
        contradictions = self.detect_contradictions(normalized_items)
        contradicting_ev_ids: Dict[str, Tuple[str, List[str]]] = {}
        for c in contradictions:
            contradicting_ev_ids.setdefault(c.evidence_id_a, (c.severity, []))[1].append(c.evidence_id_b)
            contradicting_ev_ids.setdefault(c.evidence_id_b, (c.severity, []))[1].append(c.evidence_id_a)

        # 3. Evaluate each evidence claim
        claim_results: List[ClaimValidationResult] = []
        updated_evidence_list: List[Dict[str, Any]] = []
        human_review_queue: List[HumanReviewItem] = []

        # Count independent domains per claim topic for corroboration
        domains_by_claim: Dict[str, Set[str]] = {}
        for item in normalized_items:
            c = item["claim"].lower()
            dom = item["canonical_domain"]
            if dom:
                domains_by_claim.setdefault(c, set()).add(dom)

        for item in normalized_items:
            evidence_id = str(item.get("original_evidence_id") or item.get("evidence_id") or f"ev-{research_id}")
            claim = item.get("claim", "")
            source_url = item.get("source_url", "")
            source_domain = item.get("source_domain", "")
            raw_snippet = item.get("raw_snippet", "")
            published_at = item.get("published_at")
            retrieved_at = item.get("retrieved_at", datetime.now(timezone.utc))

            # Credibility
            cred_assessment = self.assess_source_credibility(
                source_url=source_url,
                source_domain=source_domain,
                evidence_type=item.get("evidence_type", "other"),
                company_domain=company_domain,
            )

            # Freshness
            fresh_assessment = self.assess_freshness(
                claim=claim,
                published_at=published_at,
                retrieved_at=retrieved_at,
            )

            # Match
            match = self.match_claim(
                claim=claim,
                raw_snippet=raw_snippet,
                evidence_id=evidence_id,
            )

            # Independent domains count for this specific claim
            indep_domains = domains_by_claim.get(claim.lower(), set())
            indep_count = len(indep_domains)

            # Check if this evidence was involved in a contradiction
            contra_info = contradicting_ev_ids.get(evidence_id)
            contra_severity = contra_info[0] if contra_info else None
            contra_targets = contra_info[1] if contra_info else []

            # Confidence
            conf_score, conf_breakdown = self.compute_confidence(
                credibility_score=cred_assessment.credibility_score,
                freshness_score=fresh_assessment.freshness_score,
                relevance_score=match.relevance_score,
                independent_domains_count=indep_count,
                contradiction_severity=contra_severity,
                is_primary_source=cred_assessment.is_primary,
            )

            # Determine final status
            missing_evidence: List[str] = []
            human_review_req = False
            review_reason: Optional[str] = None

            if contra_severity is not None or match.match_type == "contradicts":
                status = VerificationStatus.CONTRADICTED
                human_review_req = True
                review_reason = f"Cross-source contradiction flagged with evidence IDs {contra_targets}."
            elif fresh_assessment.is_stale:
                status = VerificationStatus.STALE
                missing_evidence.append(f"Current {fresh_assessment.category} confirmation required.")
            elif match.match_type == "insufficient":
                status = VerificationStatus.UNVERIFIED
                missing_evidence.append("Corroborating snippet or primary citation missing.")
            elif conf_score >= 0.75 and match.match_type == "directly_supports":
                status = VerificationStatus.VERIFIED
            elif conf_score >= 0.45:
                status = VerificationStatus.PARTIALLY_VERIFIED
                if indep_count < 2 and not cred_assessment.is_primary:
                    missing_evidence.append("Independent secondary source needed for full verification.")
            else:
                status = VerificationStatus.UNVERIFIED
                missing_evidence.append("Insufficient credibility or relevance.")

            # Flag ambiguous or low-confidence primary claims for human review
            if (
                status in (VerificationStatus.CONTRADICTED, VerificationStatus.STALE)
                or (status == VerificationStatus.PARTIALLY_VERIFIED and cred_assessment.tier == SourceCredibilityTier.BLOG_OPINION)
            ):
                human_review_req = True
                if not review_reason:
                    review_reason = f"Claim in state '{status}' requires analyst verification."

            val_result = ClaimValidationResult(
                claim_id=evidence_id,
                claim=claim,
                validation_status=status,
                confidence_score=conf_score,
                supporting_evidence_ids=[evidence_id] if match.match_type in ("directly_supports", "partially_supports") else [],
                contradicting_evidence_ids=contra_targets,
                source_credibility_assessments=[cred_assessment],
                freshness_assessment=fresh_assessment,
                validation_explanation=f"{match.explanation} | {conf_breakdown}",
                missing_evidence=missing_evidence,
                human_review_required=human_review_req,
                human_review_reason=review_reason,
                validated_at=datetime.now(timezone.utc),
            )
            claim_results.append(val_result)

            if human_review_req:
                human_review_queue.append(
                    HumanReviewItem(
                        claim_id=evidence_id,
                        claim_description=claim,
                        validation_status=status,
                        supporting_sources=[
                            {
                                "evidence_id": evidence_id,
                                "source_url": source_url,
                                "domain": source_domain,
                                "tier": cred_assessment.tier,
                            }
                        ],
                        contradicting_sources=[
                            {"evidence_id": tid} for tid in contra_targets
                        ],
                        reason_for_review=review_reason or "Flagged for editorial confirmation.",
                        missing_information=missing_evidence,
                        confidence_explanation=conf_breakdown,
                    )
                )

            # Updated evidence record
            updated_ev = {
                **item,
                "confidence": conf_score,
                "verification_status": status,
                "evidence_id": evidence_id,
            }
            # Remove internal fields before returning to state
            updated_ev.pop("is_duplicate", None)
            updated_ev.pop("canonical_url", None)
            updated_ev.pop("canonical_domain", None)
            updated_ev.pop("original_evidence_id", None)
            updated_evidence_list.append(updated_ev)

        # 4. Compute overall summary counts
        total_claims = len(claim_results)
        verified_count = sum(1 for r in claim_results if r.validation_status == VerificationStatus.VERIFIED)
        partially_count = sum(1 for r in claim_results if r.validation_status == VerificationStatus.PARTIALLY_VERIFIED)
        unverified_count = sum(1 for r in claim_results if r.validation_status == VerificationStatus.UNVERIFIED)
        contradicted_count = sum(1 for r in claim_results if r.validation_status == VerificationStatus.CONTRADICTED)
        stale_count = sum(1 for r in claim_results if r.validation_status == VerificationStatus.STALE)
        review_count = len(human_review_queue)

        avg_conf = (
            round(sum(r.confidence_score for r in claim_results) / total_claims, 2)
            if total_claims > 0
            else 0.0
        )

        overall_status = (
            "completed"
            if total_claims > 0 and contradicted_count == 0
            else "requires_review" if contradicted_count > 0 or review_count > 0
            else "insufficient_evidence"
        )

        summary = ValidationSummary(
            research_id=research_id,
            total_claims=total_claims,
            verified_count=verified_count,
            partially_verified_count=partially_count,
            unverified_count=unverified_count,
            contradicted_count=contradicted_count,
            stale_count=stale_count,
            requires_human_review_count=review_count,
            average_confidence=avg_conf,
            status=overall_status,
            claim_results=claim_results,
            contradictions=contradictions,
            human_review_queue=human_review_queue,
            validated_at=datetime.now(timezone.utc),
        )

        return {
            "evidence": updated_evidence_list,
            "validation_results": summary.model_dump(),
            "_metadata_details": {
                "total_claims": total_claims,
                "verified_count": verified_count,
                "contradicted_count": contradicted_count,
                "human_review_count": review_count,
                "average_confidence": avg_conf,
                "overall_status": overall_status,
            },
        }


__all__ = ["EvidenceValidatorAgent"]
