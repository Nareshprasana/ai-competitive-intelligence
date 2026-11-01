# Implementation Plan: ACIS Phase 0 + Phase 1 + Phase 1.5 + Phase 2A

## Overview
ACIS backend: FastAPI + LangGraph multi-agent system with persistent PostgreSQL storage and a real AI-powered Company Research Agent (Phase 2A). Frontend: Next.js dashboard. Phase 2A replaces the mock company_researcher with a real agent using search + LLM extraction, evidence with provenance, and PostgreSQL persistence. No LLM credits consumed unless explicitly configured.

## Architecture Decisions
- **company_researcher** replaces **company_researcher_mock** in the LangGraph linear workflow.
- Real agent uses `CompanyResearcherAgent` with budgeted search, SSRF-safe fetching, LLM structured extraction, evidence provenance, conflict detection, and PostgreSQL persistence.
- Mock provider is default (no network, no credits); DuckDuckGo available for live free-tier search.
- LLM client is real OpenRouter HTTP with structured Pydantic output, retry logic, timeout handling — no calls at import time.
- All repository queries enforce `organization_id` server-side.

## Task List

### Phase 0 + 1 + 1.5 (complete)
- [x] Repo structure, FastAPI app, LangGraph core, 8 mock nodes
- [x] LLM factory, config, logging, exceptions, DI, CORS, health endpoint
- [x] SQLAlchemy, Alembic, PostgreSQL persistence, graceful degradation
- [x] LangGraph checkpointing, 40 core tests, docs, Docker

### Phase 2A (complete)
- [x] Search provider abstraction + mock + DuckDuckGo providers
- [x] CompanyProfile/Evidence schemas, Evidence intelligence logic
- [x] BaseAgent (budget, rate limit, cache, SSRF), CompanyResearcherAgent
- [x] Real OpenRouter LLM client with structured output
- [x] Config + requirements (selectolax, search env vars)
- [x] CompanyProfile/EvidenceClaim ORM models + repositories + migration 0002
- [x] company_researcher node registered in graph builder
- [x] ~23 new tests (search, schemas, evidence, agent, LLM, persistence, LangGraph)
- [x] Existing tests pass in fallback mode; persistence tests pass with DB

### Docs + Git (IN PROGRESS)
- [ ] Update docs/architecture.md, docs/agent-design.md, docs/development-roadmap.md, README.md
- [ ] Commit on phase-0-1-foundation, don't merge to main

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No npm network in env | High | Frontend verification documented as limitation, not claimed |
| pgvector not on Windows PG | High | JSONB used instead; migration pgvector-ready for future |
| LLM credit spend | High | No calls at import; credits only consumed when API key configured + live provider |

## Open Questions
- None blocking.