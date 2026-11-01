"""LangGraph StateGraph construction (separate from node logic).

Builds the linear research workflow:

    START -> initialize_research -> research_planner -> company_researcher
    -> competitor_discovery -> evidence_validator_mock -> strategic_analyst_mock
    -> report_generator_mock -> finalize_research -> END

Node logic lives in ``app.graph.nodes``; this module only wires the graph.
A compiled graph is exposed as ``graph`` for convenience, and ``build_graph()``
returns a fresh compiled graph (useful in tests).
"""

from typing import Any, Optional

from langgraph.graph import StateGraph, START, END

from app.graph.state import ResearchState
from app.graph.nodes.initialize_research import initialize_research
from app.graph.nodes.research_planner import research_planner
from app.graph.nodes.company_researcher import company_researcher
from app.graph.nodes.competitor_discovery_node import competitor_discovery
from app.graph.nodes.evidence_validator_mock import evidence_validator_mock
from app.graph.nodes.strategic_analyst_mock import strategic_analyst_mock
from app.graph.nodes.report_generator_mock import report_generator_mock
from app.graph.nodes.finalize_research import finalize_research


# Ordered node names matching the required workflow.
NODE_ORDER = [
    "initialize_research",
    "research_planner",
    "company_researcher",
    "competitor_discovery",
    "evidence_validator_mock",
    "strategic_analyst_mock",
    "report_generator_mock",
    "finalize_research",
]

_NODES = {
    "initialize_research": initialize_research,
    "research_planner": research_planner,
    "company_researcher": company_researcher,
    "competitor_discovery": competitor_discovery,
    "evidence_validator_mock": evidence_validator_mock,
    "strategic_analyst_mock": strategic_analyst_mock,
    "report_generator_mock": report_generator_mock,
    "finalize_research": finalize_research,
}


def build_graph(checkpointer: Optional[Any] = None):
    """Build and compile the research StateGraph.

    The graph is linear, making execution order trivial to verify. It is
    structured so future phases can insert conditional routing (e.g. review
    gates) and parallel agents without changing node logic.

    Args:
        checkpointer: Optional LangGraph checkpointer (e.g. async PostgreSQL
            saver) for thread-based checkpointing and resume. When omitted, the
            graph runs without persistence.
    """
    builder = StateGraph(ResearchState)

    for name in NODE_ORDER:
        builder.add_node(name, _NODES[name])

    # Linear chain.
    builder.add_edge(START, NODE_ORDER[0])
    for current, nxt in zip(NODE_ORDER, NODE_ORDER[1:]):
        builder.add_edge(current, nxt)
    builder.add_edge(NODE_ORDER[-1], END)

    return builder.compile(checkpointer=checkpointer)


# Compiled graph (created on first access, not at import time of other modules).
_graph: Optional[Any] = None


def get_graph(checkpointer: Optional[Any] = None):
    """Return a compiled graph, compiling lazily on first use.

    When a checkpointer is provided, a fresh graph compiled with that
    checkpointer is returned (checkpointer-bound graphs are not cached across
    different checkpointer instances).
    """
    global _graph
    if checkpointer is None and _graph is not None:
        return _graph
    graph = build_graph(checkpointer=checkpointer)
    if checkpointer is None:
        _graph = graph
    return graph


graph = get_graph()

__all__ = ["build_graph", "get_graph", "graph", "NODE_ORDER"]
