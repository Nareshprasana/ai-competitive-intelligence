"""LangGraph StateGraph construction (separate from node logic).

Builds the linear research workflow:

    START -> initialize_research -> research_planner -> company_researcher_mock
    -> competitor_discovery_mock -> evidence_validator_mock -> strategic_analyst_mock
    -> report_generator_mock -> finalize_research -> END

Node logic lives in ``app.graph.nodes``; this module only wires the graph.
A compiled graph is exposed as ``graph`` for convenience, and ``build_graph()``
returns a fresh compiled graph (useful in tests).
"""

from langgraph.graph import StateGraph, START, END

from app.graph.state import ResearchState
from app.graph.nodes import (
    initialize_research,
    research_planner,
    company_researcher_mock,
    competitor_discovery_mock,
    evidence_validator_mock,
    strategic_analyst_mock,
    report_generator_mock,
    finalize_research,
)


# Ordered node names matching the required workflow.
NODE_ORDER = [
    "initialize_research",
    "research_planner",
    "company_researcher_mock",
    "competitor_discovery_mock",
    "evidence_validator_mock",
    "strategic_analyst_mock",
    "report_generator_mock",
    "finalize_research",
]

_NODES = {
    "initialize_research": initialize_research,
    "research_planner": research_planner,
    "company_researcher_mock": company_researcher_mock,
    "competitor_discovery_mock": competitor_discovery_mock,
    "evidence_validator_mock": evidence_validator_mock,
    "strategic_analyst_mock": strategic_analyst_mock,
    "report_generator_mock": report_generator_mock,
    "finalize_research": finalize_research,
}


def build_graph():
    """Build and compile the research StateGraph.

    The graph is linear, making execution order trivial to verify. It is
    structured so future phases can insert conditional routing (e.g. review
    gates) and parallel agents without changing node logic.
    """
    builder = StateGraph(ResearchState)

    for name in NODE_ORDER:
        builder.add_node(name, _NODES[name])

    # Linear chain.
    builder.add_edge(START, NODE_ORDER[0])
    for current, nxt in zip(NODE_ORDER, NODE_ORDER[1:]):
        builder.add_edge(current, nxt)
    builder.add_edge(NODE_ORDER[-1], END)

    return builder.compile()


# Compiled graph (created on first access, not at import time of other modules).
_graph = None


def get_graph():
    """Return a compiled graph, compiling lazily on first use."""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


graph = get_graph()

__all__ = ["build_graph", "get_graph", "graph", "NODE_ORDER"]
