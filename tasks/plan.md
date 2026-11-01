# Implementation Plan: AI Competitive Intelligence System (ACIS) — Phase 0 + Phase 1

## Overview
Build a functioning, production-oriented AI Competitive Intelligence backend (FastAPI + LangGraph) and a minimal Next.js dashboard. Phase 1 uses deterministic mock agents (no LLM calls, no external API credits), a configurable LLM factory ready for DeepSeek/OpenRouter, SQLAlchemy + Alembic + pgvector prep that degrades gracefully without PostgreSQL, Pytest coverage, and documentation.

## Architecture Decisions
- Monorepo: `backend/`, `frontend/`, `infrastructure/`, `docs/` at repo root.
- LangGraph `StateGraph` with a Pydantic `ResearchState`; `Annotated` list fields use `operator.add` reducers for `competitors`, `evidence`, `errors`.
- Graph building (`graph/builder.py`) is strictly separate from node logic (`graph/nodes/`).
- Mock nodes never call an LLM; they return deterministic structured data and record execution metadata (node name, timestamps, duration, status).
- Nodes catch exceptions internally, record them in `errors`, and never let the graph report success when a node fails.
- LLM factory (`core/llm.py`) is provider-independent, OpenRouter-compatible, env-based, lazily initialized, and raises a clear error if invoked without configuration (no calls in Phase 1).
- SQLAlchemy async engine/session created lazily; never crashes at import; health endpoint reports DB availability honestly.
- FastAPI app with centralized logging, exception handling, CORS, DI, versioned API (`/api/v1`), health endpoint.
- Frontend: Next.js App Router (JS), Tailwind, shadcn-style components implemented manually (avoids interactive/network CLI), talks to the real FastAPI backend.
- Tests with pytest + httpx ASGITransport; no network, no secrets committed.

## Task List

### Phase A: Repo foundation & backend core
- [ ] Task 1: Create repo structure, .gitignore, python requirements, env template
- [ ] Task 2: Core config (Pydantic settings), centralized logging
- [ ] Task 3: Centralized exception handling + custom exceptions
- [ ] Task 4: FastAPI app factory, DI, CORS, versioned router, health endpoint
- [ ] Task 5: SQLAlchemy engine/session + Base, pgvector prep, Alembic init + initial migration

### Phase B: LangGraph core
- [ ] Task 6: ResearchState Pydantic model + reducers
- [ ] Task 7: Graph node implementations (8 mock nodes)
- [ ] Task 8: Graph builder (StateGraph compilation), metadata tracking, error handling
- [ ] Task 9: LLM factory (provider-independent, OpenRouter-compatible, lazy)

### Phase C: API & research flow
- [ ] Task 10: Research schemas (Pydantic) and service layer
- [ ] Task 11: POST /api/v1/research and GET /api/v1/research/{id} endpoints
- [ ] Task 12: Wire graph execution into research endpoint

### Phase D: Frontend
- [ ] Task 13: Next.js app, Tailwind, layout + sidebar
- [ ] Task 14: Research submission form + API client
- [ ] Task 15: Status polling + structured report display

### Phase E: Tests
- [ ] Task 16: Backend tests (startup, health, validation, research API, state, nodes, full graph, order, report, failure, LLM config, DB unavailable)
- [ ] Task 17: Run full test suite, fix failures

### Phase F: Docs & git
- [ ] Task 18: README.md, docs/architecture.md, docs/agent-design.md, docs/development-roadmap.md
- [ ] Task 19: Git branch, commits, final review

## Checkpoints
### After Phase A/B: Backend starts, health works, graph executes, tests pass
### After Phase C/D: Frontend submits research, backend returns structured report end-to-end
### After Phase E/F: All acceptance criteria verified, docs complete, committed

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| PostgreSQL not available | High | Graceful degradation; engine lazy; health reports DB status honestly |
| langchain full package missing | Med | Use langchain_core (installed); no LLM calls in Phase 1 |
| shadcn/ui CLI needs network/interactive | Med | Implement shadcn-style components manually with Tailwind |
| Python 3.14 compatibility | Low | Pin minimal deps; verify imports at install |

## Open Questions
- None blocking.