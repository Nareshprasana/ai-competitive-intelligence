# AI Competitive Intelligence System (ACIS)

A production-oriented AI Competitive Intelligence system built with **LangGraph**, **FastAPI**, **PostgreSQL + pgvector**, and **Next.js**. Phase 0 + Phase 1 deliver a functioning multi-agent backend with deterministic mock agents (no LLM credits consumed). Phase 1.5 adds persistent research storage (PostgreSQL + SQLAlchemy repositories + Alembic migrations) and LangGraph PostgreSQL checkpointing. Phase 2A replaces the mock company researcher with a real AI-powered Company Research Agent that investigates real companies via search + LLM extraction, attaches evidence with provenance, and persists to PostgreSQL. A minimal Next.js dashboard talks to the real backend.

> **Status:** Phases 0, 1, 1.5, 2A, 2B, and 2C are implemented. Phase 2D adds authentication, RBAC, tenant-scoped API access, encrypted persistence, and an authenticated dashboard. PostgreSQL migration and integration verification remain pending a dedicated test database.

## Repository structure

```
ai-competitive-intelligence/
  backend/              # FastAPI + LangGraph backend (Python)
    app/
      core/             # config, logging, exceptions, database, LLM factory, checkpoint
      security/         # authentication, RBAC, encryption, tenant context
      api/v1/           # public health/auth flows and protected research APIs
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
- Authentication is invite-only: bootstrap the first platform administrator with `python -m app.cli bootstrap-admin`, create an organization, then issue an owner invitation. Access tokens are short-lived; refresh tokens rotate in HttpOnly cookies.
- Protected research endpoints:
  - `POST /api/v1/research` — accepts `company_name`, `industry`, and `research_question`; requires a bearer access token, organization membership, and `X-Organization-ID`.
  - `GET /api/v1/research/{research_id}` — returns records only when the selected organization owns them.
- LangGraph `StateGraph` with a typed Pydantic `ResearchState` and `Annotated` list reducers (`competitors`, `evidence`, `errors`, `execution_metadata`).
- Graph building (`graph/builder.py`) strictly separate from node logic (`graph/nodes/`).
- Eight nodes in the required order:
  `initialize_research → research_planner → company_researcher → competitor_discovery → evidence_validator_mock → strategic_analyst_mock → report_generator_mock → finalize_research → END`.
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

The authenticated API requires PostgreSQL. Configure the database and generate
separate authentication, email-lookup, and encryption keys before applying
migrations. `0005_encrypt_sensitive_payloads` rewrites sensitive persisted
values and requires the encryption keyring to be available:

```bash
alembic upgrade head
```

Direct local service tests can still run without PostgreSQL, but API research,
authentication, rate limiting, audit events, and checkpointing require the
database.

### 4. Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Verify

- Health: `GET http://localhost:8000/api/v1/health`
- API docs: `http://localhost:8000/api/v1/docs`
- Sign in: `POST http://localhost:8000/api/v1/auth/login`; use the returned
  bearer token and select a membership from `GET /api/v1/auth/organizations`.
- Submit research with `Authorization: Bearer <access-token>` and
  `X-Organization-ID: <member-organization>`; the request body cannot set an
  organization ID.

The dashboard signs in and selects a validated organization. Refresh tokens
remain in HttpOnly cookies; the short-lived access token stays in browser
memory. A non-secret CSRF token is kept in session storage/local browser state
and is paired with an Origin check on refresh.

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

## Developer workflow: Graphify + Ponytail

Project-level Copilot guidance in [.github/copilot-instructions.md](./.github/copilot-instructions.md) combines Graphify architecture queries with Ponytail's minimal-change principles. Graphify is installed as an isolated CLI (`uv tool install graphifyy`), not an ACIS runtime dependency. Query the graph before tracing existing code, then verify important relationships in source and tests:

```powershell
graphify query "How does research submission reach LangGraph execution?"
graphify path "run_research()" "ResearchRepository"
graphify explain "CompetitorResearcherAgent"
graphify update .
```

