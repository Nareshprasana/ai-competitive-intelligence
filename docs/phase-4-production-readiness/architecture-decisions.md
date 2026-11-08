# ACIS Architecture Decision Records (ADRs)

**Project:** AI Competitive Intelligence System (ACIS)  
**Document:** Architecture Decision Records (ADR-001 through ADR-009)  
**Target Release:** Phase 4 Production Foundation  
**Status:** Validated Architecture Specification  
**Date:** November 2026

---

## ADR-001: Frontend Runtime (Node.js LTS) and Next.js Framework Modernization Strategy

### Status: Accepted
### Context
The existing ACIS frontend is built on Next.js 14.2.17 and React 18.3.1. In late 2026, Next.js 14 is outside official maintenance and support policies. Furthermore, previous drafts mentioned Node.js 20 (which reached official End-of-Life on April 30, 2026) and Node.js 22 (which is entering maintenance in late 2026 and reaches EOL in April 2027). Running an unsupported framework or runtime in production creates serious security compliance violations, unpatched V8/OpenSSL risks, and library deprecation blockers.

Official Node.js Release Lifecycle Status:
- **Node.js 26:** Released April 2026; Current/LTS transition October 2026. **Preferred primary long-term runtime.**
- **Node.js 24:** Active LTS (October 2025 – October 2027; EOL April 2028). Conservative, thoroughly tested alternative.
- **Node.js 22:** Maintenance LTS (EOL April 30, 2027). **Explicitly disqualified as the primary long-term recommendation.**
- **Node.js 20:** End-of-Life (April 30, 2026). Strictly prohibited.

Next.js Framework Modernization Matrix:
- **Next.js 16:** **Preferred modernization target.** Features full React 19 stabilization, Partial Prerendering (PPR), Turbopack production builds, and advanced Server Actions caching.
- **Next.js 15:** Intermediate milestone if upstream peer dependencies temporarily block direct Next.js 16 adoption. Introduces async request headers (`await cookies()`, `await headers()`), uncached `fetch` by default, and React 19.

### Decision
1. **Separation of Architectural Gates:**
   - **Gate A (Temporary Local Infrastructure Testing — Phase 4A):** For initial Docker Compose packaging and containerization in Phase 4A only, Next.js 14.2.17 is temporarily permitted to run on **Node.js 24 LTS or Node.js 26 Alpine** (`node:24-alpine` / `node:26-alpine`) in `output: 'standalone'` mode. This allows local container testing without conflating infrastructure changes with code refactoring.
   - **Gate B (Mandatory Production Deployment Gate):** **Next.js 14 is strictly disqualified from production deployment.** Production deployment is blocked until the frontend is modernized to **Next.js 16** (or Next.js 15 as an intermediate step if technically required) with **React 19**, and verified across all unit, integration, and E2E suites.
2. **Framework Migration Requirements:**
   - Audit and refactor asynchronous request handling (`cookies()`, `headers()` as Promises).
   - Update `fetch` caching semantics from Next.js 14 default caching to Next.js 15/16 explicit caching.
   - Validate React 19 compatibility across all custom UI components and Lucide icons.
   - Preserve all existing authentication flows, CSRF token handling, HttpOnly cookie reception, tenant header propagation, and Playwright/Node test suites.

### Consequences
- **Positive:** Guarantees that production systems run only on supported, actively patched software; eliminates premature tech debt.
- **Negative:** Establishes a mandatory frontend modernization workstream before commercial production deployment.

---

## ADR-002: Durable LangGraph Execution Architecture (PostgreSQL Transactional Queue)

### Status: Accepted
### Context
The current ACIS research workflow executes synchronously inside the FastAPI HTTP route handler (`research_service.run_research`). With live LLM providers (OpenRouter/DeepSeek) and web scrapers, a complete research run takes **30 to 120+ seconds**. Synchronous execution causes:
1. Reverse proxy HTTP gateway timeouts (typically 60s).
2. Browser connection timeouts.
3. Thread/process starvation in the ASGI server.
4. Total loss of in-flight research state if a client disconnects or container restarts.

FastAPI `BackgroundTasks` executes in ephemeral process memory: an unhandled exception, OOM restart, or deployment SIGTERM permanently destroys queued and running jobs without recovery.

