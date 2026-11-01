"""Tests for evidence collection and validation logic."""

from app.intelligence.evidence import (
    build_evidence_from_result,
    classify_evidence_type,
    detect_conflicts,
    score_confidence,
)
from app.schemas.evidence import Evidence, VerificationStatus
from app.tools.search.schemas import SearchResult


def _make_result(url, title, snippet=None, domain="example.com"):
    return SearchResult(
        url=url,
        title=title,
        snippet=snippet,
        source_domain=domain,
        query="test",
        provider="mock",
    )


def test_build_evidence_from_result():
    result = _make_result(
        "https://example.com/acme", "Acme Corp", "Acme is an AI company."
    )
    evidence = build_evidence_from_result(
        research_id="res-1",
        claim="Acme is an AI company.",
        result=result,
        confidence=0.7,
        verification_status=VerificationStatus.PARTIALLY_VERIFIED,
    )
    assert evidence.claim == "Acme is an AI company."
    assert evidence.source_url == "https://example.com/acme"
    assert evidence.source_domain == "example.com"
    assert evidence.confidence == 0.7
    assert evidence.verification_status == VerificationStatus.PARTIALLY_VERIFIED


def test_score_confidence():
    result = _make_result("https://example.gov/page", "Gov Page")
    score = score_confidence(base=0.5, result=result, multiple_sources_agree=True)
    assert 0.0 <= score <= 1.0
    assert score > 0.5  # trusted domain + multiple sources


def test_detect_conflicts():
    e1 = Evidence(
        evidence_id="ev-1",
        research_id="res-1",
        claim="claim A",
        source_url="https://a.com",
        source_domain="a.com",
        verification_status=VerificationStatus.VERIFIED,
        confidence=0.9,
    )
    e2 = Evidence(
        evidence_id="ev-2",
        research_id="res-1",
        claim="claim B",
        source_url="https://b.com",
        source_domain="b.com",
        verification_status=VerificationStatus.CONFLICTING,
        confidence=0.3,
    )
    conflicts = detect_conflicts([e1, e2])
    assert len(conflicts) == 1
    assert conflicts[0]["reason"] == "conflicting_verification_status"


def test_classify_evidence_type():
    assert classify_evidence_type("https://sec.gov/filing", "10-K", "") == "regulatory_filing"
    assert classify_evidence_type("https://ir.example.com", "Investors", "") == "investor_relations"
    assert classify_evidence_type("https://news.com", "Press Release", "") == "press_release"
    assert classify_evidence_type("https://example.com", "About", "") == "other"


__all__ = []
