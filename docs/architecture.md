# Architecture — ACIS Phase 0 + Phase 1 + Phase 1.5 + Phase 2A + Phase 2B

## Overview

ACIS is a modular monorepo. The backend is a FastAPI service orchestrating a LangGraph `StateGraph` of agents. Phase 2A adds real company research, and Phase 2B adds evidence-backed competitor discovery using the same search, LLM, and persistence infrastructure. The frontend is a Next.js App Router dashboard that calls the backend. No LLM calls are made during application import; no external API credits are consumed unless `OPENROUTER_API_KEY` and a live search provider are explicitly configured.

## High-level data flow

```
Client (Next.js)
     │  Sign in → short-lived bearer token + HttpOnly refresh cookie
     │  POST /api/v1/research + X-Organization-ID
     ▼
FastAPI (app/main.py)
     │
     ├─► Authentication + shared rate limiting
     │       ├─ Argon2id password verification
     │       ├─ JWT signature/expiry + persisted session status
     │       └─ Active organization membership + centralized RBAC
     │
     ├─► Research Service (services/research_service.py)
     │       ├─ builds initial ResearchState
     │       ├─ receives only trusted organization context
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

- `research_id` (unique, indexed), `organization_id` (indexed), encrypted `company_name`, `industry`, and `research_question`
- `status`, `review_status` (indexed), encrypted `results` and `errors` JSON payloads
- `created_at`, `updated_at` (timestamptz, server default `now()`)
- Composite index `(organization_id, status)` for org-scoped lookups

All repository queries filter by `organization_id`, so records are never exposed across organizations.

Migration `0004_identity_and_tenant_ownership` creates
`organizations`, `users`, `organization_memberships`, `organization_invitations`,
`auth_sessions`, `refresh_tokens`, `audit_events`, and `rate_limit_buckets`.
Migration `0005_encrypt_sensitive_payloads` encrypts existing research,
company, competitor, evidence, user-email, invitation-email, and checkpoint
payloads. Database query keys such as IDs, roles, status, timestamps, and
HMAC email lookup digests remain available to indexes; passwords and bearer or
refresh tokens are never stored in plaintext.

## LangGraph checkpointing

When `DATABASE_URL` is configured, `AsyncPostgresSaver` (from `langgraph-checkpoint-postgres`) provides PostgreSQL checkpoint storage in dedicated `checkpoints` / `checkpoint_writes` tables — SEPARATE from the business `researches` table.

- Thread-based execution: `config={"configurable": {"thread_id": "org:<organization-id>:research:<research-id>"}}`
- Checkpoints are stored per thread and can be retrieved for resume
- `AsyncPostgresSaver.setup()` creates the checkpoint tables at startup
- Checkpoint channel values, metadata, blobs, and writes use AES-GCM encryption;
  migration `0005_encrypt_sensitive_payloads` encrypts existing checkpoint rows.
  The organization namespace prevents an unscoped research ID from selecting
  another organization's thread.

Because the installed `PostgresSaver` exposes working sync methods but raises `NotImplementedError` on its async tuple methods, `app/core/checkpoint.py::AsyncPostgresSaver` wraps `get_tuple`/`put`/`put_writes` in `asyncio.to_thread` so LangGraph's `ainvoke` can checkpoint and resume.

## Database degradation

Without `DATABASE_URL`, the application starts normally and `db.health_check()`
reports `available: false`. Direct service/unit tests may use the process-local
fallback store, but the authenticated API is unavailable because identity,
membership, rate-limit, audit, persistence, and checkpoint checks require
PostgreSQL. No API request silently falls back to unauthenticated access.

## LLM abstraction

`LLMFactory` builds provider-independent clients (OpenRouter-compatible; DeepSeek default). Configured entirely from environment. No initialization at module import time. Phase 1/1.5: mock agents never call the LLM. Invoking the client without an API key raises `LLMConfigurationError` — no credits can be consumed accidentally.

## Security

- Input validation via Pydantic (min/max lengths, non-empty).
- Environment-based secrets; none hardcoded; none in Git.
- Restricted CORS (configured origins, no wildcard).
- Research, profile, competitor, and evidence lookups remain organization-filtered in repositories and are additionally guarded by active user membership and RBAC. Client-supplied research organization IDs are rejected.
- Platform administrators are provisioned by `python -m app.cli bootstrap-admin`; ordinary users join via hashed, expiring, single-use invitations. Organization creation issues the initial owner invitation.
- Organization permission matrix (all checks are server-side):

  | Permission | Owner | Admin | Analyst | Viewer |
  |---|---:|---:|---:|---:|
  | Manage users/invitations | Yes | Yes | No | No |
  | Manage organization/configuration | Yes | No | No | No |
  | Create/view/delete research | Yes | Yes | Create/view | View |
  | Manage competitors/evidence | Yes | Yes | Yes | No |
  | View strategy reports | Yes | Yes | Yes | Yes |

  Platform administrators use separate control-plane dependencies for organization creation and bootstrap administration; platform status does not bypass organization membership on research endpoints.
- Passwords use Argon2id. Access JWTs expire quickly and every request checks session status; refresh tokens are stored as SHA-256 digests, rotated once, and replay revokes the session. Refresh uses an HttpOnly cookie plus double-submit CSRF and Origin checks.
- User and invitation emails, research results, profiles, claims/snippets, and all checkpoint payload components are AES-256-GCM encrypted. Email lookup uses a separate HMAC key. Email HMAC key rotation requires re-indexing lookup hashes; AES key rotation retains old key IDs until re-encryption.
- PostgreSQL-backed rate-limit buckets and API audit events are shared across workers. The API applies an IP limit before authentication, plus account-specific login and authenticated-user limits. Request bodies are bounded even without a content-length header; error validation omits submitted values, and audit records do not store request bodies. Configure trusted-proxy client-IP handling at deployment; the app does not trust arbitrary forwarded-IP headers.
- Root, health, login, refresh, and invitation acceptance are public by design; organization listing and business operations require authentication. API docs/OpenAPI are disabled in production.
- Production requires `DEBUG=false`, configured signing and email lookup keys, a valid encryption keyring, secure cookies, a database, and restricted CORS. TLS 1.3 and optional mTLS are deployment responsibilities: terminate TLS at a trusted reverse proxy/service mesh that rejects weaker TLS, and restrict direct backend access. Local HTTP does not prove TLS enforcement.
- Bearer access tokens can be replayed until expiry or revocation; short TTL and session checks limit this exposure but do not prevent replay of a still-valid stolen access token.
- Page fetching resolves DNS once per request, rejects the request if any returned address is non-public, and connects to a vetted IP literal while preserving the original HTTP Host header and HTTPS SNI/certificate hostname. Redirects are followed manually and each destination is resolved and checked again. This closes the DNS-rebinding gap between a separate preflight lookup and HTTP client's connection-time lookup.
- DNS pinning is implemented at the HTTP request layer; it relies on the configured HTTPX client/httpcore honoring the pinned literal URL and TLS `sni_hostname` extension. Changes to custom transports or proxy configuration require renewed SSRF validation.

### Phase 2D database setup and verification

Migrations `0004_identity_and_tenant_ownership` and
`0005_encrypt_sensitive_payloads` add identity/ownership controls and encrypt
existing sensitive columns and checkpoint rows. The encryption migration is
intentionally one-way; restore a verified backup and run an approved decrypt
migration rather than downgrading encrypted records to plaintext.

For persistence, authentication, rate-limit, and checkpoint tests, create a
dedicated PostgreSQL database whose name contains a delimited `test` component.
Set `ACIS_TEST_DATABASE_URL` and `DATABASE_URL` to that database, then configure
test-only `AUTH_JWT_SIGNING_KEY`, `AUTH_EMAIL_LOOKUP_KEY`,
`DATA_ENCRYPTION_ACTIVE_KEY_ID`, and `DATA_ENCRYPTION_KEYS`. Use the same
encryption keyring for `alembic upgrade head` and the test process. The pytest
guard rejects non-PostgreSQL or non-test database names and refuses missing
encryption/authentication keys. Never run these migrations or destructive
tests against development or production data.

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

Next.js App Router, JavaScript, Tailwind CSS, shadcn-style components. Calls `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`). Signs in through the public auth endpoint, restores sessions through CSRF-protected refresh, selects one of the user's validated memberships, and sends bearer and organization headers for research submission and retrieval.

> The environment used to build this phase has no working `npm install` path to the npm registry (tarball downloads hang), so the frontend could not be `npm install`ed or started here. Frontend verification (dev server, production build, e2e research) is therefore documented as a limitation, not a claimed result.
