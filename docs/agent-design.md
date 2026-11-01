# Agent Design — ACIS LangGraph Multi-Agent System (Phase 1)

## Design principles

- **Genuine multi-agent system**, not a basic chatbot: a LangGraph `StateGraph` with specialized nodes that pass a typed `ResearchState` between them.
- **Deterministic mocks in Phase 1**: no agent performs real research, calls an LLM, or consumes external credits. Every node returns structured placeholder data clearly marked `mock: true`. This is explicit and intentional — the graph is real, the data is not.
- **Separation of concerns**: node logic (`graph/nodes/`) is independent of graph wiring (`graph/builder.py`).
- **Observable execution**: every node records metadata; failures are captured, not swallowed.

## The agents (nodes)

| Node | Role | Output |
|------|------|--------|
| `initialize_research` | Assigns/resolves `research_id`, marks run started | `research_id`, `review_status`, timestamps |
| `research_planner` | Builds the research plan from inputs | `research_plan` (steps, focus areas) |
| `company_researcher_mock` | Mock company profile | `company_profile` |
| `competitor_discovery_mock` | Mock competitor list (3 direct competitors) | `competitors` |
| `evidence_validator_mock` | Mock evidence + validation summary | `evidence`, `validation_results` |
| `strategic_analyst_mock` | Mock opportunities/threats/recommendations | `strategic_analysis` |
| `report_generator_mock` | Assembles the final report from prior artifacts | `final_report` |
| `finalize_research` | Sets overall status; never reports success on failure | `review_status`, preserves `errors` |

## State transitions

Each node is `async (state: ResearchState) -> dict` returning a partial update. LangGraph merges updates into the Pydantic state. List fields (`competitors`, `evidence`, `errors`, `execution_metadata`) use `operator.add` reducers to accumulate.

## Error handling

- Nodes wrap logic in `try/except` via `graph/nodes/base.py::run_node`.
- On success: node update merged + `status: "completed"` metadata appended.
- On failure: `status: "failed"` metadata + an `errors` entry appended; the graph continues to `finalize_research`, which marks `review_status = "failed"`.
- The API never returns `status: "completed"` when any node has failed.

## Extensibility (future phases)

- **Conditional routing**: insert a review gate after `report_generator_mock` (e.g., route to a human-review node or back to `strategic_analyst_mock` on low confidence).
- **Parallel agents**: branch from `research_planner` into independent company/competitor/market subgraphs, then join.
- **Real LLM agents**: swap `*_mock` nodes for nodes that call `get_llm_client()` (OpenRouter/DeepSeek) once `OPENROUTER_API_KEY` is configured.
- **Persistence**: replace the in-memory `_research_store` with SQLAlchemy-backed models and the Alembic migrations once PostgreSQL is provisioned.
- **Auth/RBAC**: `organization_id` on `ResearchState` enables tenant isolation.

## Why mocks in Phase 1

- Zero LLM API credits consumed.
- Zero external network dependencies.
- Deterministic, reproducible tests.
- The graph, state schema, reducers, error handling, and API contract are all validated end-to-end before any probabilistic LLM component is introduced.