### Decision
Implement a **Durable Asynchronous Worker Architecture** using a **PostgreSQL-backed transactional queue (`research_jobs`)** and a dedicated worker process (`python -m app.workers.research_worker`):
1. `POST /api/v1/research` inserts a `research_records` row and a `research_jobs` row (`status = 'pending'`) in a single ACID transaction, returning HTTP 202 Accepted with `research_id` and `job_id` in <100ms.
2. A separate background worker process claims jobs using `SELECT ... FOR UPDATE SKIP LOCKED`.
3. The worker executes the LangGraph `StateGraph` workflow, persisting incremental node checkpoints via `AsyncPostgresSaver`.
4. The frontend polls `GET /api/v1/research/{id}` for state updates until the terminal state (`completed` or `failed`) is reached.

### Alternatives Considered
- **Redis + ARQ / Celery:** Rejected for initial production. Adds external stateful infrastructure (Redis container), extra memory overhead (~150MB), backup management, and dual-store consistency hazards between Redis and PostgreSQL.
- **RabbitMQ:** Rejected. Extreme operational complexity and maintenance overhead for current scale.

### Consequences
- **Positive:** Zero new broker infrastructure; 100% ACID consistency between job state and research state; survives container crashes.
- **Negative:** Requires implementing worker claiming logic, heartbeats, and queue tables.

---

## ADR-003: PostgreSQL-Backed Job Lifecycle, Heartbeats, and Stale Lease Recovery

### Status: Accepted
### Context
A durable queue without external brokers must reliably manage concurrency, worker heartbeats, crash recovery, and bounded retries.

### Decision
1. **Schema Definition (`research_jobs`):**
   - `id` (UUID, Primary Key)
   - `research_id` (VARCHAR, Foreign Key to `research_records`, Indexed)
   - `organization_id` (VARCHAR, Indexed for Tenant Isolation)
   - `status` (`pending`, `running`, `completed`, `failed`, `cancelled`)
   - `worker_id` (VARCHAR, identifying claiming worker)
   - `fence_token` (BIGINT, monotonic lease counter)
   - `attempt_count` (INT, default 0)
   - `max_attempts` (INT, default 3)
   - `lease_expires_at` (TIMESTAMPTZ, updated via heartbeats)
   - `scheduled_at` (TIMESTAMPTZ, default `NOW()`)
   - `created_at`, `started_at`, `completed_at` (TIMESTAMPTZ)
   - `error_details` (JSONB)
   - `idempotency_key` (VARCHAR, Unique Index per tenant + hash)
2. **Atomic Claiming with Lease Ownership:**
   ```sql
   WITH next_job AS (
     SELECT id FROM research_jobs
     WHERE status = 'pending' AND scheduled_at <= NOW()
     ORDER BY created_at ASC
     LIMIT 1
     FOR UPDATE SKIP LOCKED
   )
   UPDATE research_jobs
   SET status = 'running',
       worker_id = :worker_id,
       fence_token = fence_token + 1,
       attempt_count = attempt_count + 1,
       started_at = NOW(),
       lease_expires_at = NOW() + INTERVAL '30 seconds'
   FROM next_job
   WHERE research_jobs.id = next_job.id
   RETURNING research_jobs.*;
   ```
3. **Heartbeat & Lease Renewal:** The worker maintains an asynchronous heartbeat loop every 10–15 seconds:
   ```sql
   UPDATE research_jobs
   SET lease_expires_at = NOW() + INTERVAL '30 seconds'
   WHERE id = :job_id AND worker_id = :worker_id AND fence_token = :fence_token;
   ```
4. **Stale Lease Reclamation:** A supervisor task runs every 30 seconds:
   ```sql
   UPDATE research_jobs
   SET status = CASE WHEN attempt_count >= max_attempts THEN 'failed' ELSE 'pending' END,
       worker_id = NULL,
       scheduled_at = NOW() + (INTERVAL '5 seconds' * attempt_count),
       error_details = jsonb_build_object('error', 'Worker lease expired; reclaimed for retry')
   WHERE status = 'running' AND lease_expires_at < NOW();
   ```

### Consequences
- **Positive:** Bounded retries with backoff; automatic self-healing after worker container crashes.

---

## ADR-004: Production Secrets and KMS/Vault Key Management Strategy

### Status: Accepted
### Context
ACIS handles confidential enterprise intelligence across four distinct categories of secrets:
1. Database credentials (`DATABASE_URL`).
2. Authentication token signing keys (`AUTH_JWT_SIGNING_KEY`, `AUTH_EMAIL_LOOKUP_KEY`).
3. Sensitive data encryption keys (`DATA_ENCRYPTION_KEYS`, `DATA_ENCRYPTION_ACTIVE_KEY_ID`).
4. External provider API keys (`OPENROUTER_API_KEY`).

