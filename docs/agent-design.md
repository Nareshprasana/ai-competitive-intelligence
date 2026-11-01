# Agent Design — ACIS LangGraph Multi-Agent System (Phase 1 + 1.5 + 2A + 2B)

## Design principles

- **Genuine multi-agent system**, not a basic chatbot: a LangGraph `StateGraph` with specialized nodes that pass a typed `ResearchState` between them.
- **Deterministic mocks in Phase 1**: no agent performs real research, calls an LLM, or consumes external credits. Every node returns structured placeholder data clearly marked `mock: true`. This is explicit and intentional — the graph is real, the data is not.
- **Separation of concerns**: node logic (`graph/nodes/`) is independent of graph wiring (`graph/builder.py`).
- **Observable execution**: every node records metadata; failures are captured, not swallowed.
- **Server-side organization ownership**: research records are owned by an `organization_id` enforced in the repository layer; clients cannot read another org's records.
- **No fabrication**: the Company Research Agent never invents missing information; unavailable data is `None`/empty, never hallucinated.

## The agents (nodes)

| Node | Role | Output |
|------|------|--------|
| `initialize_research` | Assigns/resolves `research_id`, marks run started | `research_id`, `review_status`, timestamps |
| `research_planner` | Builds the research plan from inputs | `research_plan` (steps, focus areas) |
| `company_researcher` | Real AI-powered company research: search + LLM extraction + evidence | `company_profile`, `evidence` |
| `competitor_discovery` | Evidence-backed competitor discovery and qualification | `competitors`, `evidence` |
| `evidence_validator_mock` | Mock evidence + validation summary | `evidence`, `validation_results` |
| `strategic_analyst_mock` | Mock opportunities/threats/recommendations | `strategic_analysis` |
| `report_generator_mock` | Assembles the final report from prior artifacts | `final_report` |
| `finalize_research` | Sets overall status; never reports success on failure | `review_status`, preserves `errors` |

## Company Research Agent pipeline

The `company_researcher` node runs `CompanyResearcherAgent` through:

1. **Search query generation** — 10 prioritized aspects (overview, HQ/geography, founders/leadership, products/services, business model, target customers, industry classification, geographic markets, financials, recent developments).
2. **External search** — via configurable provider (mock deterministic, or DuckDuckGo HTML). Budgeted, cached, rate-limited.
3. **Source retrieval** — SSRF-protected, timeout-bounded, size-limited HTTP fetch.
4. **Information extraction** — LLM (OpenRouter/DeepSeek) returns structured `CompanyProfile` via Pydantic validation.
5. **Evidence collection** — each claim gets an `Evidence` record with source_url, source_title, source_domain, confidence, verification_status.
6. **Validation** — conflict detection across sources; confidence scored editorially (0–1, not statistical certainty).
7. **Persistence** — company profile and evidence claims stored in PostgreSQL, organization-isolated.

## Competitor Discovery Agent pipeline (Phase 2B)

The `competitor_discovery` node consumes the company profile, evidence, and
search results from `company_researcher`. It reuses retrieved results, then
performs a bounded set of additional searches for direct competitors,
alternatives, emerging entrants, substitutes, and market landscape sources.
LLM input explicitly treats retrieved content as untrusted; only citations
whose exact URLs were retrieved are retained. Profile websites are kept only
when the URL is public and the source host corroborates the company name.

Qualification is deterministic and separate from LLM extraction. A weighted
score uses product (0.20), service (0.15), customer (0.20), problem-space
(0.20), geographic (0.10), business-model (0.10), and market-positioning
(0.05) overlap. Text overlap uses Jaccard similarity over normalized keywords.
Every factor value is returned (including zero); missing company/candidate data
is separately listed in `unknown_information`.
Category assignment also requires relevant overlap evidence; candidates with
no supported product/customer/problem overlap are excluded rather than labeled
as substitutes. Emerging classification additionally requires source text
indicating recent entry or growth. The score is an analytical ranking, not an
LLM-generated probability.

Each profile separates evidence-backed source snippets, analytical overlap
judgments, and unknown fields. A verbatim claim corroborated by distinct source
domains is marked `partially_verified`; conflicting claims retain a
`conflicting` status. Official company sites, regulatory filings, investor
relations, press releases, industry reports, and credible publications are
prioritized when selecting profile evidence. A single source is unverified.
Competitor profiles and evidence are stored in organization- and
research-scoped PostgreSQL tables. Competitors have a composite foreign key to
their owning research and organization; evidence has a composite ownership
foreign key to its competitor. Normalized company keys and deterministic
evidence IDs make retries idempotent.

Search and page budgets and candidate/token caps are configurable through
`SEARCH_MAX_QUERIES`, `SEARCH_MAX_PAGES`, `COMPETITOR_MAX_CANDIDATES`,
`COMPETITOR_MAX_SEARCH_QUERIES`, and `COMPETITOR_MAX_TOKENS`. The default
search provider is deterministic mock data; live research requires explicit
DuckDuckGo configuration and an OpenRouter API key for LLM extraction.

## State transitions

Each node is `async (state: ResearchState) -> dict` returning a partial update. LangGraph merges updates into the Pydantic state. List fields (`search_results`, `competitors`, `evidence`, `errors`, `execution_metadata`) use `operator.add` reducers to accumulate.

## Error handling

- Nodes wrap logic in `try/except` via `graph/nodes/base.py::run_node`.
- On success: node update merged + `status: "completed"` metadata appended.
- On failure: `status: "failed"` metadata + an `errors` entry appended; the graph continues to `finalize_research`, which marks `review_status = "failed"`.
- The API never returns `status: "completed"` when any node has failed.
- The `company_researcher` node degrades gracefully: without LLM/search config, it builds a search-snippet-based profile marked unverified rather than failing.

## Persistence and checkpointing (Phase 1.5 + 2A)

- Business research records are stored in PostgreSQL (`researches` table) via `ResearchRepository`, with organization isolation.
- Company profiles stored in `company_profiles` table; evidence claims in `evidence_claims` table (FK → company_profiles), both organization-isolated.
- LangGraph checkpoint state is stored in separate PostgreSQL tables (`checkpoints`, `checkpoint_writes`) via `AsyncPostgresSaver`.
- Thread-based execution: each research run uses `thread_id = research_id`, enabling checkpoint/resume.
- Checkpoint storage is kept separate from business records.

## Extensibility (future phases)

- **Conditional routing**: insert a review gate after `report_generator_mock`.
- **Parallel agents**: branch from `research_planner` into independent subgraphs, then join.
- **Remaining real agents**: replace `evidence_validator_mock`, `strategic_analyst_mock`, and `report_generator_mock` with real agents.
- **Auth/RBAC**: `organization_id` on `ResearchState` enables tenant isolation; repository already enforces org-scoped queries.

## Why mocks in Phase 1

- Zero LLM API credits consumed.
- Zero external network dependencies.
- Deterministic, reproducible tests.
- The graph, state schema, reducers, error handling, and API contract are all validated end-to-end before any probabilistic LLM component is introduced.
