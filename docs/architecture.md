# Architecture — ACIS Phase 0 + Phase 1 + Phase 1.5 + Phase 2A + Phase 2B

## Overview

ACIS is a modular monorepo. The backend is a FastAPI service orchestrating a LangGraph `StateGraph` of agents. Phase 2A adds real company research, and Phase 2B adds evidence-backed competitor discovery using the same search, LLM, and persistence infrastructure. The frontend is a Next.js App Router dashboard that calls the backend. No LLM calls are made during application import; no external API credits are consumed unless `OPENROUTER_API_KEY` and a live search provider are explicitly configured.

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
     │       │   ├─ company_researcher
     │       │   ├─ competitor_discovery
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
| `app/core/llm.py` | Provider-independent LLM factory (OpenRouter-compatible), lazy; real HTTP client with structured Pydantic output |
| `app/agents/base.py` | Base agent: search budgeting, rate limiting, result caching, DNS-pinned SSRF-safe URL validation, HTTP fetch with size limits/timeouts |
| `app/agents/company_researcher.py` | Company Research Agent: query generation → search → retrieval → LLM extraction → evidence → validation → profile |
| `app/agents/competitor_researcher.py` | Competitor discovery: shared research results → bounded search → extraction → source validation → overlap scoring |
| `app/tools/search/base.py` | Abstract `SearchProvider` interface |
| `app/tools/search/schemas.py` | `SearchResult`, `SearchQuery` Pydantic schemas |
| `app/tools/search/providers/mock.py` | Deterministic mock provider (offline, no network, no credits) |
| `app/tools/search/providers/duckduckgo.py` | DuckDuckGo HTML provider (free, no API key, SSRF-protected) |
| `app/schemas/company.py` | `CompanyProfile`, `CompanySize` Pydantic schemas |
| `app/schemas/evidence.py` | `Evidence`, `EvidenceCollection`, `EvidenceType`, `VerificationStatus` |
| `app/intelligence/evidence.py` | Evidence collection, confidence scoring, conflict detection, source classification |
| `app/models/company.py` | `CompanyProfile`, `EvidenceClaim` SQLAlchemy ORM models |
| `app/repositories/company.py` | `CompanyRepository` with server-side organization isolation |
| `app/repositories/evidence.py` | `EvidenceRepository` with server-side organization isolation |
| `app/schemas/competitor.py` | Typed competitor classifications, factor values, and source evidence |
| `app/models/competitor.py` | Organization/research-owned competitor and evidence records |
| `app/repositories/competitor.py` | Organization-scoped competitor access and idempotent persistence support |
| `app/graph/state.py` | Typed Pydantic `ResearchState` with `Annotated` list reducers |
| `app/graph/nodes/` | Graph node implementations; `company_researcher` replaces `company_researcher_mock` |
| `app/graph/builder.py` | StateGraph construction (optional checkpointer), separate from node logic |
| `app/services/research_service.py` | Orchestrates graph execution; repository-backed persistence with fallback store |

## State (`ResearchState`)

A Pydantic model carried through every node. List fields use `Annotated[T, operator.add]` reducers so values accumulate across nodes instead of being overwritten.

The `company_researcher` node adds its normalized `search_results` to state.
`competitor_discovery` reuses these results and evidence before making bounded
additional searches.

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
- Page fetching resolves DNS once per request, rejects the request if any returned address is non-public, and connects to a vetted IP literal while preserving the original HTTP Host header and HTTPS SNI/certificate hostname. Redirects are followed manually and each destination is resolved and checked again. This closes the DNS-rebinding gap between a separate preflight lookup and HTTP client's connection-time lookup.
- DNS pinning is implemented at the HTTP request layer; it relies on the configured HTTPX client/httpcore honoring the pinned literal URL and TLS `sni_hostname` extension. Changes to custom transports or proxy configuration require renewed SSRF validation.

## Company Research Agent pipeline (Phase 2A)

The `company_researcher` node runs the CompanyResearcherAgent through this pipeline:

