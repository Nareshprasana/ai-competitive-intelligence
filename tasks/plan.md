# Implementation Plan: ACIS Phase 1.5 — Integration Verification & Database Persistence

## Overview
Complete Phase 1.5: verify the frontend (install, dev server, production build, end-to-end research), replace the in-memory research store with PostgreSQL-backed persistence via SQLAlchemy repositories + Alembic migrations, add LangGraph PostgreSQL checkpointing, enforce server-side organization ownership, and add tests. Existing 40 Phase-1 tests must remain green; no LLM credits consumed; no Redis/Kafka.

## Architecture Decisions
- Keep existing API contracts (`POST /api/v1/research`, `GET /api/v1/research/{id}`) compatible.
- New `repositories/` layer for DB access; service layer switches from in-memory store to repository.
- Separate `researches` (business records) from LangGraph checkpoints (`checkpoints` table).
- LangGraph `AsyncPostgresSaver` checkpointing, thread-based execution, resume support.
- Organization ownership enforced server-side; client-supplied `organization_id` ignored/overridden.
- Existing `__pycache__`, `.pytest_cache`, alembic `__pycache__` are build artifacts, not source.

## Task List
- [ ] Task 1: Repo inspection (complete — read existing modules, git history, tree)
- [ ] Task 2: Frontend verification (npm install, dev server, production build, e2e research)
- [ ] Task 3: PostgreSQL integration (models, repositories, Alembic migrations)
- [ ] Task 4: Replace in-memory storage with PostgreSQL-backed persistence
- [ ] Task 5: LangGraph PostgreSQL checkpointing (AsyncPostgresSaver, threads, resume)
- [ ] Task 6: Tests (persistence, restart survival, status updates, txn failures, repo ops, migration, checkpoints, cross-org isolation)
- [ ] Task 7: Security (server-side org ownership, no trusted client org IDs, unauthorized access tests)
- [ ] Task 8: Resource efficiency (no Redis/Kafka, no local LLM, no credits, lightweight DB)
- [ ] Task 9: Git management (commit logically, preserve branch, don't merge to main)

## Checkpoints
- After Task 2: frontend verifiable (or limitation documented honestly)
- After Task 4: backend persists research to Postgres, existing 40 tests still green
- After Task 5: LangGraph checkpointing configured + tested
- After Task 6: new tests pass; existing 40 green
- After Task 9: committed on phase-0-1-foundation, not merged to main

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No npm network in env | High | Document honestly; don't claim frontend verification |
| No PostgreSQL running | High | Tests use sqlite fallback or skip; document requirement |
| langgraph version checkpointer API | Med | Verify installed langgraph API before coding |

## Open Questions
- Whether PostgreSQL is available/running in this environment.
- Whether npm registry is reachable from this environment.