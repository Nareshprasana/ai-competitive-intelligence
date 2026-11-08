# ACIS Architecture Decision Records (ADRs)

**Project:** AI Competitive Intelligence System (ACIS)  
**Document:** Architecture Decision Records (ADR-001 through ADR-006)  
**Target Release:** Phase 4 Production Foundation  
**Status:** Approved Architecture Decisions  
**Date:** November 2026

---

## ADR-001: Frontend Runtime (Node.js LTS) and Next.js Upgrade Strategy

### Status: Accepted
### Context
The ACIS frontend currently uses Next.js 14.2.17 with React 18.3.1. The initial Phase 4 Stage 1 draft proposed Node.js 20-slim. However, Node.js 20 reached official End-of-Life (EOL) on April 30, 2026. Running an EOL runtime in production introduces unpatched OpenSSL/V8 vulnerabilities and fails security compliance audits.

Next.js framework support status in late 2026:
- Next.js 14.2.x: Maintenance mode. Compatible with Node.js 18.17+, 20, 22, and 24.
- Next.js 15.x: Current LTS framework version, introduces React 19, asynchronous request APIs (`await cookies()`, `await headers()`), uncached `fetch` by default, and Turbopack.
- Next.js 16.x: Latest release, stabilizes Partial Prerendering (PPR) and Server Actions caching.

### Decision
1. **Container Runtime Selection:** Pin the production container runtime to **Node.js 22 LTS (Active/Maintenance)** or **Node.js 24 LTS (Active LTS)** using the official Alpine image (`node:22.12.0-alpine3.20` or `node:24.0.0-alpine`).
2. **Framework Staging Strategy:** 
   - **Phase 4A Initial Deployment:** Retain Next.js 14.2.17 running under Node.js 22/24 LTS with `output: 'standalone'`. Empirically verified to build and pass all 28 frontend tests without breaking changes.
   - **Post-Phase 4 Framework Migration:** Schedule a dedicated, isolated migration workstream for upgrading Next.js 14 to Next.js 15/16. This decouples infrastructure deployment from framework breaking changes (async cookie migration, React 19 peer dependency audits).

### Consequences
- **Positive:** Immediately eliminates EOL runtime risk without risking application code regressions during containerization.
- **Negative:** Requires a scheduled follow-up task to modernize to Next.js 15/16 before Next.js 14 upstream security maintenance concludes.

---

## ADR-002: Durable LangGraph Execution Architecture

### Status: Accepted
### Context
Currently, `research_service.run_research()` executes synchronously inside the FastAPI HTTP route handler. In mock mode, this completes in <500ms. In production with live LLMs (OpenRouter/DeepSeek) and web scrapers, a complete research workflow requires 4–8 LLM round trips and 6–10 search/extraction steps, taking **30 to 120+ seconds**.

Executing this synchronously inside an HTTP request causes:
1. Reverse proxy HTTP gateway timeouts (typically 60s).
2. Browser connection timeouts.
3. Thread/process starvation in the ASGI server.
4. Total loss of in-flight research state if a client disconnects or container restarts.

FastAPI `BackgroundTasks` was evaluated but rejected as an architectural sole solution because tasks reside in volatile process memory: an unhandled exception, SIGTERM during deployment, or OOM restart permanently destroys queued and running jobs without recovery.

### Decision
Implement a **Durable Asynchronous Worker Architecture** using a **PostgreSQL-backed transactional job queue** and an asynchronous worker process:
1. API handler `POST /api/v1/research` creates a persistent `research_jobs` record within the same PostgreSQL transaction as `research_records`, immediately returning HTTP 202 Accepted with `research_id` and `job_id`.
2. A separate background worker process (`python -m app.workers.research_worker`) claims jobs using PostgreSQL ACID row-level locking (`SELECT ... FOR UPDATE SKIP LOCKED`).
3. The worker executes the LangGraph `StateGraph` workflow, persisting incremental node checkpoints via `AsyncPostgresSaver`.
4. The frontend polls `GET /api/v1/research/{id}` for state updates until the terminal state (`completed` or `failed`) is reached.

