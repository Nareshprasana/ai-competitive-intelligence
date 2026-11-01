"""Tests for company profile schemas."""

from app.schemas.company import CompanyProfile, CompanySize


def test_company_profile_minimal():
    profile = CompanyProfile(company_name="Acme Corp")
    assert profile.company_name == "Acme Corp"
    assert profile.industry is None
    assert profile.description is None
    assert profile.products == []
    assert profile.source_references == []


def test_company_profile_full():
    profile = CompanyProfile(
        company_name="Acme Corp",
        industry="AI Software",
        description="Leading AI software company.",
        headquarters="San Francisco, CA",
        founders=["Jane Doe", "John Smith"],
        products=["Platform A", "Platform B"],
        business_model="SaaS subscription",
        target_customers=["Enterprise", "SMB"],
        website="https://acme.example.com",
    )
    assert profile.industry == "AI Software"
    assert profile.headquarters == "San Francisco, CA"
    assert len(profile.founders) == 2
    assert len(profile.products) == 2
    assert profile.business_model == "SaaS subscription"
    assert profile.target_customers == ["Enterprise", "SMB"]
    assert str(profile.website) == "https://acme.example.com"


def test_company_profile_rejects_bad_website():
    try:
        CompanyProfile(company_name="Acme", website="not-a-url")
        assert False, "expected validation error"
    except Exception:
        pass


def test_company_size():
    size = CompanySize(employees_min=10, employees_max=50, label="11-50")
    assert size.employees_min == 10
    assert size.employees_max == 50
    assert size.label == "11-50"


def test_company_size_max_gte_min():
    try:
        CompanySize(employees_min=50, employees_max=10)
        assert False, "expected validation error"
    except Exception:
        pass


__all__ = []
