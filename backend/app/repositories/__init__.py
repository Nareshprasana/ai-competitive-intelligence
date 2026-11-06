"""Research data access repositories."""

from app.repositories.company import CompanyRepository
from app.repositories.evidence import EvidenceRepository
from app.repositories.research import ResearchRepository
from app.repositories.strategy import StrategyRepository

__all__ = [
    "CompanyRepository",
    "EvidenceRepository",
    "ResearchRepository",
    "StrategyRepository",
]