### Alternatives Considered
- **Redis + ARQ / Celery:** Rejected for initial production. Adds external stateful infrastructure (Redis container), extra memory overhead (~150MB), backup management, and dual-store consistency hazards between Redis and PostgreSQL.
- **RabbitMQ:** Rejected. Extreme operational complexity and maintenance overhead for current scale.

### Consequences
- **Positive:** Zero new infrastructure dependencies (reuses PostgreSQL 18); 100% ACID consistency between job state and research state; survives container crashes.
- **Negative:** Requires implementing worker claiming logic, heartbeats, and queue tables.

---

## ADR-003: PostgreSQL-Backed Job Lifecycle, Heartbeats, and Crash Recovery

### Status: Accepted
### Context
To guarantee durability without external broker software, the PostgreSQL job queue must handle concurrency, worker crashes, duplicate execution prevention, and cancellation.

### Decision
Define a robust job table and lifecycle state machine:

#### Schema (`research_jobs`):
- `id` (UUID, Primary Key)
- `research_id` (VARCHAR, Foreign Key to `research_records`, Indexed)
- `organization_id` (VARCHAR, Indexed for Tenant Isolation)
- `status` (`pending`, `running`, `completed`, `failed`, `cancelled`)
- `idempotency_key` (VARCHAR, Unique Index per tenant + hash)
- `worker_id` (VARCHAR, identifying claiming worker)
- `attempt_count` (INT, default 0)
- `max_attempts` (INT, default 3)
- `heartbeat_at` (TIMESTAMPTZ, updated every 15s)
- `scheduled_at` (TIMESTAMPTZ, default `NOW()`)
- `created_at`, `started_at`, `completed_at` (TIMESTAMPTZ)
- `error_details` (JSONB)

#### Concurrency & Claiming:
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
    attempt_count = attempt_count + 1,
    started_at = NOW(),
    heartbeat_at = NOW()
FROM next_job
WHERE research_jobs.id = next_job.id
RETURNING research_jobs.*;
```

#### Crash Recovery & Stale Job Reclamation:
A supervisor routine runs every 60 seconds:
```sql
UPDATE research_jobs
SET status = CASE WHEN attempt_count >= max_attempts THEN 'failed' ELSE 'pending' END,
    worker_id = NULL,
    error_details = jsonb_build_object('error', 'Worker crashed or heartbeat timed out')
WHERE status = 'running'
  AND heartbeat_at < NOW() - INTERVAL '90 seconds';
