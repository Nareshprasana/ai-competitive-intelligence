# Architecture — ACIS Phase 0 + Phase 1

## Overview

ACIS is a modular monorepo. The backend is a FastAPI service orchestrating a LangGraph `StateGraph` of deterministic mock agents. The frontend is a Next.js App Router dashboard that calls the backend. No LLM calls are made in Phase 1; no external API credits are consumed.

## High-level data flow

```
Client (Next.js)
     │  POST /api/v1/research  {company_name, industry, research_question}
     ▼
FastAPI (app/main.py)
     │
     ├─► Research Service (services/research_service.py)
     │       ├─ builds initial ResearchState
     │       └─► LangGraph StateGraph (graph/builder.py)
     │               ├─ initialize_research
     │               ├─ research_planner
     │               ├─ company_researcher_mock
     │               ├─ competitor_discovery_mock
     │               ├─ evidence_validator_mock
     │               ├─ strategic_analyst_mock
     │               ├─ report_generator_mock
     │               └─ finalize_research
     │       └─ returns structured ResearchResult
     │
     └─► 201 {research_id, status, results}
```

## Modules

| Module | Responsibility |
|--------|----------------|
| `app/core/config.py` | Pydantic Settings; all config from env / `.env` |
| `app/core/logging.py` | Centralized logging; secrets redacted |
| `app/core/exceptions.py` | Custom exceptions + centralized FastAPI handlers |
| `app/core/database.py` | SQLAlchemy async engine/session; graceful degradation without PG |
| `app/core/llm.py` | Provider-independent LLM factory (OpenRouter-compatible), lazy |
| `app/dependencies.py` | FastAPI dependency injection |
| `app/main.py` | FastAPI app factory, CORS, size-limit middleware, routers, lifespan |
| `app/api/v1/` | Versioned endpoints (health, research) |
| `app/schemas/research.py` | Pydantic request/response schemas |
| `app/graph/state.py` | Typed Pydantic `ResearchState` with `Annotated` list reducers |
| `app/graph/nodes/` | Eight deterministic mock node implementations |
| `app/graph/builder.py` | StateGraph construction (separate from node logic) |
| `app/services/research_service.py` | Orchestrates graph execution; in-memory result store (Phase 1) |

## State (`ResearchState`)

A Pydantic model carried through every node. List fields use `Annotated[T, operator.add]` reducers so values accumulate across nodes instead of being overwritten:

- `research_id`, `organization_id`, `company_name`, `industry`, `research_question`
- `research_plan`, `company_profile`, `competitors`, `product_intelligence`, `market_intelligence`
- `evidence`, `validation_results`, `strategic_analysis`, `final_report`
- `review_status`, `reviewer_feedback`
- `errors`, `execution_metadata`
- `created_at`, `updated_at`

## Graph execution

- Linear chain: `START → initialize_research → research_planner → company_researcher_mock → competitor_discovery_mock → evidence_validator_mock → strategic_analyst_mock → report_generator_mock → finalize_research → END`.
- Each node records execution metadata (`node_name`, `status`, `started_at`, `completed_at`, `duration_ms`, `mock`, `details`).
- Nodes catch exceptions internally; failures are appended to `errors` and metadata status is set to `failed`.
- `finalize_research` sets overall `review_status` to `failed` if any errors exist — the run is **never** reported as successful when a node fails.
- The graph is structured for future conditional routing (review gates) and parallel agents without changing node logic.

## LLM abstraction

- `LLMFactory` builds provider-independent clients (OpenRouter-compatible; DeepSeek default).
- Configured entirely from environment (`LLM_PROVIDER`, `LLM_MODEL`, `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, timeouts, etc.).
- No initialization at module import time; client created lazily.
- Phase 1: mock agents never call the LLM. Invoking the client without an API key raises `LLMConfigurationError` — no credits can be consumed accidentally.

## Database

- SQLAlchemy 2.0 async engine/session; `DeclarativeBase`.
- Engine created lazily; no connection at import time.
- Without `DATABASE_URL`, the app starts and `db.health_check()` returns `available: false` honestly.
- Alembic initialized (`backend/alembic/`) with an initial pgvector-compatible migration (`0001_initial_research_tables`). Online migrations require PostgreSQL; offline/SQL generation works without it.
- `pgvector` SQLAlchemy `Vector` type imported conditionally for metadata/column compatibility.

## Security

- Input validation via Pydantic (min/max lengths, non-empty).
- Environment-based secrets; none hardcoded; none in Git.
- Restricted CORS (configured origins, no wildcard).
- Request-size limit (default 4 MB).
- Safe error messages to clients; internal details not leaked.
- `organization_id` ownership modeled for future auth/RBAC and tenant isolation.

## Frontend

Next.js App Router, JavaScript, Tailwind CSS, shadcn-style components (implemented manually to avoid the interactive `shadcn init` CLI). Lives in `frontend/` and calls `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`). Includes a research submission form, status polling, execution-metadata display, and structured report rendering.

> The environment used to build this phase has no network access to the npm registry, so the frontend could not be `npm install`ed or started here. It is complete by inspection.