Tracked outputs are in `graphify-out/`: `graph.json`, `GRAPH_REPORT.md`, and `graph.html`. The graph includes code and selected architecture Markdown documents; it excludes secrets/environment files, dependencies, caches, build output, database/user data, and the user-maintained task plans listed in `.graphifyignore`. Graphify can infer relationships and omit unsupported files; it is a navigation aid, not a substitute for source inspection. Detailed install, query, refresh, scope, and verification notes are in [docs/development-roadmap.md](./docs/development-roadmap.md).

## Testing (backend)

```powershell
cd backend
# Core/unit tests run offline; PostgreSQL-backed tests skip unless explicitly configured.
python -m pytest

# PostgreSQL tests: create a dedicated acis_test database; never use development
# or production data. Supply test-only keys and use the same encryption keyring
# for migration and pytest.
$env:ACIS_TEST_DATABASE_URL = "postgresql+asyncpg://<user>:<password>@localhost:5432/acis_test"
$env:DATABASE_URL = $env:ACIS_TEST_DATABASE_URL
$env:AUTH_JWT_SIGNING_KEY = "<test-only-random-secret-at-least-32-characters>"
$env:AUTH_EMAIL_LOOKUP_KEY = "<test-only-random-secret-at-least-32-characters>"
$env:DATA_ENCRYPTION_ACTIVE_KEY_ID = "test-key"
$env:DATA_ENCRYPTION_KEYS = '{"test-key":"<base64-encoded-32-byte-test-key>"}'
alembic upgrade head
python -m pytest -q tests/unit tests/integration
```

The test harness rejects non-PostgreSQL URLs and database names without a delimited `test` component. It ignores `.env`/`DATABASE_URL` when no `ACIS_TEST_DATABASE_URL` is set and overrides `DATABASE_URL` with the dedicated test URL when it is set. Never use a development or production database for these tests. Do not commit credentials.

All tests use deterministic mock data and make **no external API calls** or consume **no LLM credits**.
Search provider configuration (`.env`): `SEARCH_PROVIDER=mock` (default, offline) or `duckduckgo` (live); `SEARCH_MAX_QUERIES` (default 8), `SEARCH_MAX_PAGES` (default 10), and `DUCKDUCKGO_BASE_URL`.

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
- Organization-owned APIs require a valid access token and an active membership selected through `X-Organization-ID`. The organization ID is never accepted from the research payload.
- Passwords use Argon2id. Access tokens are short-lived JWTs and each request checks the active session; refresh tokens are stored as hashes, rotated on use, and replay revokes the session.
- Roles are `organization_owner`, `organization_admin`, `analyst`, and `viewer`; permission checks are centralized and server-side. Platform administrator actions are global and require the bootstrap role.
- Research/profile/evidence payloads and user/invitation emails use AES-256-GCM. Email lookup uses a separate HMAC key. Password hashes and refresh/invitation token digests are one-way hashes.
- Rate-limit counters and audit events are PostgreSQL-backed. Request bodies are size-limited (default 4 MB), correlation IDs are returned, validation errors omit submitted values, and audit records do not include request bodies.
- Production requires non-default JWT and email lookup keys, an externally managed AES keyring, secure cookies, a database, restricted CORS, and `DEBUG=false`. Keep old AES key IDs configured until data is re-encrypted. Rotate the email HMAC key only with a coordinated lookup-hash migration.
- TLS 1.3 and optional mTLS must be enforced at the deployment reverse proxy/service mesh; the local FastAPI server does not establish that guarantee. Put the API behind a proxy that terminates TLS 1.3, rejects weaker protocols, and overwrites forwarded headers. Restrict PostgreSQL and checkpoint DB network access.
- Refresh rotation and session revocation limit replay, but an already-issued bearer access token can be replayed until expiry or session revocation. Keep access TTL short and protect client devices.
- PostgreSQL migrations `0004` and `0005` and their persistence/checkpoint tests were not run in this environment. Only apply them to a dedicated test database first; never use a development or production DB as a disposable test target.

## License

Private / internal.
