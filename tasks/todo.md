# Task List: ACIS Phase 0 + Phase 1

## Phase A: Repo foundation & backend core
- [ ] Task 1: Repo structure, .gitignore, requirements, env template
- [ ] Task 2: Core config (Pydantic settings), centralized logging
- [ ] Task 3: Centralized exception handling + custom exceptions
- [ ] Task 4: FastAPI app factory, DI, CORS, versioned router, health endpoint
- [ ] Task 5: SQLAlchemy engine/session + Base, pgvector prep, Alembic init + migration

## Phase B: LangGraph core
- [ ] Task 6: ResearchState Pydantic model + reducers
- [ ] Task 7: Graph node implementations (8 mock nodes)
- [ ] Task 8: Graph builder (StateGraph compilation), metadata tracking, error handling
- [ ] Task 9: LLM factory (provider-independent, OpenRouter-compatible, lazy)

## Phase C: API & research flow
- [ ] Task 10: Research schemas + service layer
- [ ] Task 11: POST /api/v1/research + GET /api/v1/research/{id}
- [ ] Task 12: Wire graph execution into research endpoint

## Phase D: Frontend
- [x] Task 13: Next.js app, Tailwind, layout + sidebar
- [x] Task 14: Research submission form + API client
- [x] Task 15: Status polling + structured report display

## Phase E: Tests
- [ ] Task 16: Backend test suite
- [ ] Task 17: Run full test suite, fix failures

## Phase F: Docs & git
- [ ] Task 18: README + docs (architecture, agent-design, roadmap)
- [ ] Task 19: Git branch, commits, final review
