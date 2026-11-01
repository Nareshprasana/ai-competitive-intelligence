# Task List: ACIS Phase 0 + Phase 1 + Phase 1.5 + Phase 2A (FINAL)

## Phase A: Repo inspection (done)
- [x] Inspected ResearchState, graph nodes/builder, LLM factory, DB models/repositories, tests

## Phase B: Search tool layer (done)
- [x] app/tools/search/base.py — abstract SearchProvider
- [x] app/tools/search/schemas.py — SearchResult, SearchQuery
- [x] app/tools/search/providers/__init__.py
- [x] app/tools/search/providers/mock.py — deterministic mock
- [x] app/tools/search/providers/duckduckgo.py — real DDG search

## Phase C: Schemas (done)
- [x] app/schemas/company.py — CompanyProfile, CompanySize
- [x] app/schemas/evidence.py — Evidence, EvidenceCollection

## Phase D: Intelligence layer (done)
- [x] app/intelligence/evidence.py — evidence collection/validation

## Phase E: Agent layer (done)
- [x] app/agents/base.py — base agent with budget/retry/SSRF
- [x] app/agents/company_researcher.py — Company Research Agent

## Phase F: LLM integration (done)
- [x] app/core/llm.py — real OpenRouter HTTP client with structured output

## Phase G: Config + requirements (done)
- [x] app/core/config.py — search provider fields
- [x] backend/.env.example — search env vars
- [x] backend/requirements.txt — selectolax

## Phase H: Database models + repositories + migration (done)
- [x] app/models/company.py — CompanyProfile, EvidenceClaim ORM
- [x] app/repositories/company.py — CompanyRepository
- [x] app/repositories/evidence.py — EvidenceRepository
- [x] alembic/versions/0002_company_profiles.py

## Phase I: Replace mock node in LangGraph (done)
- [x] app/graph/nodes/company_researcher.py — real agent node
- [x] app/graph/builder.py — registered company_researcher node
- [x] app/graph/nodes/__init__.py — exports both real + mock

## Phase J: Tests (done — verified)
- [x] tests/unit/test_search_provider.py
- [x] tests/unit/test_search_schemas.py
- [x] tests/unit/test_company_schemas.py
- [x] tests/unit/test_evidence_schemas.py
- [x] tests/unit/test_evidence_intelligence.py
- [x] tests/unit/test_agent_base.py
- [x] tests/unit/test_company_researcher_agent.py (mocked LLM/search)
- [x] tests/unit/test_llm_client.py (mocked HTTP)
- [x] tests/integration/test_company_researcher_node.py (LangGraph integration)
- [x] tests/integration/test_persistence_company.py (DB + org isolation)
- [x] Existing tests pass in fallback mode (without DATABASE_URL)
- [x] Persistence tests pass in DB mode (with DATABASE_URL)

## Phase K: Docs + Git (IN PROGRESS)
- [x] Update docs/architecture.md
- [x] Update docs/agent-design.md
- [x] Update docs/development-roadmap.md
- [x] Update README.md
- [ ] Commit on phase-0-1-foundation, don't merge to main