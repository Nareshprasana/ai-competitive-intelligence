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

1. Backend:
   ```
   cd backend
   cp .env.example .env
   # Set DATABASE_URL=postgresql+asyncpg://acis_app:acis_dev_password@127.0.0.1:5432/acis_db
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn app.main:app --reload
   ```
2. Tests:
   ```
   cd backend
   # Without DATABASE_URL (fallback mode): 40 tests
   pytest
   # With DATABASE_URL (persistence mode): 15 additional tests
   DATABASE_URL=postgresql+asyncpg://acis_app:acis_dev_password@127.0.0.1:5432/acis_db pytest
   ```
3. Frontend:
   ```
   cd frontend
   npm install && npm run dev   # requires working npm registry access
   ```
