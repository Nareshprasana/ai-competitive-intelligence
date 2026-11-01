# Task List: ACIS Phase 0 + Phase 1 (final state)

## Phase A: Repo foundation & backend core
- [x] Task 1: Repo structure, .gitignore, requirements, env template
- [x] Task 2: Core config (Pydantic settings), centralized logging
- [x] Task 3: Centralized exception handling + custom exceptions
- [x] Task 4: FastAPI app factory, DI, CORS, versioned router, health endpoint
- [x] Task 5: SQLAlchemy engine/session + Base, pgvector prep, Alembic init + migration

## Phase B: LangGraph core
- [x] Task 6: ResearchState Pydantic model + reducers
- [x] Task 7: Graph node implementations (8 mock nodes)
- [x] Task 8: Graph builder (StateGraph compilation), metadata tracking, error handling
- [x] Task 9: LLM factory (provider-independent, OpenRouter-compatible, lazy)

## Phase C: API & research flow
- [x] Task 10: Research schemas + service layer
- [x] Task 11: POST /api/v1/research + GET /api/v1/research/{id}
- [x] Task 12: Wire graph execution into research endpoint

## Phase D: Frontend
- [x] Task 13: Next.js app, Tailwind, layout + sidebar (code complete)
- [x] Task 14: Research submission form + API client (code complete)
- [x] Task 15: Status polling + structured report display (code complete)
  [NOTE: could not npm install / start — no network to npm registry in this env]

## Phase E: Tests
- [x] Task 16: Backend test suite (40 tests)
- [x] Task 17: Full test suite passes — 40 passed, 0 failed

## Phase F: Docs & git
- [x] Task 18: README + docs (architecture, agent-design, roadmap)
- [x] Task 19: Git branch phase-0-1-foundation, commit 1453827, not pushed