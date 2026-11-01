# Development Roadmap

## Phase 0 + Phase 1 (complete)

- [x] Repository structure (monorepo: backend, frontend, infrastructure, docs)
- [x] FastAPI app, Pydantic settings, centralized logging/exception handling
- [x] CORS, dependency injection, API versioning (`/api/v1`), health endpoint, request-size limit
- [x] LangGraph `StateGraph` with typed Pydantic `ResearchState` and reducers
- [x] Eight deterministic mock agents in required linear order
- [x] Graph building separate from node logic; execution metadata; error handling
- [x] Provider-independent LLM factory (OpenRouter-compatible); lazy; no LLM calls
- [x] SQLAlchemy 2.0 async engine/session; Alembic; pgvector-compatible migration
- [x] Graceful degradation without PostgreSQL (honest health reporting)
- [x] `POST /api/v1/research` and `GET /api/v1/research/{id}` endpoints
- [x] Pytest suite (40 tests): startup, health, validation, API, state, nodes, graph, order, report, failure, LLM config, DB-unavailable
- [x] Minimal Next.js dashboard (form, status polling, report display)
- [x] Documentation (README, architecture, agent-design, roadmap)

## Phase 1.5 — Integration Verification & Database Persistence (complete)

- [x] PostgreSQL 18 integration: `acis_db` / `acis_app`, password auth (scram-sha-256)
- [x] SQLAlchemy ORM `Research` model with indexes and org ownership
- [x] `ResearchRepository` with server-side organization isolation
- [x] Alembic migration `0001_initial_research_tables` applied to `acis_db`
- [x] In-memory store replaced by PostgreSQL-backed persistence (with in-memory fallback when DB unavailable)
- [x] Safe transaction handling (`flush` + `commit` in service layer)
- [x] LangGraph `AsyncPostgresSaver` checkpointing (async adapter over sync `PostgresSaver`)
- [x] Thread-based research execution (`thread_id = research_id`)
- [x] Checkpoint storage separate from business records
- [x] Resume support (checkpoint retrieval via `aget_tuple`)
- [x] New tests: 15 persistence/checkpoint/API tests (repository, cross-org isolation, status updates, migration, checkpoints, API persistence)
- [x] Existing 40 tests remain green (fallback mode without DATABASE_URL)

## Phase 2A — Real Company Research Agent (complete)

- [x] Search provider abstraction: `SearchProvider` interface, `SearchResult`/`SearchQuery` schemas
- [x] Deterministic mock search provider (offline, no network, no credits) for tests
- [x] DuckDuckGo HTML provider (free, no API key, SSRF-protected, size-limited)
- [x] `CompanyProfile` / `CompanySize` Pydantic schemas
- [x] `Evidence` / `EvidenceCollection` / `EvidenceType` / `VerificationStatus` schemas
- [x] Evidence collection/validation: confidence scoring, conflict detection, source classification
- [x] `BaseAgent`: search budgeting, rate limiting, result caching, SSRF-safe URL validation, HTTP fetch with size limits/timeouts
- [x] `CompanyResearcherAgent`: full pipeline (query gen → search → retrieval → LLM extraction → evidence → validation → profile)
- [x] Real OpenRouter LLM client: structured Pydantic output, retry logic, timeout/rate-limit handling, no import-time calls
- [x] Search provider config: `SEARCH_PROVIDER`, `SEARCH_MAX_QUERIES`, `SEARCH_MAX_PAGES`, `DUCKDUCKGO_BASE_URL`
- [x] `CompanyProfile` / `EvidenceClaim` SQLAlchemy ORM models with org isolation
- [x] `CompanyRepository` / `EvidenceRepository` with server-side organization isolation
- [x] Alembic migration `0002_company_profiles` (`company_profiles` + `evidence_claims` tables)
- [x] `company_researcher` node replaces `company_researcher_mock` in LangGraph (mock retained for back-compat)
- [x] New tests: ~23 unit/integration tests (search, schemas, evidence, agent, LLM, persistence, LangGraph integration)
- [x] Existing tests remain green (fallback mode without DATABASE_URL)
- [x] Persistence tests pass (with DATABASE_URL)