### Decision
1. **Separation of Concerns:** Each category of secret is managed independently with dedicated rotation procedures.
2. **KMS / HSM Key Protection Requirement:** For production environments, the master key protecting `DATA_ENCRYPTION_KEYS` (AES-256-GCM) must be secured by an external **KMS (Key Management Service)**, **Hardware Security Module (HSM)**, or **HashiCorp Vault**. Application containers receive decrypted envelope keys into memory only at startup.
3. **Container Secret Injection:**
   - **Initial Host VPS Deployment:** Docker Compose secrets or protected host environment files (`/opt/acis/.env.production`) restricted to `chmod 0600 root:root`.
   - **Managed Cloud Deployment:** Transition to native cloud secret managers (AWS Secrets Manager, GCP Secret Manager, or Infisical).
4. **Zero-Secret Invariant:** No secret values may ever be committed to Git, baked into container images, or output in application logs.

---

## ADR-005: Cookie Security, CSRF Defense-in-Depth, and Ingress Security Headers

### Status: Accepted
### Context
Cookie security and CSRF defense must be rigorous and grounded in defense-in-depth principles.

### Decision
1. **Cookie Defense-in-Depth (`SameSite=Strict`):**
   - Refresh token cookies enforce: `HttpOnly: true`, `Secure: true`, and `SameSite: Strict`.
   - **Explicit Clarification:** `SameSite=Strict` is a **defense-in-depth layer, NOT a replacement for CSRF protection**. ACIS mandates:
     - Strict `X-CSRF-Token` header validation for all state-changing API endpoints.
     - Strict `Origin` and `Referer` header validation against `BACKEND_CORS_ORIGINS`.
     - Refresh token rotation on every issuance.
     - Replay detection and immediate session revocation if an expired or revoked token is reused.
2. **TLS 1.3 Termination:** The edge proxy terminates TLS using modern ciphers, mandating TLS 1.3 (with TLS 1.2 fallback).
3. **HSTS Preload Policy:** 
   - **Do NOT enable HSTS preload automatically.**
   - Initial production will set: `Strict-Transport-Security: max-age=31536000; includeSubDomains`.
   - The `preload` directive will only be added after 90 days of stable HTTPS operation across the root domain and all subdomains, following formal submission to `hstspreload.org`.
4. **CSP Strategy (Report-Only First):**
   - Deploy `Content-Security-Policy-Report-Only` during staging and the first 30 days of production.
   - Enforce strict blocking `Content-Security-Policy` only after report logs confirm zero false positives.

---

## ADR-006: Container Base Image Pinning and Vulnerability Patch Policy

### Status: Accepted
### Context
Using `:latest` or unpinned tags creates non-deterministic builds and security vulnerabilities.

### Decision
1. **Strict Tag Pinning:** Production container images must be pinned to explicit patch versions and Debian/Alpine release codenames:
   - **Backend & Worker:** `python:3.12-slim-bookworm` or `python:3.11-slim-bookworm`.
   - **Frontend:** `node:24-alpine` (conservative) or `node:26-alpine` (preferred long-term).
   - **PostgreSQL:** `pgvector/pgvector:0.8.0-pg18` (see ADR-009).
   - **Reverse Proxy:** `caddy:2.9-alpine` or `nginx:1.27-alpine`.
2. **Digest Verification Policy:** In production release manifests, images must be pinned to immutable `@sha256:...` digests discovered dynamically during the CI/CD build pipeline (never invented arbitrary hashes).
3. **Vulnerability Patch Policy:**
   - Base images scanned weekly via Trivy in GitHub Actions.
   - Patch-level security updates reviewed and deployed on a monthly cadence.
   - Critical CVEs (CVSS >= 9.0) trigger an expedited out-of-band rebuild and redeployment within 48 hours.

---

## ADR-007: Fencing Tokens, Stale Worker Overwrite Prevention, and At-Least-Once LangGraph Semantics

### Status: Accepted
### Context
In distributed background execution, network pauses, long garbage collection pauses, or temporary worker stalls can cause a worker's lease to expire while the worker is still running. The supervisor may reclaim the job and assign it to a second worker. If the original ("zombie") worker recovers and attempts to write results or checkpoints, it could overwrite newer, valid state.

Furthermore, distributed workflow execution cannot promise *exactly-once* execution. Network timeouts between the worker and external LLM APIs (OpenRouter/DeepSeek) mean that a node may be partially executed before an interruption occurs.

