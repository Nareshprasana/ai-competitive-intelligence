"""Research data access repositories."""

from app.repositories.company import CompanyRepository
from app.repositories.evidence import EvidenceRepository
from app.repositories.research import ResearchRepository

__all__ = ["CompanyRepository", "EvidenceRepository", "ResearchRepository"]
