"""Tests for competitor qualification and deduplication logic."""

from app.intelligence.competitor import (
    SCORE_DIRECT,
    SCORE_EMERGING,
    SCORE_INDIRECT,
    classify_from_score,
    classify_from_factors,
    compute_text_overlap,
    deduplicate_competitors,
    score_qualification,
)
from app.schemas.competitor import (
    CompetitorProfile,
    QualificationFactor,
)


def test_score_qualification_all_factors():
    score, factors = score_qualification(
        product_similarity=1.0,
        service_similarity=1.0,
        customer_overlap=1.0,
        problem_space_overlap=1.0,
        geographic_overlap=1.0,
        business_model_similarity=1.0,
        market_positioning=1.0,
        factors_present=[],
    )
    assert score == 1.0
    assert len(factors) == 7


def test_score_qualification_no_factors():
    score, factors = score_qualification(
        product_similarity=0.0,
        service_similarity=0.0,
        customer_overlap=0.0,
        problem_space_overlap=0.0,
        geographic_overlap=0.0,
        business_model_similarity=0.0,
        market_positioning=0.0,
        factors_present=[],
    )
    assert score == 0.0
    assert len(factors) == 7
    assert all(value == 0.0 for value in factors.values())


def test_score_qualification_partial():
    score, factors = score_qualification(
        product_similarity=1.0,
        service_similarity=0.0,
        customer_overlap=1.0,
        problem_space_overlap=0.5,
        geographic_overlap=0.0,
        business_model_similarity=0.0,
        market_positioning=0.0,
        factors_present=[],
    )
    # 0.20 * 1.0 + 0.20 * 1.0 + 0.20 * 0.5 = 0.20 + 0.20 + 0.10 = 0.50
    assert abs(score - 0.50) < 0.001
    assert QualificationFactor.PRODUCT_SIMILARITY in factors
    assert QualificationFactor.CUSTOMER_OVERLAP in factors
    assert QualificationFactor.PROBLEM_SPACE_OVERLAP in factors


def test_classify_from_score_direct():
    assert classify_from_score(0.9) == "direct"
    assert classify_from_score(0.65) == "direct"


def test_classify_from_score_indirect():
    assert classify_from_score(0.5) == "indirect"
    assert classify_from_score(0.40) == "indirect"


def test_classify_from_score_emerging():
    assert classify_from_score(0.3) == "emerging"
    assert classify_from_score(0.25) == "emerging"


def test_classify_from_score_substitute():
    assert classify_from_score(0.1) is None
    assert classify_from_score(0.0) is None


def test_classifies_all_competitor_types_from_overlap_evidence():
    assert classify_from_factors(
        0.7,
        {
            "product_similarity": 0.8,
            "customer_overlap": 0.7,
            "problem_space_overlap": 0.7,
        },
    ) == "direct"
    assert classify_from_factors(
        0.45,
        {
            "product_similarity": 0.05,
            "problem_space_overlap": 0.6,
        },
    ) == "substitute"
    assert classify_from_factors(
        0.45,
        {
            "product_similarity": 0.25,
            "problem_space_overlap": 0.6,
        },
    ) == "indirect"
    assert classify_from_factors(
        0.3,
        {"problem_space_overlap": 0.2},
        emerging_signal=True,
    ) == "emerging"
    assert classify_from_factors(
        0.8,
        {
            "product_similarity": 0.8,
            "customer_overlap": 0.7,
            "problem_space_overlap": 0.7,
        },
        emerging_signal=True,
    ) == "emerging"
    assert classify_from_factors(0.0, {}) is None


def test_deduplicate_competitors_by_name():
    c1 = CompetitorProfile(
        competitor_id="comp-1",
        company_name="Acme Corp",
        competitor_type="direct",
    )
    c2 = CompetitorProfile(
        competitor_id="comp-2",
        company_name="acme corp",  # Same name, different case
        competitor_type="indirect",
    )
    c3 = CompetitorProfile(
        competitor_id="comp-3",
        company_name="Globex",
        competitor_type="direct",
    )
    deduped, count = deduplicate_competitors([c1, c2, c3])
    assert len(deduped) == 2
    assert count == 1
    assert deduped[0].company_name == "Acme Corp"
    assert deduped[1].company_name == "Globex"


def test_deduplicate_competitors_by_domain():
    c1 = CompetitorProfile(
        competitor_id="comp-1",
        company_name="Company A",
        website="https://example.com/page1",
        competitor_type="direct",
    )
    c2 = CompetitorProfile(
        competitor_id="comp-2",
        company_name="Company B",
        website="https://example.com/page2",  # Same domain
        competitor_type="indirect",
    )
    deduped, count = deduplicate_competitors([c1, c2])
    assert len(deduped) == 1
    assert count == 1


def test_compute_text_overlap():
    score = compute_text_overlap("AI software company", "AI software platform")
    assert 0.0 < score <= 1.0

    score = compute_text_overlap("biotech company", "restaurant chain")
    assert score == 0.0

    score = compute_text_overlap(None, "anything")
    assert score == 0.0


def test_compute_text_overlap_identical():
    score = compute_text_overlap("same text", "same text")
    assert score == 1.0


__all__ = []