## Phase 2B — Competitor Discovery Agent

- [x] Replace `competitor_discovery_mock` in the active graph with a real discovery node
- [x] Reuse company research profiles, evidence, and search results
- [x] Add typed direct, indirect, emerging, and substitute competitor schemas
- [x] Add deterministic weighted overlap scoring and evidence-based qualification gates
- [x] Validate citations against retrieved source URLs and retain source snippets
- [x] Add organization/research-scoped competitor and evidence persistence
- [x] Add bounded search/candidate/token settings and checkpoint-compatible state updates
- [x] Add mocked unit/integration coverage and update agent/architecture docs

## Phase 2C - Codebase knowledge and development workflow

This phase adds a local Graphify architecture graph, Copilot project guidance informed by Ponytail, a DNS-rebinding fix, and safer PostgreSQL-test configuration. It does not add another competitive-intelligence agent.

### Graphify installation and use

- Official project: [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify); official package: `graphifyy`. Installed in an isolated `uv tool` environment (`graphifyy v0.9.89`), not in ACIS backend/frontend dependencies.
- To install on Windows with `uv`: `uv tool install graphifyy`. Project integration: `graphify install --platform copilot --project` (inspect existing `.github/copilot-instructions.md` before installation; merge rather than overwrite).
- The Copilot skill/rules are project instructions in `.github/copilot-instructions.md`; use Graphify's official install/update instructions if regenerating them.
- Initial extraction used local code-only mode. The official incremental `graphify update .` then indexed code and five Markdown files (README, the three architecture/design/roadmap docs, and Copilot instructions) locally. The current graph has 1,148 nodes, 2,776 edges, and 58 communities; `graph.json` references 114 distinct source paths. Graphify reports zero token cost; no embeddings, vector database, or external LLM/API calls were used.
- All graph source references were checked against repository files and line ranges; no missing files or out-of-range locations were found. `.graphifyignore` excludes `tasks/plan.md` and `tasks/todo.md`; these pre-existing user changes are not represented in the graph or commits.
- Required tracked artifacts: `graphify-out/graph.json`, `graphify-out/GRAPH_REPORT.md`, and `graphify-out/graph.html`.
- Query with `graphify query "..."`, `graphify path "<symbol>" "<symbol>"`, or `graphify explain "<concept>"`. Refresh changed source with `graphify update .`; then rerun scoped queries and inspect the report for stale references.
- Representative query results: `ResearchForm() -> submitResearch()` and `submit_research() -> run_research()` are direct call edges; `run_research() -> get_graph() -> build_graph()` traces orchestration; `_persist_competitor_discovery() -> CompetitorRepository` and `fetch_page() -> _resolve_public_addresses()` confirm persistence and DNS-pin helper paths. `CompetitorEvidenceRepository -> CompetitorEvidence` is tagged inferred, so verify ownership claims in ORM/repository source. Broad text queries can return truncated neighborhoods; use `path` for focused traces.
- No Git hook or watcher is installed. Manual incremental updates avoid unnecessary background scans and preserve existing Git workflows.
- **Scope limitation:** the graph report lists 10 unsupported/config files as unclassified. The extracted graph also contains inferred edges (11%); verify them against source. Graphify's static analysis cannot prove that code is dead, unreachable, or orphaned. The frontend-to-backend HTTP edge is not represented: source inspection confirms `ResearchForm -> submitResearch -> POST /api/v1/research -> submit_research`, but Graphify does not connect across that HTTP boundary.
- **Architecture risk notes:** the report found no import cycles. Its highest-degree nodes include `ResearchState` (70 edges), `SearchResult` (50), and `CompetitorResearcherAgent` (46); treat this as a coupling-review signal, not proof of a defect. Repeated labels such as the active and mock `competitor_discovery()` make unqualified paths ambiguous. Organization-scoped repositories are not authentication; auth/RBAC remains planned, so organization IDs must not be treated as an authorization boundary.

