# Task List: ACIS Phase 1.5 — Integration Verification & Database Persistence (FINAL)

## Phase A: Inspection (done)
- [x] Inspected existing implementation, git history, working tree
- [x] Confirmed PostgreSQL 18 running, acis_db/acis_app configured
- [x] Installed asyncpg, psycopg[binary], psycopg_pool, langgraph-checkpoint-postgres
- [x] Confirmed AsyncPostgresSaver adapter works with ainvoke (thread-based, resume)
- [x] pgvector extension NOT available on Windows PG — documented as prerequisite

## Phase B: Backend persistence (done)
- [x] SQLAlchemy ORM models (Research table, indexes, org ownership)
- [x] SQLAlchemy repository layer (create, get_by_id, update, list_by_org, cross-org isolation)
- [x] Alembic migration matches models (0001_initial_research_tables)
- [x] .env.example + requirements.txt updated
- [x] alembic env.py imports Research model
- [x] research_service uses repository + checkpointer + fallback store
- [x] Existing 40 tests still pass (without DATABASE_URL)

## Phase C: LangGraph checkpointing (done)
- [x] AsyncPostgresSaver adapter (delegates sync get_tuple/put/put_writes to thread)
- [x] graph builder accepts optional checkpointer
- [x] Thread-based execution (thread_id = research_id)
- [x] Checkpoint storage separate from business records
- [x] Resume supported (aget_tuple works)

## Phase D: Frontend verification (LIMITATION DOCUMENTED)
- [x] npm registry reachable (npm view works) but npm install HANGS (tarball downloads)
- [x] Frontend dev server could NOT be started
- [x] Frontend production build could NOT be verified
- [x] End-to-end research via frontend could NOT be tested
- [x] Limitation documented in README + architecture.md (not claimed as a result)

## Phase E: New tests (done - 15 tests)
- [x] PostgreSQL persistence (create/retrieve/update)
- [x] Cross-organization data isolation (repository + API level)
- [x] Status updates persisted
- [x] Migration correctness (alembic upgrade head, researches table exists)
- [x] Checkpoint configuration (setup creates tables, store + retrieve)
- [x] Research retrieval after restart simulation (API persistence test)
- [x] Existing 40 tests still green

## Phase F: Security + docs + git
- [x] Server-side org ownership enforced (repository filters by organization_id)
- [x] Client-supplied org IDs not trusted (_resolve_organization_id)
- [x] Cross-organization access tests
- [x] No secrets in Git (.env.example only)
- [x] Docs updated (architecture, agent-design, roadmap, README)
- [x] Commit on phase-0-1-foundation, don't merge to main