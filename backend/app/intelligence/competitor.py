"""Competitor qualification, deduplication, and overlap analysis.

All logic is deterministic; no LLM calls happen here. The qualification score is
a transparent weighted sum of evidence-backed factors, never an unexplained LLM
score.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.schemas.competitor import (
    CompetitorProfile,
    CompetitorType,
    QualificationFactor,
)

# Weights for the transparent qualification scoring model. Sum of all weights = 1.0.
# Each weight represents the importance of that factor in determining whether a
# company is a meaningful competitor to the researched company.
FACTOR_WEIGHTS: Dict[str, float] = {
    QualificationFactor.PRODUCT_SIMILARITY: 0.20,
    QualificationFactor.SERVICE_SIMILARITY: 0.15,
    QualificationFactor.CUSTOMER_OVERLAP: 0.20,
    QualificationFactor.PROBLEM_SPACE_OVERLAP: 0.20,
    QualificationFactor.GEOGRAPHIC_OVERLAP: 0.10,
    QualificationFactor.BUSINESS_MODEL_SIMILARITY: 0.10,
    QualificationFactor.MARKET_POSITIONING: 0.05,
}

# Thresholds for competitor classification based on qualification score.
SCORE_DIRECT = 0.65
SCORE_INDIRECT = 0.40
SCORE_EMERGING = 0.25


def _normalize_name(name: str) -> str:
    """Normalize a company name for deduplication comparison."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _domain_of(url: Optional[str]) -> Optional[str]:
    """Extract the registered domain from a URL."""
    if not url:
        return None
    from urllib.parse import urlparse

    return (urlparse(url).hostname or "").lower()


def deduplicate_competitors(
    competitors: List[CompetitorProfile],
) -> Tuple[List[CompetitorProfile], int]:
    """Remove duplicate competitors by normalized name and domain.

    Returns (deduplicated_list, duplicate_count).
    """
    seen_names: Set[str] = set()
    seen_domains: Set[str] = set()
    deduped: List[CompetitorProfile] = []
    duplicate_count = 0

    for comp in competitors:
        name_key = _normalize_name(comp.company_name)
        domain_key = _domain_of(comp.website)

        if name_key and name_key in seen_names:
            duplicate_count += 1
            continue
        if domain_key and domain_key in seen_domains:
            duplicate_count += 1
            continue

        seen_names.add(name_key)
        if domain_key:
            seen_domains.add(domain_key)
        deduped.append(comp)

    return deduped, duplicate_count


def score_qualification(
    *,
    product_similarity: float,
    service_similarity: float,
    customer_overlap: float,
    problem_space_overlap: float,
    geographic_overlap: float,
    business_model_similarity: float,
    market_positioning: float,
    factors_present: Optional[List[str]] = None,
) -> Tuple[float, Dict[str, float]]:
    """Compute a transparent qualification score from evidence-backed factors.

    Each factor is a value in [0, 1] representing the strength of evidence for
    that dimension. The final score is a weighted sum; every factor value is
    returned, while the profile separately records dimensions with unknown data.

    Returns the weighted score and all factor values.
    """
    score = 0.0
    contributing: Dict[str, float] = {}

    factor_values = {
        QualificationFactor.PRODUCT_SIMILARITY: product_similarity,
        QualificationFactor.SERVICE_SIMILARITY: service_similarity,
        QualificationFactor.CUSTOMER_OVERLAP: customer_overlap,
        QualificationFactor.PROBLEM_SPACE_OVERLAP: problem_space_overlap,
        QualificationFactor.GEOGRAPHIC_OVERLAP: geographic_overlap,
        QualificationFactor.BUSINESS_MODEL_SIMILARITY: business_model_similarity,
        QualificationFactor.MARKET_POSITIONING: market_positioning,
    }

    for factor, weight in FACTOR_WEIGHTS.items():
        value = factor_values.get(factor, 0.0)
        normalized_value = max(0.0, min(1.0, value))
        score += weight * normalized_value
        contributing[factor] = normalized_value

    return max(0.0, min(1.0, score)), contributing


def classify_from_score(score: float) -> Optional[str]:
    """Classify a competitor type from its qualification score.

    Thresholds are heuristic and should be reviewed against domain knowledge.
    """
    if score >= SCORE_DIRECT:
        return CompetitorType.DIRECT
    if score >= SCORE_INDIRECT:
        return CompetitorType.INDIRECT
    if score >= SCORE_EMERGING:
        return CompetitorType.EMERGING
    return None


def classify_from_factors(
    score: float,
    factors: Dict[str, float],
    *,
    emerging_signal: bool = False,
) -> Optional[str]:
    """Classify only when observed evidence shows meaningful market overlap."""
    product = factors.get(QualificationFactor.PRODUCT_SIMILARITY, 0.0)
    service = factors.get(QualificationFactor.SERVICE_SIMILARITY, 0.0)
    customers = factors.get(QualificationFactor.CUSTOMER_OVERLAP, 0.0)
    problem = factors.get(QualificationFactor.PROBLEM_SPACE_OVERLAP, 0.0)

    if emerging_signal and score >= SCORE_EMERGING and problem >= 0.05:
        return CompetitorType.EMERGING
    if (
        score >= SCORE_DIRECT
        and product >= 0.15
        and customers >= 0.10
        and problem >= 0.10
    ):
        return CompetitorType.DIRECT
    if score >= SCORE_INDIRECT and problem >= 0.10:
        if product < 0.15 and service < 0.15:
            return CompetitorType.SUBSTITUTE
        return CompetitorType.INDIRECT
    return None


def extract_keywords(text: Optional[str]) -> Set[str]:
    """Extract lowercase keywords from text for overlap comparison."""
    if not text:
        return set()
    # Simple tokenization: split on non-alphanumeric, filter short tokens.
    tokens = re.findall(r"[a-z0-9]{3,}", text.lower())
    return set(tokens)


def compute_text_overlap(
    text_a: Optional[str], text_b: Optional[str]
) -> float:
    """Compute Jaccard-style keyword overlap between two texts in [0, 1]."""
    set_a = extract_keywords(text_a)
    set_b = extract_keywords(text_b)
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def build_competitor_evidence(
    *,
    research_id: str,
    claim: str,
    source_url: str,
    source_title: Optional[str] = None,
    source_domain: str = "",
    evidence_type: str = "other",
    confidence: float = 0.5,
    verification_status: str = "unverified",
    raw_snippet: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a competitor evidence item dict for state persistence."""
    return {
        "claim": claim,
        "source_url": source_url,
        "source_title": source_title,
        "source_domain": source_domain,
        "evidence_type": evidence_type,
        "confidence": max(0.0, min(1.0, confidence)),
        "verification_status": verification_status,
        "raw_snippet": raw_snippet,
    }


__all__ = [
    "FACTOR_WEIGHTS",
    "SCORE_DIRECT",
    "SCORE_INDIRECT",
    "SCORE_EMERGING",
    "deduplicate_competitors",
    "score_qualification",
    "classify_from_score",
    "classify_from_factors",
    "compute_text_overlap",
    "build_competitor_evidence",
    "extract_keywords",
]