### Decision
1. **At-Least-Once Execution with Idempotent Effects:**
   - ACIS explicitly designs for **at-least-once execution with idempotent effects**, not an unrealistic exactly-once promise.
   - LangGraph nodes must check existing state/checkpoints before dispatching external side effects (e.g. LLM API calls, web searches, artifact writes). If an output artifact or step result already exists for the current node execution, the node reuses the existing result instead of incurring duplicate costs or side effects.
2. **Monotonic Fencing Tokens:**
   - Every job claim or reclamation increments the integer `fence_token` on `research_jobs`.
   - When a worker updates job progress, saves checkpoints, or marks completion, the database query MUST include:
     ```sql
     UPDATE research_jobs
     SET status = :status, error_details = :error_details, completed_at = NOW()
     WHERE id = :job_id AND fence_token = :worker_fence_token;
     ```
   - If the update affects 0 rows, the worker detects that its lease was revoked and its fence token superseded. The worker immediately aborts execution without modifying research records or artifact storage.
3. **LangGraph Checkpoint Resumption:**
   - Checkpoints are saved per node using `AsyncPostgresSaver`.
   - When a recovered job is executed, LangGraph loads the checkpoint corresponding to `thread_id = f"{org_id}:{research_id}"`, resuming from the last successfully committed node.

---

## ADR-008: Validated Organization Authorization vs. Client-Supplied Identifiers

### Status: Accepted
### Context
In multi-tenant architectures, relying on a client-supplied HTTP header (such as `X-Organization-ID`) to determine tenant identity is a critical security vulnerability if not strictly validated against the authenticated user's credentials.

### Decision
1. **Client Header as Context Selector Only:**
   - A client-supplied `X-Organization-ID` **never independently establishes tenant identity or authorization**.
   - It is strictly an optional *tenant context selector* used when an authenticated user belongs to multiple organizations.
2. **Mandatory Authorization Validation:**
   - The effective organization ID is derived from the validated JWT token (`org_id` claim) or explicitly verified against the user's active organization memberships in PostgreSQL (`user_organizations` table).
   - If `X-Organization-ID` is provided, the backend validates that the authenticated user is an active member of that specific organization. If unauthorized, the request is rejected with HTTP 403 Forbidden.
3. **Cross-Tenant Enumeration Prevention:**
   - Any attempt to access a specific resource (e.g., `GET /api/v1/research/{id}`) belonging to a different tenant returns **HTTP 404 Not Found** (not 403), preventing attackers from enumerating valid resource IDs across organizations.
4. **Universal 8-Layer Enforcement:** Tenant scoping is enforced at Auth Middleware, API Routes, Service Facades, Database Repositories (`WHERE organization_id = :org_id`), Queue Operations, Checkpoint Access, Artifact Storage (`/data/artifacts/{org_id}/`), and Audit Logging.

---

## ADR-009: PostgreSQL 18 Official `pgvector/pgvector` Image and Volume Mount Conventions

### Status: Accepted
### Context
Previous drafts referenced `ankane/pgvector:v0.8.0-pg18`. The official, actively maintained image repository for pgvector is `pgvector/pgvector`. Furthermore, PostgreSQL 18 containers enforce strict internal directory layout rules. Mounting a Docker named volume directly to `/var/lib/postgresql/data` when the image expects a subpath (or vice versa) causes accidental anonymous volume creation, permissions collisions, or total data invisibility when a container is recreated.

### Decision
1. **Official Image Pinning:**
   - Use the official upstream pgvector repository: **`pgvector/pgvector:pg18`** (pinned to specific patch/digest, e.g. `pgvector/pgvector:0.8.0-pg18`).
2. **Explicit PGDATA Directory & Volume Mount:**
   - **Named Volume:** `acis_postgres_data`
   - **Container Mount Path:** `/var/lib/postgresql/data`
   - **Explicit Environment Variable:** `PGDATA=/var/lib/postgresql/data/pgdata`
   *Rationale:* Setting `PGDATA` to a subdirectory (`/pgdata`) within the mount point allows PostgreSQL to initialize its cluster cleanly, leaving mount-level filesystem artifacts (e.g., `lost+found`) untouched and preventing permissions conflicts.
3. **Authentication & Hardening:**
   - Enforce SCRAM-SHA-256 via `POSTGRES_INITDB_ARGS="--auth-host=scram-sha-256 --auth-local=scram-sha-256"`.
   - Private network isolation: PostgreSQL is strictly bound to `acis_internal` bridge network with zero host port exposure.
