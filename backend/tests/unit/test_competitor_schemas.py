"""Tests for competitor profile schemas."""

from app.schemas.competitor import (
    CompetitorProfile,
    CompetitorType,
    QualificationFactor,
)


def test_competitor_profile_minimal():
    profile = CompetitorProfile(
        competitor_id="comp-001",
        company_name="Acme Corp",
        competitor_type="direct",
    )
    assert profile.competitor_id == "comp-001"
    assert profile.company_name == "Acme Corp"
    assert profile.competitor_type == CompetitorType.DIRECT
    assert profile.products_and_services == []
    assert profile.target_customers == []
    assert profile.competitive_strengths == []
    assert profile.competitive_weaknesses == []
    assert profile.evidence == []
    assert profile.source_references == []
    assert profile.qualification_score == 0.0
    assert profile.confidence == 0.5
    assert profile.verification_status == "unverified"


def test_competitor_profile_full():
    profile = CompetitorProfile(
        competitor_id="comp-002",
        company_name="Globex",
        website="https://globex.example.com",
        competitor_type="indirect",
        company_description="Biotechnology company.",
        products_and_services=["Gene therapy", "Diagnostics"],
        target_customers=["Hospitals", "Research labs"],
        geographic_markets=["North America", "Europe"],
        competitive_strengths=["Strong IP portfolio"],
        competitive_weaknesses=["High pricing"],
        overlap_explanation="Serves similar healthcare customers.",
        qualification_score=0.75,
        qualification_factors={
            "customer_overlap": 0.8,
            "product_similarity": 0.6,
        },
        confidence=0.8,
        verification_status="partially_verified",
        judgment_notes="Likely indirect competitor based on customer overlap.",
        unknown_information=["pricing details"],
        source_references=["https://globex.example.com"],
    )
    assert profile.competitor_type == CompetitorType.INDIRECT
    assert str(profile.website) == "https://globex.example.com"
    assert len(profile.products_and_services) == 2
    assert profile.qualification_score == 0.75
    assert len(profile.qualification_factors) == 2
    assert profile.confidence == 0.8
    assert profile.verification_status == "partially_verified"


def test_competitor_profile_rejects_bad_type():
    try:
        CompetitorProfile(
            competitor_id="comp-003",
            company_name="BadCo",
            competitor_type="not_a_valid_type",
        )
        assert False, "expected validation error"
    except Exception:
        pass


def test_competitor_profile_rejects_bad_website():
    try:
        CompetitorProfile(
            competitor_id="comp-004",
            company_name="BadCo",
            website="not-a-url",
        )
        assert False, "expected validation error"
    except Exception:
        pass


def test_competitor_profile_rejects_out_of_range_scores():
    import pytest

    with pytest.raises(Exception):
        CompetitorProfile(
            competitor_id="comp-005",
            company_name="TestCo",
            competitor_type="direct",
            confidence=1.5,
        )

    with pytest.raises(Exception):
        CompetitorProfile(
            competitor_id="comp-006",
            company_name="TestCo2",
            competitor_type="direct",
            qualification_score=-0.5,
        )


def test_competitor_evidence_requires_a_valid_http_source():
    import pytest
    from app.schemas.competitor import CompetitorEvidenceItem

    with pytest.raises(Exception):
        CompetitorEvidenceItem(
            claim="Claim",
            source_url="javascript:alert(1)",
            source_domain="example.com",
        )


def test_competitor_collection():
    from app.schemas.competitor import CompetitorCollection

    collection = CompetitorCollection(research_id="res-001")
    p1 = CompetitorProfile(
        competitor_id="comp-001",
        company_name="Company A",
        competitor_type="direct",
        qualification_score=0.8,
    )
    p2 = CompetitorProfile(
        competitor_id="comp-002",
        company_name="Company B",
        competitor_type="indirect",
        qualification_score=0.5,
    )
    collection.add(p1)
    collection.add(p2)
    assert len(collection.items) == 2
    assert len(collection.by_type("direct")) == 1
    assert len(collection.by_type("indirect")) == 1
    sorted_by_score = collection.sorted_by_score()
    assert sorted_by_score[0].company_name == "Company A"
    assert sorted_by_score[1].company_name == "Company B"


__all__ = []
