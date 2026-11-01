# AI Competitive Intelligence System (ACIS)

A production-oriented AI Competitive Intelligence system built with **LangGraph**, **FastAPI**, **PostgreSQL + pgvector**, and **Next.js**. Phase 0 + Phase 1 deliver a functioning multi-agent backend with deterministic mock agents (no LLM credits consumed) and a minimal dashboard that talks to the real backend.

> **Status:** Phase 0 + Phase 1 complete (backend fully tested; frontend code complete — see "Frontend" below).

## Repository structure

```
ai-competitive-intelligence/
  backend/              # FastAPI + LangGraph backend (Python)
    app/
      core/             # config, logging, exceptions, database, LLM factory
      api/v1/           # versioned endpoints (health, research)
      graph/            # LangGraph state, nodes, builder
      schemas/          # Pydantic request/response schemas
      services/         # research orchestration service
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
- Eight deterministic mock nodes in the required order:
  `initialize_research → research_planner → company_researcher_mock → competitor_discovery_mock → evidence_validator_mock → strategic_analyst_mock → report_generator_mock → finalize_research → END`.
- Execution metadata recorded per node (name, status, timestamps, duration, mock flag).
- Exception handling: nodes capture failures, record them in `errors`, and the run is never reported as successful when a node fails.
- Configurable, provider-independent LLM factory (OpenRouter-compatible); **no LLM calls in Phase 1**, lazy initialization (nothing at import time).
- SQLAlchemy async engine/session; Alembic initialized with a pgvector-compatible initial migration; degrades gracefully without PostgreSQL (never falsely reports a connection).
- Pytest suite: 40 tests covering startup, health, validation, research API, state, nodes, full graph, execution order, report generation, failure handling, missing LLM config, DB-unavailable behavior.
- Minimal Next.js dashboard (see Frontend).
- Documentation: README, `docs/architecture.md`, `docs/agent-design.md`, `docs/development-roadmap.md`.

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

### 3. Run the server

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
pytest                    # run the full suite (40 tests)
pytest -q                 # quieter output
```

All tests use deterministic mock data and make **no external API calls** and consume **no LLM credits**.

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
