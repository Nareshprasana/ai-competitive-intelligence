# Architecture — ACIS Phase 0 + Phase 1 + Phase 1.5

## Overview

ACIS is a modular monorepo. The backend is a FastAPI service orchestrating a LangGraph `StateGraph` of deterministic mock agents. The frontend is a Next.js App Router dashboard that calls the backend. Phase 1.5 adds persistent research storage (PostgreSQL + SQLAlchemy repositories + Alembic) and LangGraph PostgreSQL checkpointing. No LLM calls are made in Phase 1/1.5; no external API credits are consumed.

## High-level data flow

```
Client (Next.js)
     │  POST /api/v1/research  {company_name, industry, research_question}
     ▼
FastAPI (app/main.py)
     │
     ├─► Research Service (services/research_service.py)
     │       ├─ builds initial ResearchState
     │       ├─ enforces organization ownership (server-side)
     │       ├─► LangGraph StateGraph (graph/builder.py)
     │       │   ├─ initialize_research
     │       │   ├─ research_planner
     │       │   ├─ company_researcher_mock
     │       │   ├─ competitor_discovery_mock
     │       │   ├─ evidence_validator_mock
     │       │   ├─ strategic_analyst_mock
     │       │   ├─ report_generator_mock
     │       │   └─ finalize_research
     │       │   (optionally compiled with a PostgreSQL checkpointer)
     │       ├─ persists result via ResearchRepository (PostgreSQL)
     │       └─ returns structured ResearchResult
     │
     └─► 201 {research_id, status, results}

GET /api/v1/research/{research_id}
     │
     ├─► ResearchRepository fetches record, restricted to the owning
     │    organization_id (server-side enforced; client-supplied org IDs
     │    are never trusted as authorization evidence)
     │
     └─► 200 {research_id, status, results}
```

## Modules

| Module | Responsibility |
|--------|----------------|
| `app/core/config.py` | Pydantic Settings; all config from env / `.env` |
| `app/core/logging.py` | Centralized logging; secrets redacted |
| `app/core/exceptions.py` | Custom exceptions + centralized FastAPI handlers |
| `app/core/database.py` | SQLAlchemy async engine/session; graceful degradation without PG; LangGraph checkpointer factory |
| `app/core/checkpoint.py` | Async-compatible PostgreSQL checkpointer adapter for LangGraph |
| `app/core/llm.py` | Provider-independent LLM factory (OpenRouter-compatible), lazy |
| `app/dependencies.py` | FastAPI dependency injection |
| `app/main.py` | FastAPI app factory, CORS, size-limit middleware, routers, lifespan |
| `app/api/v1/` | Versioned endpoints (health, research) |
| `app/schemas/research.py` | Pydantic request/response schemas |
| `app/models/research.py` | SQLAlchemy ORM `Research` model (indexes, org ownership, timestamps) |
| `app/repositories/research.py` | SQLAlchemy repository with server-side organization isolation |
| `app/graph/state.py` | Typed Pydantic `ResearchState` with `Annotated` list reducers |
| `app/graph/nodes/` | Eight deterministic mock node implementations |
| `app/graph/builder.py` | StateGraph construction (optional checkpointer), separate from node logic |
| `app/services/research_service.py` | Orchestrates graph execution; repository-backed persistence with fallback store |

## State (`ResearchState`)

A Pydantic model carried through every node. List fields use `Annotated[T, operator.add]` reducers so values accumulate across nodes instead of being overwritten.

## Persistent storage (`researches` table)

When `DATABASE_URL` is configured, research records are persisted to PostgreSQL:

- `research_id` (unique, indexed), `organization_id` (indexed), `company_name`, `industry`, `research_question`
- `status`, `review_status` (indexed), `results` (JSON), `errors` (JSON)
- `created_at`, `updated_at` (timestamptz, server default `now()`)
- Composite index `(organization_id, status)` for org-scoped lookups

All repository queries filter by `organization_id`, so records are never exposed across organizations.

## LangGraph checkpointing

When `DATABASE_URL` is configured, `AsyncPostgresSaver` (from `langgraph-checkpoint-postgres`) provides PostgreSQL checkpoint storage in dedicated `checkpoints` / `checkpoint_writes` tables — SEPARATE from the business `researches` table.

- Thread-based execution: `config={"configurable": {"thread_id": "<research_id>"}}`
- Checkpoints are stored per thread and can be retrieved for resume
- `AsyncPostgresSaver.setup()` creates the checkpoint tables at startup

Because the installed `PostgresSaver` exposes working sync methods but raises `NotImplementedError` on its async tuple methods, `app/core/checkpoint.py::AsyncPostgresSaver` wraps `get_tuple`/`put`/`put_writes` in `asyncio.to_thread` so LangGraph's `ainvoke` can checkpoint and resume.

## Database degradation

Without `DATABASE_URL`, the application starts normally. The SQLAlchemy engine is not created, `db.health_check()` returns `available: false` honestly, and research results fall back to an in-memory store (process-local only). No connection is ever falsely reported as successful.

## LLM abstraction

`LLMFactory` builds provider-independent clients (OpenRouter-compatible; DeepSeek default). Configured entirely from environment. No initialization at module import time. Phase 1/1.5: mock agents never call the LLM. Invoking the client without an API key raises `LLMConfigurationError` — no credits can be consumed accidentally.

## Security

- Input validation via Pydantic (min/max lengths, non-empty).
- Environment-based secrets; none hardcoded; none in Git.
- Restricted CORS (configured origins, no wildcard).
- Request-size limit (default 4 MB).
- Safe error messages to clients; internal details not leaked.
- `organization_id` ownership modeled and enforced server-side for tenant isolation.

## Frontend

Next.js App Router, JavaScript, Tailwind CSS, shadcn-style components. Calls `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`). Includes a research submission form, status polling, execution-metadata display, and structured report rendering.

> The environment used to build this phase has no working `npm install` path to the npm registry (tarball downloads hang), so the frontend could not be `npm install`ed or started here. Frontend verification (dev server, production build, e2e research) is therefore documented as a limitation, not a claimed result.