```

#### LangGraph Checkpoint Resumption:
When a reclaimed job is retried by a worker, the worker initializes LangGraph with the existing `thread_id` (`research_id`). `AsyncPostgresSaver` loads the latest saved checkpoint, allowing the pipeline to resume from the last successful node rather than restarting from scratch.

#### Cancellation:
Between each LangGraph node execution, the worker checks if `status == 'cancelled'`. If so, execution stops cleanly, emitting an `AuditEvent`.

### Consequences
- **Positive:** High resilience; idempotent execution; transparent progress tracking; zero lost jobs on worker restarts.

---

## ADR-004: Production Secrets and KMS/Vault Key Management Strategy

### Status: Accepted
### Context
ACIS handles confidential enterprise intelligence and requires four distinct categories of secrets:
1. Database credentials (`DATABASE_URL`).
2. Authentication token signing keys (`AUTH_JWT_SIGNING_KEY`, `AUTH_EMAIL_LOOKUP_KEY`).
3. Sensitive data encryption keys (`DATA_ENCRYPTION_KEYS`, `DATA_ENCRYPTION_ACTIVE_KEY_ID`).
4. External provider API keys (`OPENROUTER_API_KEY`).

Exposing secrets in Dockerfiles, Git, or world-readable files compromises the entire tenant security boundary.

### Decision
1. **Separation of Concerns:** Each category of secret must be managed independently with dedicated rotation procedures.
2. **Sensitive Data Key Protection:** For production environments, the master key protecting `DATA_ENCRYPTION_KEYS` (AES-256-GCM) must be secured by an external **KMS (Key Management Service)**, **Hardware Security Module (HSM)**, or **HashiCorp Vault**. Application containers receive decrypted envelope keys into memory only at startup.
3. **Container Secret Injection:**
   - **Initial Host VPS Deployment:** Use Docker Compose secrets or protected host environment files (`/opt/acis/.env.production`) restricted to `chmod 0600 root:root`.
   - **Managed Cloud Deployment:** Transition to native cloud secret managers (AWS Secrets Manager, GCP Secret Manager, or Infisical).
4. **Zero-Secret Invariant:** No secret values may ever be committed to Git, baked into container images, or output in application logs.

### Consequences
- **Positive:** Defense-in-depth; meets SOC 2 and ISO 27001 encryption key management controls.

---

## ADR-005: TLS 1.3, Cookie Policy (`SameSite=Strict`), and Ingress Security Headers

### Status: Accepted
### Context
Transport security and edge ingress policies must prevent cross-site request forgery, clickjacking, protocol downgrades, and content sniffing.

### Decision
1. **Cookie Security Policy:** All refresh token cookies must enforce:
   - `HttpOnly: true` (inaccessible to JavaScript).
   - `Secure: true` (transmitted only over HTTPS).
   - `SameSite: Strict` (preventing cross-site leakage on any third-party navigation).
   *Rationale:* Because the reverse proxy routes both frontend (`/`) and backend (`/api/v1`) under the exact same origin (e.g. `https://acis.example.com`), `SameSite=Strict` provides maximum protection without breaking legitimate same-site API interactions.
2. **TLS 1.3 Termination:** The edge proxy terminates TLS using modern ciphers, mandating TLS 1.3 (with TLS 1.2 fallback).
3. **HSTS Preload Policy:** 
   - **Do NOT enable HSTS preload automatically.**
   - Initial production will set: `Strict-Transport-Security: max-age=31536000; includeSubDomains`.
   - The `preload` directive will only be added after 90 days of stable HTTPS operation across the root domain and all subdomains, following formal submission to `hstspreload.org`.
4. **CSP Strategy (Report-Only First):**
   - Deploy `Content-Security-Policy-Report-Only` during staging and the first 30 days of production to identify any CSP violations in Next.js dynamic script injection or styling.
   - Enforce strict blocking `Content-Security-Policy` only after report logs confirm zero false positives.

### Consequences
- **Positive:** Prevents accidental lockout from premature HSTS preloading; avoids UI breakage from overly aggressive CSP rules while guaranteeing maximum CSRF immunity.

---

## ADR-006: Container Base Image Pinning and Vulnerability Patch Policy

### Status: Accepted
### Context
Using `:latest` or broad minor tags (e.g. `node:20-slim`, `python:3.11-slim`) introduces non-deterministic builds, breaking changes on rebuilds, and unexpected vulnerabilities.

### Decision
1. **Strict Tag Pinning:** All production container images must be pinned to explicit patch versions and Debian/Alpine release codenames:
   - **Backend:** `python:3.11.11-slim-bookworm` (or `3.12.8-slim-bookworm`).
   - **Frontend:** `node:22.12.0-alpine3.20` (or `node:24.0.0-alpine`).
   - **PostgreSQL:** `ankane/pgvector:v0.8.0-pg18` or `postgres:18.0-bookworm` with compiled `pgvector 0.8.0`.
   - **Reverse Proxy:** `caddy:2.9.1-alpine` or `nginx:1.27.3-alpine`.
2. **Digest Verification:** Production release manifests in CI/CD will pin immutable SHA-256 image digests (`image@sha256:...`).
3. **Vulnerability Patch Policy:**
   - Base images scanned weekly via Trivy in GitHub Actions.
   - Patch-level security updates reviewed and deployed on a monthly cadence.
   - Critical CVEs (CVSS >= 9.0) trigger an expedited out-of-band rebuild and redeployment within 48 hours.

### Consequences
- **Positive:** 100% reproducible builds; immunity to upstream breaking updates; automated vulnerability tracking.
