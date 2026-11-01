# Development Roadmap

## Phase 0 + Phase 1 (complete — this delivery)

- [x] Repository structure (monorepo: backend, frontend, infrastructure, docs)
- [x] FastAPI app, Pydantic settings, centralized logging/exception handling
- [x] CORS, dependency injection, API versioning (`/api/v1`), health endpoint, request-size limit
- [x] LangGraph `StateGraph` with typed Pydantic `ResearchState` and reducers
- [x] Eight deterministic mock nodes in required order
- [x] Graph building separate from node logic; execution metadata; error handling
- [x] Provider-independent LLM factory (OpenRouter-compatible); lazy; no LLM calls
- [x] SQLAlchemy 2.0 async engine/session; Alembic; pgvector-compatible migration
- [x] Graceful degradation without PostgreSQL (honest health reporting)
- [x] `POST /api/v1/research` and `GET /api/v1/research/{id}` endpoints
- [x] Pytest suite (40 tests): startup, health, validation, API, state, nodes, graph, order, report, failure, LLM config, DB-unavailable
- [x] Minimal Next.js dashboard (research form, status polling, report display)
- [x] Documentation (README, architecture, agent-design, roadmap)

## Phase 2 (planned)

- [ ] Replace in-memory result store with SQLAlchemy-backed persistence + Alembic migrations
- [ ] Add PostgreSQL + pgvector to `docker-compose.yml`; run migrations on startup
- [ ] Replace mock agents with real LLM-backed agents (OpenRouter / DeepSeek) behind the LLM factory
- [ ] Add authentication (JWT/session), RBAC, and organization-level tenant isolation
- [ ] Add conditional routing (review gates) and parallel sub-agents in the LangGraph
- [ ] Add rate limiting, request tracing, and structured audit logging

## Phase 3 (planned)

- [ ] Production Docker Compose deployment (backend, frontend, PostgreSQL, pgvector)
- [ ] CI pipeline (lint, type check, tests, build)
- [ ] Frontend polish: research history, comparison charts, report export (PDF)
- [ ] Performance tuning and load testing

## Immediate next steps to run locally

1. Backend: `cd backend && cp .env.example .env && pip install -r requirements.txt && uvicorn app.main:app --reload`
2. Frontend: `cd frontend && npm install && npm run dev` (requires network access to npm)
3. Open `http://localhost:3000` and submit a research request; verify `http://localhost:8000/api/v1/health`.
