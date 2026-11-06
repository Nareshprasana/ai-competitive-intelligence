"""Research graph node implementations.

Each node is an async function ``(state: ResearchState) -> dict`` that returns
a partial state update. Node logic is kept strictly separate from graph
building (see ``graph/builder.py``).

The company, competitor discovery, and evidence validator nodes use their real agents.
Their mock variants remain available for focused tests and compatibility.
"""

from app.graph.nodes.company_researcher import company_researcher
from app.graph.nodes.company_researcher_mock import company_researcher_mock
from app.graph.nodes.competitor_discovery_node import competitor_discovery
from app.graph.nodes.competitor_discovery_mock import competitor_discovery_mock
from app.graph.nodes.evidence_validator import evidence_validator
from app.graph.nodes.evidence_validator_mock import evidence_validator_mock
from app.graph.nodes.finalize_research import finalize_research
from app.graph.nodes.initialize_research import initialize_research
from app.graph.nodes.report_generator import report_generator
from app.graph.nodes.report_generator_mock import report_generator_mock
from app.graph.nodes.research_planner import research_planner
from app.graph.nodes.strategic_analyst import strategic_analyst
from app.graph.nodes.strategic_analyst_mock import strategic_analyst_mock

__all__ = [
    "company_researcher",
    "company_researcher_mock",
    "competitor_discovery",
    "competitor_discovery_mock",
    "evidence_validator",
    "evidence_validator_mock",
    "finalize_research",
    "initialize_research",
    "report_generator",
    "report_generator_mock",
    "research_planner",
    "strategic_analyst",
    "strategic_analyst_mock",
]
