"""Tests for evidence schemas."""

from app.schemas.evidence import (
    Evidence,
    EvidenceCollection,
    VerificationStatus,
)


def test_evidence_creation():
    evidence = Evidence(
        evidence_id="ev-001",
        research_id="res-001",
        claim="Acme Corp is headquartered in San Francisco.",
        source_url="https://example.com/acme-corp",
        source_title="Acme Corp - Official Website",
        source_domain="example.com",
        evidence_type="official_website",
        confidence=0.8,
        verification_status=VerificationStatus.VERIFIED,
    )
    assert evidence.evidence_id == "ev-001"
    assert evidence.research_id == "res-001"
    assert evidence.confidence == 0.8
    assert evidence.verification_status == VerificationStatus.VERIFIED
    assert evidence.retrieved_at is not None


def test_evidence_confidence_clamped():
    evidence = Evidence(
        evidence_id="ev-001",
        research_id="res-001",
        claim="claim",
        source_url="https://example.com/page",
        source_domain="example.com",
        confidence=1.5,
    )
    assert evidence.confidence == 1.0

    evidence2 = Evidence(
        evidence_id="ev-002",
        research_id="res-001",
        claim="claim",
        source_url="https://example.com/page",
        source_domain="example.com",
        confidence=-0.5,
    )
    assert evidence2.confidence == 0.0


def test_evidence_rejects_bad_url():
    try:
        Evidence(
            evidence_id="ev-001",
            research_id="res-001",
            claim="claim",
            source_url="not-a-url",
            source_domain="example.com",
        )
        assert False, "expected validation error"
    except Exception:
        pass


def test_evidence_collection():
    collection = EvidenceCollection(research_id="res-001")
    e1 = Evidence(
        evidence_id="ev-001",
        research_id="res-001",
        claim="claim 1",
        source_url="https://example.com/1",
        source_domain="example.com",
        verification_status=VerificationStatus.VERIFIED,
    )
    e2 = Evidence(
        evidence_id="ev-002",
        research_id="res-001",
        claim="claim 2",
        source_url="https://example.com/2",
        source_domain="example.com",
        verification_status=VerificationStatus.UNVERIFIED,
    )
    collection.add(e1)
    collection.add(e2)
    assert len(collection.items) == 2
    assert len(collection.by_status(VerificationStatus.VERIFIED)) == 1
    assert len(collection.by_status(VerificationStatus.UNVERIFIED)) == 1
    assert len(collection.by_domain("example.com")) == 2


__all__ = []
