# ACIS Phase 4 Implementation Roadmap

**Project:** AI Competitive Intelligence System (ACIS)  
**Document:** Phase 4 Workstreams, Sequencing & Verification Criteria  
**Target Release:** Phase 4 Production Infrastructure & Deployment  
**Status:** Architecture Blueprint & Implementation Specification

---

## 1. Roadmap Overview & Sequencing

The Phase 4 deployment foundation is divided into six sequential, testable workstreams designed to minimize deployment risk and ensure strict compliance with ACIS security and reliability standards:

```mermaid
flowchart LR
    Phase4A["Phase 4A\nProduction Containerization\n& Compose Validation"]
    Phase4B["Phase 4B\nProduction Database\n& Persistent Storage"]
    Phase4C["Phase 4C\nReverse Proxy, TLS\n& Network Hardening"]
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
- **Objective:** Convert prototype development Dockerfiles into production-hardened, multi-stage, unprivileged container images and validate local composition.
- **Scope:**
  - Build multi-stage `Dockerfile.backend` on `python:3.11-slim` running as non-root `appuser` (UID 10001) with production `gunicorn` / `uvicorn` workers.
  - Build multi-stage `Dockerfile.frontend` on `node:20-alpine` using Next.js `output: 'standalone'` running as non-root `nextjs` (UID 1001).
  - Update `docker-compose.yml` (and production overlay `docker-compose.prod.yml`) with healthchecks, persistent volumes, internal networks, and resource limits.
- **Dependencies:** Formal acceptance of Phase 3.3 (Commit `f658533`).
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

### Phase 4B: Production Database, Migrations & Persistent Storage
- **Objective:** Establish production-grade PostgreSQL 18 with persistent volume mounts, automated migration execution, and backup automation scripts.
- **Scope:**
  - Configure PostgreSQL 18 container with `pgvector`, `scram-sha-256` authentication, and volume persistence (`acis_postgres_data`).
  - Create pre-startup migration entrypoint (`alembic upgrade head`) with fail-fast validation.
  - Develop and test `backup-database.sh` script (compressed `pg_dump -Fc`, SHA-256 checksums, AES-256/GPG encryption).
  - Verify artifact filesystem persistence (`acis_artifacts_data`) and permissions.
- **Dependencies:** Completion of Phase 4A.
- **Files to Modify/Create:**
  - `infrastructure/docker/docker-entrypoint-backend.sh`
  - `infrastructure/scripts/backup-database.sh`
  - `infrastructure/scripts/restore-database.sh`
  - `infrastructure/scripts/verify-backup.sh`
- **Risks:** Database migration locks during startup; permissions mismatch on Docker volume mounts across host and container user IDs.
- **Complexity:** Medium (3 days).
- **Acceptance Criteria:**
  - Starting stack automatically runs Alembic migrations to latest revision.
  - Automated backup script creates encrypted dump and verifies SHA-256 checksum.
  - Restore script successfully restores an encrypted dump into a clean test database.

---

### Phase 4C: Reverse Proxy, TLS Termination & Network Hardening
- **Objective:** Deploy edge reverse proxy (Caddy or NGINX) with TLS 1.3, strict security headers, and total isolation of internal database and application ports.
- **Scope:**
  - Configure reverse proxy routing: `/` to Next.js (port 3000), `/api/*` to FastAPI (port 8000).
  - Enforce TLS 1.3, HSTS (`includeSubDomains; preload`), CSP, and anti-sniffing headers.
  - Configure internal Docker networks (`acis_ingress` and `acis_internal`); remove all public port bindings for PostgreSQL and backend.
  - Tune FastAPI trusted proxy settings to safely extract real client IP from `X-Forwarded-For`.
- **Dependencies:** Completion of Phase 4A and Phase 4B.
- **Files to Modify/Create:**
  - `infrastructure/docker/Caddyfile` or `infrastructure/docker/nginx.conf`
  - `docker-compose.prod.yml`
  - `backend/app/main.py` (trusted proxy validation settings)
- **Risks:** Next.js Server Actions / SSR proxy header mismatches; CSRF / Origin header mismatches during authentication.
- **Complexity:** Medium (3 days).
- **Acceptance Criteria:**
  - Port `5432` and port `8000` are completely inaccessible from host public interfaces (`nmap` / `curl` connection refused).
  - Public HTTPS connection terminates cleanly with TLS 1.3 and A+ rating on SSL Labs.
  - Next.js login, token refresh, and research requests flow seamlessly through proxy with correct client IP in audit logs.

---

### Phase 4D: Observability, Metrics & Structured Logging
- **Objective:** Implement lightweight, resource-efficient structured JSON logging, correlation tracking, and Prometheus metrics.
- **Scope:**
  - Configure backend logger to emit structured JSON to `stdout` with `request_id`, `tenant_id`, and log level.
  - Add Prometheus metrics exporter (`prometheus-fastapi-instrumentator`) exposing `/metrics` internally.
  - Configure Docker container logging limits (`max-size: 50m`, `max-file: 5`) to prevent disk exhaustion.
  - Provide minimal Prometheus + Grafana dashboard configuration for monitoring request latencies, error rates, and DB pool stats.
- **Dependencies:** Completion of Phase 4C.
- **Files to Modify/Create:**
  - `backend/app/core/logging.py`
  - `backend/app/main.py` (metrics middleware)
  - `infrastructure/monitoring/prometheus.yml`
  - `infrastructure/monitoring/grafana/dashboards/`
- **Risks:** Excessive log volume filling host storage; metric collection adding latency to API requests.
- **Complexity:** Low to Medium (2–3 days).
- **Acceptance Criteria:**
  - Backend emits machine-parseable JSON logs with sanitized headers.
  - Prometheus scrapes `/metrics` without error; Grafana renders API latency (p50/p95/p99) and error rate graphs.
  - `X-Request-ID` is traceable across proxy, backend log, and client responses.

---

### Phase 4E: CI/CD Pipeline & Automated Release Engineering
- **Objective:** Implement GitHub Actions workflow for automated testing, security scanning, container builds, and deployment verification.
- **Scope:**
  - Create `.github/workflows/ci.yml`: runs linting, backend tests (pytest against PostgreSQL service container), frontend unit tests, and production build.
  - Integrate automated secret scanning (`gitleaks` / `trufflehog`) and dependency vulnerability checks (`pip-audit`, `npm audit`).
  - Create `.github/workflows/release.yml`: builds multi-arch container images on Git tag, scans images with Trivy, and pushes to private container registry.
- **Dependencies:** Completion of Phase 4A–4D.
- **Files to Modify/Create:**
  - `.github/workflows/ci.yml`
  - `.github/workflows/release.yml`
  - `.github/workflows/security-scan.yml`
- **Risks:** Flaky tests in GitHub Actions runner; slow container build times.
- **Complexity:** Medium (3–4 days).
- **Acceptance Criteria:**
  - Pull requests trigger automated CI: backend tests, frontend tests, and production build pass 100%.
  - Zero secrets or critical CVEs detected in scanner.
  - Git tags produce versioned, immutable Docker images.

---

### Phase 4F: Deployment, Disaster Recovery Validation & Operational Signoff
- **Objective:** Execute staging deployment, run live disaster recovery drill, perform security penetration verification, and obtain formal Phase 4 production signoff.
- **Scope:**
  - Provision staging host VM (Hetzner / DigitalOcean); deploy full stack via Docker Compose.
  - Execute end-to-end user journeys against staging host over public HTTPS.
  - Perform live Disaster Recovery drill: simulate database host loss, restore from backup, verify zero data loss.
  - Conduct security validation: verify firewall rules, check cookie security attributes, confirm memory fallback is disabled.
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
