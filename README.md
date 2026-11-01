# AI Competitive Intelligence System (ACIS)

A production-oriented AI Competitive Intelligence system built with **LangGraph**, **FastAPI**, **PostgreSQL + pgvector**, and **Next.js**. Phase 0 + Phase 1 deliver a functioning multi-agent backend with deterministic mock agents (no LLM credits consumed). Phase 1.5 adds persistent research storage (PostgreSQL + SQLAlchemy repositories + Alembic migrations) and LangGraph PostgreSQL checkpointing. Phase 2A replaces the mock company researcher with a real AI-powered Company Research Agent that investigates real companies via search + LLM extraction, attaches evidence with provenance, and persists to PostgreSQL. A minimal Next.js dashboard talks to the real backend.

> **Status:** Phase 0 + Phase 1 + Phase 1.5 + Phase 2A complete (backend fully tested: ~78 tests; frontend code complete — see "Frontend" below for a verification limitation).

## Repository structure

```
ai-competitive-intelligence/
  backend/              # FastAPI + LangGraph backend (Python)
    app/
      core/             # config, logging, exceptions, database, LLM factory, checkpoint
      api/v1/           # versioned endpoints (health, research)
      graph/            # LangGraph state, nodes, builder
      models/           # SQLAlchemy ORM models
      repositories/     # SQLAlchemy data-access repositories
      schemas/          # Pydantic request/response schemas
      services/         # research orchestration service
      agents/           # AI research agents (Company Research Agent)
      tools/            # external tool integrations (search providers)
      intelligence/     # evidence collection and validation logic
    tests/              # Pytest unit + integration tests
    alembic/            # Alembic migrations (pgvector-compatible)
    requirements.txt
    .env.example
  frontend/             # Next.js App Router dashboard (JavaScript + Tailwind)
    app/                # App Router pages
    components/         # shadcn-style UI components
    lib/                # API client, utils
  infrastructure/       # Docker / Docker Compose (placeholder)
  docs/                 # architecture, agent-design, development-roadmap
  tasks/                # implementation plan & task list
  docker-compose.yml
```

## Technology stack

| Layer | Technology |
|-------|------------|
| Backend language | Python 3.11+ (running on 3.14 in this environment) |
| API framework | FastAPI |
| Multi-agent orchestrator | LangGraph (StateGraph) |
| Data validation | Pydantic |
| Database | SQLAlchemy 2.0 (async) + PostgreSQL + pgvector |
| Migrations | Alembic |
| LLM | OpenRouter-compatible factory; DeepSeek initial provider (configurable) |
| Frontend | Next.js App Router, JavaScript, Tailwind CSS, shadcn-style UI |
| Testing | Pytest |
| Infrastructure | Docker, Docker Compose |

## Phase 0 + Phase 1 scope (implemented)

- FastAPI application with centralized logging, exception handling, CORS, dependency injection, API versioning (`/api/v1`), request-size limiting.
- Environment-based configuration via Pydantic Settings (`backend/.env.example` → `.env`).
- Health-check endpoint: `GET /api/v1/health` (reports DB and LLM status honestly).
- Research endpoints:
  - `POST /api/v1/research` — accepts `company_name`, `industry`, `research_question` (+ optional `organization_id`); returns `research_id`, status, structured results.
  - `GET /api/v1/research/{research_id}` — status and results.
- LangGraph `StateGraph` with a typed Pydantic `ResearchState` and `Annotated` list reducers (`competitors`, `evidence`, `errors`, `execution_metadata`).
- Graph building (`graph/builder.py`) strictly separate from node logic (`graph/nodes/`).
- Eight nodes in the required order:
  `initialize_research → research_planner → company_researcher → competitor_discovery_mock → evidence_validator_mock → strategic_analyst_mock → report_generator_mock → finalize_research → END`.
  (`company_researcher` replaces the Phase 1 mock; `company_researcher_mock` is retained for back-compat and testing.)
- Execution metadata recorded per node (name, status, timestamps, duration, mock flag).
- Exception handling: nodes capture failures, record them in `errors`, and the run is never reported as successful when a node fails.
- Configurable, provider-independent LLM factory (OpenRouter-compatible); **no LLM calls in Phase 1**, lazy initialization (nothing at import time).
- SQLAlchemy async engine/session; Alembic initialized with a pgvector-compatible initial migration; degrades gracefully without PostgreSQL (never falsely reports a connection).
- LangGraph PostgreSQL checkpointing (`AsyncPostgresSaver` adapter; dedicated `checkpoints`/`checkpoint_writes` tables separate from business records; thread-based execution and resume).
- Pytest suite: 40 core tests (fallback mode, no DATABASE_URL) + 15 persistence/checkpoint tests (with DATABASE_URL) + ~23 Phase 2A tests = ~78 total covering startup, health, validation, research API, state, nodes, full graph, execution order, report generation, failure handling, missing LLM config, DB-unavailable behavior, repository operations, cross-organization isolation, migration correctness, checkpointing, search providers, schemas, evidence, agent behavior, and LangGraph integration.
- Minimal Next.js dashboard (see Frontend).
- Documentation: README, `docs/architecture.md`, `docs/agent-design.md`, `docs/development-roadmap.md`.