### Ponytail and combined Copilot workflow

- Official source: [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail), `skills/ponytail/SKILL.md` (reviewed from `main`; no separate Copilot plugin was installed).
- Copilot-compatible integration is merged into `.github/copilot-instructions.md`; it emphasizes reuse, focused diffs, no unnecessary dependencies, preserved validation/security, tests, and explicit reporting of skipped checks and risks. Existing Graphify guidance and ACIS architecture/security requirements remain authoritative.
- The project workflow is: understand task -> query Graphify -> apply Ponytail minimal-change guidance -> read/trace source -> identify security/data-integrity/compatibility constraints -> implement -> focused tests -> validate -> refresh/validate graph -> diff review -> commit only task-related files.

### SSRF/DNS-rebinding mitigation

`backend/app/agents/base.py::fetch_page` resolves the requested host once per request, rejects the request if any DNS answer is non-global, and sends the HTTP request to a vetted IP literal. It retains the original Host header and HTTPS SNI/certificate hostname. Redirects are manual, bounded, and independently resolved/validated. Existing timeout, retry, and response-byte limits remain. Mocked DNS regression tests cover pinning, mixed public/private records, and redirects to metadata addresses. This relies on HTTPX/httpcore honoring the literal target and `sni_hostname`; custom transports or proxy changes require renewed validation. It does not claim coverage for unrelated network paths.

### PostgreSQL test safety and verification

- Tests that require PostgreSQL: `tests/unit/test_persistence.py`, `tests/unit/test_checkpoint.py`, `tests/unit/test_competitor_persistence.py`, `tests/integration/test_persistence_company.py`, and `tests/integration/test_persistence_api.py`.
- Without `ACIS_TEST_DATABASE_URL`, those modules skip; the test harness also blanks `DATABASE_URL` so a developer `.env` cannot silently redirect tests to a non-test database.
- To run them, create/use a dedicated PostgreSQL database whose name contains a delimited `test` component (for example `acis_test`), set `ACIS_TEST_DATABASE_URL`, set `DATABASE_URL` to that same URL for Alembic, run `alembic upgrade head`, then run only the listed tests. The harness rejects non-PostgreSQL URLs and unsafe database names. Never use production/development databases or run destructive setup against them.
- PostgreSQL persistence and checkpoint integration remain unverified until run against a dedicated test database; migration correctness alone is not a substitute.

## Phase 2 (planned)

- [ ] Replace fallback in-memory store entirely with PostgreSQL (require DATABASE_URL in production)
- [ ] Add authentication (JWT/session), RBAC, and organization-level tenant isolation
- [ ] Add conditional routing (review gates) and parallel sub-agents in the LangGraph
- [ ] Install pgvector extension on PostgreSQL; add vector columns for semantic search
- [ ] Add rate limiting, request tracing, and structured audit logging

## Phase 3 (planned)

- [ ] Production Docker Compose deployment (backend, frontend, PostgreSQL, pgvector)
- [ ] CI pipeline (lint, type check, tests, build)
- [ ] Frontend polish: research history, comparison charts, report export (PDF)
- [ ] Performance tuning and load testing

## Immediate next steps to run locally

1. Backend: from `backend/`, create a virtual environment, install `requirements.txt`, configure `.env`, apply migrations only to the intended development database, then run `uvicorn app.main:app --reload`.
2. Offline tests: from `backend/`, run `python -m pytest`. PostgreSQL tests skip unless `ACIS_TEST_DATABASE_URL` is explicitly supplied.
3. PostgreSQL tests: create a dedicated `acis_test` database, set `ACIS_TEST_DATABASE_URL` to it and `DATABASE_URL` to the same URL, run `alembic upgrade head`, then run the five persistence/checkpoint modules listed above with `python -m pytest`. Never substitute a development or production database.
4. Frontend: from `frontend/`, run `npm install` and `npm run dev` where npm registry access is available.
5. After changing code, run `graphify update .` and inspect targeted `graphify query`/`path` results before relying on the refreshed index.
