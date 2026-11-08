# ACIS Phase 4 Implementation Roadmap

**Project:** AI Competitive Intelligence System (ACIS)  
**Document:** Phase 4 Workstreams, Sequencing & Implementation Entry Criteria (Audited)  
**Target Release:** Phase 4 Production Foundation  
**Status:** Implementation Blueprint & Execution Roadmap

---

## 1. Roadmap Overview & Sequencing

The Phase 4 deployment foundation is structured into six sequential, testable workstreams designed to minimize deployment risk and ensure strict compliance with ACIS security and reliability standards:

```mermaid
flowchart LR
    Phase4A["Phase 4A\nProduction Containerization\n& Compose Validation"]
    Phase4B["Phase 4B\nProduction Database,\nDurable Worker & Storage"]
    Phase4C["Phase 4C\nReverse Proxy, TLS 1.3\n& Network Hardening"]
    Phase4D["Phase 4D\nObservability, Metrics\n& Structured Logging"]
    Phase4E["Phase 4E\nCI/CD & Release\nEngineering Pipeline"]
    Phase4F["Phase 4F\nStaging Deployment,\nDR Drill & Final Signoff"]

    Phase4A --> Phase4B --> Phase4C --> Phase4D --> Phase4E --> Phase4F

    classDef stream fill:#0288d1,stroke:#01579b,color:#fff;
    class Phase4A,Phase4B,Phase4C,Phase4D,Phase4E,Phase4F stream;
```

---

## 2. Workstream Specifications

### Phase 4A: Production Containerization & Local Compose Validation
- **Objective:** Convert prototype development Dockerfiles into production-hardened, multi-stage, unprivileged container images and validate local composition with pinned LTS runtimes.
- **Scope:**
  - Build multi-stage `Dockerfile.backend` on verified baseline **`python:3.11.18-slim-bookworm`** (or `python:3.11.11-slim-bookworm` fallback) running as non-root `appuser` (UID 10001) with production `gunicorn` / `uvicorn` workers.
  - Build multi-stage `Dockerfile.frontend` on `node:26.1.0-alpine3.21` (preferred modern Active LTS) or `node:24.13.0-alpine3.21` (conservative Maintenance LTS) using Next.js `output: 'standalone'` running as non-root `nextjs` (UID 1001). (Node.js 22 is explicitly disqualified as primary long-term runtime).
  - Update `docker-compose.yml` (and production overlay `docker-compose.prod.yml`) with healthchecks, persistent volumes, internal networks, and resource limits.
- **Dependencies:** Formal acceptance of Phase 3.3 (Commit `f658533`) and ADR-001/ADR-006.
- **Files to Modify/Create:**
  - `infrastructure/docker/Dockerfile.backend`
  - `infrastructure/docker/Dockerfile.frontend`
  - `frontend/next.config.js` (enable `output: 'standalone'`)
  - `docker-compose.yml` / `docker-compose.prod.yml`
  - `.dockerignore` (ensure `.git`, `tests`, `.env` are excluded)
- **Risks:** Build cache invalidation issues; Next.js standalone file-tracing missing static assets; permissions on mounted volumes.
- **Complexity:** Medium (3–4 days).
- **Acceptance Criteria:**
  - Container build images test clean without root permissions (`whoami` != root).
  - Backend image size < 450 MB; frontend standalone image size < 200 MB.
  - `docker compose up` spins up healthy services; frontend connects to backend on internal network; health probes pass.

---

### Phase 4B: Production Database, Durable Worker & Persistent Storage
- **Objective:** Establish production-grade PostgreSQL 18 with persistent volume mounts, implement the durable PostgreSQL job queue (`research_jobs`), launch the dedicated research worker process, and deploy backup automation scripts.
- **Scope:**
  - Configure PostgreSQL 18 container with pinned **`pgvector/pgvector:0.8.7-pg18-bookworm`**, `scram-sha-256` authentication, volume persistence (`acis_postgres_data` mounted at `/var/lib/postgresql`), and explicit `PGDATA=/var/lib/postgresql/18/docker`.
  - Create Alembic migration `0006_research_jobs.py` for transactional queue table (`id`, `research_id`, `organization_id`, `status`, `worker_id`, `fence_token`, `attempt_count`, `max_attempts`, `lease_expires_at`, `idempotency_key`, `error_details`).
  - Implement worker process `app.workers.research_worker` with `SELECT ... FOR UPDATE SKIP LOCKED` claim loop, fencing token validation on writes, and `AsyncPostgresSaver` checkpoint resumption.
  - Create pre-startup migration entrypoint (`alembic upgrade head`) with fail-fast validation.
  - Develop and test `backup-database.sh` script (compressed `pg_dump -Fc`, SHA-256 checksums, AES-256/GPG encryption).
  - Verify artifact filesystem persistence (`acis_artifacts_data`) and permissions.