### Phase 2A: Real Company Research Agent

The `company_researcher` node runs `CompanyResearcherAgent`, which:

- Generates prioritized search queries across 10 company aspects (overview, HQ, founders, products, business model, target customers, industry, markets, financials, recent developments).
- Searches via a configurable provider (deterministic mock for offline/tests, or DuckDuckGo HTML for live free-tier search).
- Fetches source pages with SSRF protection, timeouts, and size limits.
- Extracts a structured `CompanyProfile` via the LLM (OpenRouter/DeepSeek) with Pydantic schema validation.
- Collects `Evidence` items with full provenance (source_url, source_title, source_domain, confidence, verification_status).
- Detects conflicts across sources; confidence is editorial (0–1), not statistical certainty.
- Persists company profiles and evidence claims to PostgreSQL (`company_profiles`, `evidence_claims` tables), organization-isolated.
- Degrades gracefully to a search-snippet-based profile (marked unverified) when no LLM is configured.

Database tables (migration `0002_company_profiles`):
- `company_profiles`: company profiles with organization ownership.
- `evidence_claims`: evidence items linked to company profiles, with provenance.

## Backend quick start

### 1. Create a virtual environment and install dependencies

```bash
cd backend
python -m venv .venv
# activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
# or (macOS/Linux)
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env as needed. DATABASE_URL and OPENROUTER_API_KEY are optional in
# Phase 1; the app runs in mock-agent mode without them.
```

### 3. (Optional) Initialize the database

If you set `DATABASE_URL` in `.env`, apply the Alembic migration to create the
researches schema:

```bash
alembic upgrade head
```

This step is optional — the application degrades gracefully without a database.

### 4. Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Verify

- Health: `GET http://localhost:8000/api/v1/health`
- API docs: `http://localhost:8000/api/v1/docs`
- Submit research: `POST http://localhost:8000/api/v1/research` with JSON body
  `{ "company_name": "...", "industry": "...", "research_question": "..." }`

## Frontend

The Next.js dashboard lives in `frontend/`. It communicates with the FastAPI backend at `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

> **Environment limitation:** This environment has no network access to the npm registry, so `npm install` could not be completed and the frontend could not be started here. The frontend code is complete and reviewed by inspection. To run it on a machine with network:
>
> ```bash
> cd frontend
> npm install
> npm run dev        # http://localhost:3000
> ```
>
> Then open the dashboard, submit a research request, and watch the LangGraph
  execution metadata and structured report render.

### Frontend scripts

| Script | Purpose |
|--------|---------|
| `npm run dev` | Start dev server on port 3000 |
| `npm run build` | Production build |
| `npm run start` | Start production server |
| `npm run lint` | ESLint |

## Testing (backend)

```bash
cd backend
# Without DATABASE_URL: core tests (fallback/in-memory mode)
pytest

# With DATABASE_URL: persistence/checkpoint/API + company persistence tests
DATABASE_URL=postgresql+asyncpg://acis_app:acis_dev_password@127.0.0.1:5432/acis_db pytest
```

All tests use deterministic mock data and make **no external API calls** and consume **no LLM credits**.

Search provider configuration (`.env`):
- `SEARCH_PROVIDER=mock` (default, no network, no credits) or `duckduckgo` (live free-tier search).
- `SEARCH_MAX_QUERIES` (default 8), `SEARCH_MAX_PAGES` (default 10), `DUCKDUCKGO_BASE_URL`.

## Alembic / database

Migrations live in `backend/alembic/`. To initialize/upgrade a PostgreSQL database:

```bash
cd backend
# set DATABASE_URL in .env first
alembic upgrade head
```

Without `DATABASE_URL`, the application starts normally and the health endpoint reports the database as unavailable. No connection is ever falsely reported as successful.

## Security notes

- No secrets are hardcoded; all come from environment variables.
- `.env` and `.env.*` are gitignored; only `.env.example` is tracked.
- CORS is restricted to configured origins (localhost by default).
- Request bodies are size-limited (default 4 MB).
- Errors return safe, generic messages to clients; internals are not leaked.
- Inputs are validated via Pydantic schemas.
- Organization ownership (`organization_id`) is modeled for future auth/RBAC and tenant isolation.

## License

Private / internal.