```

## Competitor Discovery Agent pipeline (Phase 2B)

```
Company profile, evidence, and reused search results
    ↓
Product/service and market/customer analysis
    ↓
Prioritized direct/indirect/emerging/substitute search
    ↓
Bounded external search and candidate extraction
    ↓
Exact-source attribution, deduplication, and evidence checks
    ↓
Weighted overlap scoring and category qualification
    ↓
Ranked profiles and PostgreSQL persistence
```

Qualification weights are product 0.20, service 0.15, customer 0.20,
problem-space 0.20, geography 0.10, business model 0.10, and market positioning
0.05. Each factor is a Jaccard keyword-overlap value; unavailable evidence is
listed as unknown and contributes zero. Classification requires overlap evidence; weak
or unrelated companies are excluded rather than automatically categorized as
substitutes. Emerging status requires a recent-entry/growth signal in source
text. Exact claims corroborated across sources are marked partially verified;
conflicting source claims are retained with a conflicting status. Source URLs
are accepted only from retrieved results, and page fetching
blocks non-public addresses and revalidates redirects. Official company sites,
regulatory filings, investor relations, press releases, industry reports, and
credible publications are prioritized for profile evidence.

Competitors and their evidence are stored in `competitors` and
`competitor_evidence`. The schema scopes records to both organization and
research, links competitors to their owning research, and uses a composite
foreign key for evidence ownership. `company_key` prevents case/punctuation
variants from duplicating a company within one research context.
Research Request
    ↓
Search Query Generation
    ↓
External Search (mock or DuckDuckGo)
    ↓
Source Retrieval (SSRF-protected, size-limited, timed)
    ↓
Information Extraction (LLM → structured Pydantic output)
    ↓
Evidence Collection (provenance: source_url, title, domain, confidence, status)
    ↓
Validation (conflict detection across sources)
    ↓
Structured Company Profile
    ↓
PostgreSQL Persistence (organization-isolated)
```

Key behaviors:
- **Search queries**: 10 prioritized aspects (overview, HQ, founders, products, business model, target customers, industry, markets, financials, recent developments).
- **Budgeting**: configurable `max_search_queries`, `max_pages_fetched`, `max_llm_calls`, `max_retries`, `max_tokens_per_llm_call`.
- **Caching**: search results cached within a research run to avoid duplicate searches.
- **Rate limiting**: minimum interval between search requests.
- **SSRF protection**: page fetches reject non-public DNS answers, connect to a vetted IP literal while preserving the original Host/SNI, and manually validate each redirect destination. This prevents DNS rebinding between hostname validation and connection. See the HTTPX transport/proxy limitation below.
- **No fabricated citations**: unavailable information is `None`/empty, never invented.
- **Confidence is editorial**: not statistical certainty; ranges 0–1.
- **Verification status**: `verified`, `partially_verified`, `conflicting`, `unverified`.
- **Fallback**: without LLM config, builds a search-snippet-based profile marked unverified.

## Persistent storage: company profiles and evidence

When `DATABASE_URL` is configured, two additional tables are created by migration `0002_company_profiles`:

- `company_profiles`: `company_id` (unique), `organization_id` (indexed), `company_name`, `industry`, `profile` (JSON), `website`, `source_references`, timestamps.
- `evidence_claims`: `evidence_id` (unique), `company_profile_id` (FK → company_profiles), `organization_id` (indexed), `claim`, `source_url`, `source_title`, `source_domain` (indexed), `published_at`, `retrieved_at`, `evidence_type`, `confidence`, `verification_status`, `raw_snippet`.

All repository queries filter by `organization_id`, so records are never exposed across organizations.

## Frontend

Next.js App Router, JavaScript, Tailwind CSS, shadcn-style components. Calls `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`). Includes a research submission form, status polling, execution-metadata display, and structured report rendering.

> The environment used to build this phase has no working `npm install` path to the npm registry (tarball downloads hang), so the frontend could not be `npm install`ed or started here. Frontend verification (dev server, production build, e2e research) is therefore documented as a limitation, not a claimed result.