- **Dependencies:** Completion of Phase 4A, ADR-002, ADR-003, ADR-007, and ADR-009.
- **Files to Modify/Create:**
  - `backend/alembic/versions/0006_research_jobs.py`
  - `backend/app/workers/research_worker.py`
  - `backend/app/services/research_service.py` (enqueue logic)
  - `infrastructure/scripts/backup-database.sh`
  - `infrastructure/scripts/restore-database.sh`
  - `infrastructure/scripts/verify-backup.sh`
- **Risks:** Database migration locks during startup; worker crash reclamation edge cases; volume mount permissions.
- **Complexity:** High (4–5 days).
- **Acceptance Criteria:**
  - `POST /api/v1/research` enqueues job and returns HTTP 202 in <100ms.
  - Background worker claims job, runs LangGraph, saves checkpoints, and completes research without holding HTTP connections.
  - Stale worker writes with mismatched `fence_token` are rejected (0 rows updated), preventing zombie overwrites.
  - Simulated worker SIGKILL during execution results in clean job reclamation and checkpoint resumption upon restart.
  - Automated backup script creates encrypted dump and verifies SHA-256 checksum.

---

### Phase 4C: Reverse Proxy, TLS Termination & Network Hardening
- **Objective:** Deploy edge reverse proxy (Caddy 2.10.2-alpine3.21 or NGINX 1.27.3-alpine3.21) with TLS 1.3, strict security headers (CSP Report-Only, HSTS without auto-preload), and total isolation of internal database and application ports.
- **Scope:**
  - Configure reverse proxy routing: `/` to Next.js (port 3000), `/api/*` to FastAPI (port 8000).
  - Enforce TLS 1.3, HSTS (`Strict-Transport-Security: max-age=31536000; includeSubDomains` without preload), CSP Report-Only, and anti-sniffing headers.
  - Enforce `SameSite=Strict`, `HttpOnly`, and `Secure` on all refresh token cookies alongside mandatory `X-CSRF-Token` and Origin validation.
  - Configure internal Docker networks (`acis_ingress` and `acis_internal`); remove all public port bindings for PostgreSQL and backend.
  - Tune FastAPI trusted proxy settings to safely extract real client IP from `X-Forwarded-For`.
- **Dependencies:** Completion of Phase 4A and Phase 4B; ADR-005 and ADR-008.
- **Files to Modify/Create:**
  - `infrastructure/docker/Caddyfile` or `infrastructure/docker/nginx.conf`
  - `docker-compose.prod.yml`
  - `backend/app/main.py` (trusted proxy validation settings)
- **Risks:** Next.js Server Actions / SSR proxy header mismatches; CSRF / Origin header mismatches during authentication.
- **Complexity:** Medium (3 days).
- **Acceptance Criteria:**
  - Port `5432` and port `8000` are completely inaccessible from host public interfaces.
  - Public HTTPS connection terminates cleanly with TLS 1.3 and A+ rating on SSL Labs.
  - Next.js login, token refresh (`SameSite=Strict`), and research requests flow seamlessly through proxy with correct client IP in audit logs.

---

### Phase 4D: Observability, Metrics & Structured Logging
- **Objective:** Implement lightweight, resource-efficient structured JSON logging, correlation tracking, and Prometheus metrics.
- **Scope:**
  - Configure backend and worker loggers to emit structured JSON to `stdout` with `request_id`, `tenant_id`, and log level.
  - Add Prometheus metrics exporter (`prometheus-fastapi-instrumentator`) exposing `/metrics` internally.
  - Configure Docker container logging limits (`max-size: 50m`, `max-file: 5`) to prevent disk exhaustion.
  - Provide minimal Prometheus + Grafana dashboard configuration for monitoring request latencies, error rates, queue depths, and DB pool stats.
- **Dependencies:** Completion of Phase 4C.
- **Files to Modify/Create:**
  - `backend/app/core/logging.py`
  - `backend/app/main.py` (metrics middleware)
  - `infrastructure/monitoring/prometheus.yml`
  - `infrastructure/monitoring/grafana/dashboards/`
