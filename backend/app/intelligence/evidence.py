"""Evidence collection and validation logic.

Provides helper functions for building Evidence records from search results and
LLM-extracted claims, scoring confidence, and detecting conflicts across
sources. All logic is deterministic; no LLM calls happen here.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.schemas.evidence import (
    Evidence,
    EvidenceCollection,
    EvidenceType,
    VerificationStatus,
)
from app.tools.search.schemas import SearchResult

_TRUSTED_DOMAIN_SUFFIXES = (
    ".gov",
    ".edu",
)


def _domain_of(url: str) -> str:
    """Extract the registered domain from a URL."""
    from urllib.parse import urlparse

    return (urlparse(url).hostname or "").lower()


def _is_trusted_domain(domain: str) -> bool:
    """Heuristic: government/academic domains are more trustworthy."""
    domain = domain.lower()
    return domain.endswith(_TRUSTED_DOMAIN_SUFFIXES)


def build_evidence_from_result(
    *,
    research_id: str,
    claim: str,
    result: SearchResult,
    evidence_type: str = EvidenceType.OTHER,
    confidence: float = 0.5,
    verification_status: str = VerificationStatus.UNVERIFIED,
    company_id: Optional[str] = None,
    raw_snippet: Optional[str] = None,
) -> Evidence:
    """Build an Evidence record from a search result and a claim.

    The source metadata is preserved verbatim; confidence is an editorial
    assessment, not statistical certainty.
    """
    return Evidence(
        evidence_id=f"ev-{research_id}-{abs(hash(claim + result.url)) % 100000:05d}",
        research_id=research_id,
        company_id=company_id,
        claim=claim,
        source_url=result.url,
        source_title=result.title,
        source_domain=result.source_domain,
        published_at=result.published_at,
        retrieved_at=datetime.now(timezone.utc),
        evidence_type=evidence_type,
        confidence=confidence,
        verification_status=verification_status,
        raw_snippet=raw_snippet or result.snippet,
    )


def score_confidence(
    *,
    base: float,
    result: SearchResult,
    multiple_sources_agree: bool = False,
    has_direct_quote: bool = False,
) -> float:
    """Score editorial confidence for a claim based on source quality.

    Returns a value in [0, 1]. Not statistical certainty.
    """
    score = base

    # Trusted domains boost confidence slightly.
    if _is_trusted_domain(result.source_domain):
        score += 0.1

    # Multiple independent sources agreeing boosts confidence.
    if multiple_sources_agree:
        score += 0.15

    # Direct quote from source boosts confidence.
    if has_direct_quote:
        score += 0.1

    return max(0.0, min(1.0, score))


def detect_conflicts(items: List[Evidence]) -> List[Dict[str, Any]]:
    """Detect potentially conflicting evidence items.

    Conflicts are flagged when two evidence items make claims about the same
    topic (same research_id, similar evidence_type) but with different
    verification_status or widely divergent confidence. This is a heuristic;
    final determination requires human or LLM review.
    """
    conflicts: List[Dict[str, Any]] = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]
            if a.evidence_type != b.evidence_type:
                continue
            if a.source_domain == b.source_domain:
                continue
            # Same type, different domains: check for contradictory statuses.
            statuses = {a.verification_status, b.verification_status}
            if VerificationStatus.CONFLICTING in statuses:
                conflicts.append(
                    {
                        "evidence_ids": [a.evidence_id, b.evidence_id],
                        "reason": "conflicting_verification_status",
                        "claims": [a.claim, b.claim],
                    }
                )
            elif abs(a.confidence - b.confidence) > 0.4:
                conflicts.append(
                    {
                        "evidence_ids": [a.evidence_id, b.evidence_id],
                        "reason": "large_confidence_divergence",
                        "claims": [a.claim, b.claim],
                    }
                )
    return conflicts


def classify_evidence_type(url: str, title: str = "", snippet: str = "") -> str:
    """Heuristically classify the evidence type from URL/title/snippet."""
    text = (url + " " + title + " " + snippet).lower()

    # Regulatory filings are checked first since "sec.gov" is a strong signal.
    if any(k in text for k in ("sec.gov", "filing", "10-k", "10-q", "8-k")):
        return EvidenceType.REGULATORY_FILING
    if any(k in text for k in ("investor", "ir.", "earnings")):
        return EvidenceType.INVESTOR_RELATIONS
    if any(k in text for k in ("press release", "newsroom", "pr newswire")):
        return EvidenceType.PRESS_RELEASE
    if any(k in text for k in (".gov", ".edu")):
        return EvidenceType.PUBLIC_DATABASE
    if any(k in text for k in ("reuters.com", "bloomberg.com", "wsj.com", "nytimes.com")):
        return EvidenceType.NEWS_ARTICLE
    return EvidenceType.OTHER


__all__ = [
    "build_evidence_from_result",
    "score_confidence",
    "detect_conflicts",
    "classify_evidence_type",
    "EvidenceCollection",
]
