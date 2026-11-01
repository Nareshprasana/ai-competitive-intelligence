"""Research graph node implementations.

Each node is an async function ``(state: ResearchState) -> dict`` that returns
a partial state update. Node logic is kept strictly separate from graph
building (see ``graph/builder.py``).

The ``company_researcher`` node uses the real AI-powered Company Research
Agent. The ``company_researcher_mock`` node is retained for backward
compatibility and testing.
"""

from app.graph.nodes.company_researcher import company_researcher
from app.graph.nodes.company_researcher_mock import company_researcher_mock
from app.graph.nodes.initialize_research import initialize_research
from app.graph.nodes.research_planner import research_planner
from app.graph.nodes.competitor_discovery_mock import competitor_discovery_mock
from app.graph.nodes.evidence_validator_mock import evidence_validator_mock
from app.graph.nodes.strategic_analyst_mock import strategic_analyst_mock
from app.graph.nodes.report_generator_mock import report_generator_mock
from app.graph.nodes.finalize_research import finalize_research

__all__ = [
    "initialize_research",
    "research_planner",
    "company_researcher",
    "company_researcher_mock",
    "competitor_discovery_mock",
    "evidence_validator_mock",
    "strategic_analyst_mock",
    "report_generator_mock",
    "finalize_research",
]