- **Risks:** Excessive log volume filling host storage; metric collection adding latency to API requests.
- **Complexity:** Low to Medium (2–3 days).
- **Acceptance Criteria:**
  - Backend and worker emit machine-parseable JSON logs with sanitized headers.
  - Prometheus scrapes `/metrics` without error; Grafana renders API latency (p50/p95/p99) and queue latency graphs.
  - `X-Request-ID` is traceable across proxy, backend log, worker log, and client responses.

---

### Phase 4E: CI/CD Pipeline & Automated Release Engineering
- **Objective:** Implement GitHub Actions workflow for automated testing, security scanning, container builds, and deployment verification.
- **Scope:**
  - Create `.github/workflows/ci.yml`: runs linting, backend tests (pytest against PostgreSQL service container), frontend unit tests, and production build.
  - Integrate automated secret scanning (`gitleaks` / `trufflehog`) and dependency vulnerability checks (`pip-audit`, `npm audit`).
  - Create `.github/workflows/release.yml`: builds multi-arch container images on Git tag, scans images with Trivy, and pushes to private container registry with pre-resolved immutable digests.
- **Dependencies:** Completion of Phase 4A–4D; ADR-006.
- **Files to Modify/Create:**
  - `.github/workflows/ci.yml`
  - `.github/workflows/release.yml`
  - `.github/workflows/security-scan.yml`
- **Risks:** Flaky tests in GitHub Actions runner; slow container build times.
- **Complexity:** Medium (3–4 days).
- **Acceptance Criteria:**
  - Pull requests trigger automated CI: backend tests, frontend tests, and production build pass 100%.
  - Zero secrets or critical CVEs detected in scanner.
  - Git tags produce versioned, immutable Docker images with pinned SHA256 digests.

---

### Phase 4F: Deployment, Disaster Recovery Validation & Operational Signoff
- **Objective:** Execute staging deployment, run live disaster recovery drill, perform security penetration verification, and obtain formal Phase 4 production signoff.
- **Scope:**
  - Provision staging host VM (Hetzner / DigitalOcean); deploy full stack via Docker Compose.
  - Execute end-to-end user journeys against staging host over public HTTPS.
  - Perform live Disaster Recovery drill: simulate database host loss, restore from backup, verify zero data loss.
  - Conduct security validation: verify firewall rules, check cookie security attributes (`SameSite=Strict`), confirm memory fallback is disabled.
  - Produce operational runbook and disaster recovery manual.
- **Dependencies:** Completion of Phase 4A through Phase 4E.
- **Files to Modify/Create:**
  - `docs/phase-4-production-readiness/operational-runbook.md`
  - `docs/phase-4-production-readiness/disaster-recovery-drill-report.md`
- **Risks:** External networking/DNS propagation delays; cloud firewall misconfigurations.
- **Complexity:** Medium (3 days).
- **Acceptance Criteria:**
  - Staging deployment passes all automated and manual smoke tests over public HTTPS.
  - DR restore drill recovers complete database state in <30 minutes.
  - Production readiness checklist is 100% satisfied and approved.

---

## 3. Phase 4A Implementation Entry Criteria

Before initiating any coding, Dockerfile editing, or container composition in Phase 4A, the following readiness criteria must be satisfied and verified:

### 1. Finalized Architectural Decisions
- [x] **ADR-001:** Node.js 26 (`node:26.1.0-alpine3.21` preferred) or Node.js 24 (`node:24.13.0-alpine3.21` conservative) Alpine base runtime; Next.js 14 permitted strictly for temporary local Phase 4A testing; Next.js 16 (or 15) required for production.
- [x] **ADR-002 & ADR-003:** Durable PostgreSQL transactional queue (`research_jobs` with `SKIP LOCKED`, 15s heartbeats, 30s lease expiry, crash reclamation).
- [x] **ADR-004:** Four independent secret categories; KMS/Vault/HSM requirement for production sensitive-data encryption.
- [x] **ADR-005:** `SameSite=Strict` cookies treated as defense-in-depth alongside mandatory CSRF tokens and Origin validation; HSTS without auto-preload; CSP in Report-Only mode first.
- [x] **ADR-006:** Backend retains verified `python:3.11.18-slim-bookworm` (or `3.11.11-slim-bookworm` fallback) baseline; exact tag and pre-release digest pinning policy; non-root user execution (`10001`/`1001`).
- [x] **ADR-007:** At-least-once execution with idempotent node side effects; monotonic fencing tokens (`fence_token`) on writes.
- [x] **ADR-008:** Validated organization authorization derived strictly from authenticated user memberships; client-supplied `X-Organization-ID` serves only as a context selector; cross-tenant access returns 404.
- [x] **ADR-009:** Official `pgvector/pgvector:0.8.7-pg18-bookworm` image with explicit named volume mount at `/var/lib/postgresql` and `PGDATA=/var/lib/postgresql/18/docker`.

### 2. Decisions Remaining Open for Stakeholder Confirmation
- **Hosting Provider:** Hetzner Cloud CPX31 (~$20–$25/mo fully loaded) vs. DigitalOcean Droplet (~$60/mo). (Does not block local Phase 4A implementation).
- **Offsite Backup Store:** Cloudflare R2 vs. AWS S3 Standard. (Does not block Phase 4A; required before Phase 4B).
- **Production Domain:** Domain name registration and Cloudflare DNS delegation. (Required before Phase 4C).

### 3. Non-Relaxable Security Invariants
- Memory fallback (`ACIS_ENABLE_MEMORY_FALLBACK`) strictly disabled in production/staging.
- Argon2id password hashing, AES-256-GCM data encryption, and short-lived (10m) access tokens must remain intact.
- PostgreSQL port `5432` must never be exposed on host network interfaces.
- Zero secrets committed to Git, baked into container images, or output in logs.

### 4. Required Implementation Tests
- **Phase 4A Tests:** Multi-stage image build verification (`docker build`), non-root user verification (`whoami != root`), Next.js standalone artifact verification, local health check probe verification (`curl -f http://localhost:8000/api/v1/health`).
- **Phase 4B Tests:** Transactional queue unit & integration tests, concurrent worker claim tests (`SKIP LOCKED`), fencing token stale-write rejection tests, SIGKILL recovery tests.
- **Phase 4C Tests:** SSL Labs TLS 1.3 verification, security header inspection, CSRF token enforcement tests, cross-tenant isolation tests.

### 5. Production Deployment Blockers
- **Mandatory Framework Modernization Gate:** Commercial production deployment is **strictly blocked** until the frontend is upgraded from Next.js 14 to Next.js 16 (or Next.js 15) with React 19 and verified across all test suites.
- **Backup Usability Gate:** Production deployment is blocked until an automated restore dry-run from an encrypted snapshot is successfully executed and verified against a test database.

### 6. Worker Reliability & Database Readiness Requirements
- Database migration `0006_research_jobs.py` must apply cleanly via Alembic.
- Worker process must trap `SIGTERM`/`SIGINT` for graceful shutdown.
- Named volume `acis_postgres_data` must mount to `/var/lib/postgresql` with explicit `PGDATA=/var/lib/postgresql/18/docker`.

---

## 4. Exact Technical Verification Still Required During Phase 4A

When Phase 4A implementation begins, the engineering team must execute the following isolated, empirical verifications:
1. **Multi-Stage Backend Build Verification:** Build `Dockerfile.backend` with `python:3.11.18-slim-bookworm` (or `3.11.11-slim-bookworm` fallback); confirm all native dependencies (`asyncpg`, `cryptography`, `argon2-cffi`, `selectolax`, `pydantic-core`) install cleanly without compilers in the final runtime stage; verify container runs as `appuser` (`uid=10001`).
2. **Next.js Standalone Build Verification:** Build `Dockerfile.frontend` using `output: 'standalone'` on `node:26.1.0-alpine3.21` / `node:24.13.0-alpine3.21`; confirm static assets and server chunks bundle properly into `.next/standalone`; verify container runs as `nextjs` (`uid=1001`).
3. **Official PostgreSQL 18 + pgvector Verification:** Pull `pgvector/pgvector:0.8.7-pg18-bookworm`; verify pgvector extension initializes in PostgreSQL 18 via `CREATE EXTENSION vector;`; test `halfvec` and HNSW index support.
4. **Volume Mount Persistence Verification:**
   - Mount named volume `acis_postgres_data` to `/var/lib/postgresql` with `PGDATA=/var/lib/postgresql/18/docker`.
   - Run Alembic migrations `0001` through `0005`.
   - Insert a test record, stop and remove the container (`docker compose down`).
   - Launch a new container instance referencing the same named volume; verify that `/var/lib/postgresql/18/docker` persists and all tables/data are immediately visible.
5. **Private Network Isolation Verification:** Inspect `docker network inspect acis_internal`; verify backend, worker, and PostgreSQL containers can resolve each other via internal DNS, while `nmap` or `curl` from the host cannot connect to port 5432.
6. **Health Probe Verification:** Confirm `GET /api/v1/health` responds HTTP 200 within 50ms inside the local Compose environment.
