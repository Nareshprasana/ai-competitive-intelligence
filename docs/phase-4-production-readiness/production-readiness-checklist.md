# ACIS Production Readiness Checklist

**Project:** AI Competitive Intelligence System (ACIS)  
**Document:** Production Readiness Audit & Verification Checklist (Audited & Hardened)  
**Target Release:** Phase 4 Production Foundation  
**Assessment Date:** November 2026

---

## Legend
- `[x] Implemented & Verified` — Code exists and is verified by tests in commit `f658533`.
- `[ ] Planned for Phase 4` — Designed in architecture blueprint; scheduled for implementation in Phase 4A–4F.
- `[?] Requires Decision` — Architectural or operational choice requiring business/user direction.

---

## 1. Application Security & Access Control

| Status | Verification Item | Code / Configuration Grounding |
| :---: | :--- | :--- |
| `[x]` | Argon2id password hashing with modern salt & memory cost | Verified in `app.security.auth.hash_password` |
| `[x]` | Short-lived JWT access tokens (10m) with asymmetric/secret validation | Verified in `app.security.auth.create_access_token` |
| `[x]` | Refresh token rotation and single-flight invalidation | Verified in `app.security.auth.rotate_refresh_token` |
| `[x]` | Replay detection revoking all user sessions upon expired token reuse | Verified in `app.security.auth.rotate_refresh_token` |
| `[x]` | HttpOnly, Secure, and SameSite=Strict refresh cookie issuance | Verified in `app.api.v1.endpoints.auth` & `app.core.config` |
| `[x]` | Mandatory CSRF token (`X-CSRF-Token`) and Origin validation on state changes | Verified in `app.main.py` middleware & API client |
| `[x]` | Validated organization membership authorization (never trust client header alone) | Verified in `app.security.auth.require_tenant_access` |
| `[x]` | Repository-level SQL query scoping by `organization_id` (cross-tenant returns 404) | Verified in `app.repositories.*` |
| `[x]` | AES-256-GCM encryption of sensitive database columns at rest | Verified in `app.security.crypto` & Alembic revision `0005` |
| `[x]` | Safe artifact storage with regex validation and path traversal defenses | Verified in `app.services.artifact_storage` |
| `[x]` | IP and user rate limiting middleware (`enforce_rate_limit`) | Verified in `app.main.py` middleware stack |
| `[x]` | Request payload size enforcement (4MB streaming cutoff) | Verified in `app.main.py` middleware stack |
| `[x]` | Fail-closed memory fallback policy (disabled in prod/staging) | Verified in `app.core.config.validate_production_security` |
| `[x]` | Correlation tracking via `X-Request-ID` and audit event logging | Verified in `app.main.py` (`AuditEvent` persistence) |
| `[ ]` | Real client IP extraction from behind trusted reverse proxy | Planned for Phase 4C (`--proxy-headers` / trusted IP subnets) |
| `[ ]` | KMS / HSM-backed envelope key protection for `DATA_ENCRYPTION_KEYS` | Planned for Phase 4C / ADR-004 |
| `[?]` | Multi-Factor Authentication (MFA / TOTP) requirement for admin users | Requires user decision (Post-Phase 4 roadmap item) |

---

## 2. Ingress & Network Hardening

| Status | Verification Item | Implementation Target |
| :---: | :--- | :--- |
| `[ ]` | Edge reverse proxy (Caddy:2.10.2-alpine3.21 / NGINX:1.27.3-alpine3.21) terminates TLS 1.3 | Planned for Phase 4C |
| `[ ]` | Automated ACME certificate issuance and 60-day renewal hooks | Planned for Phase 4C (Let's Encrypt / ZeroSSL) |
| `[ ]` | Complete elimination of public PostgreSQL port mapping (`5432`) | Planned for Phase 4A / 4C (Docker internal bridge only) |
| `[ ]` | Complete elimination of public backend ASGI port mapping (`8000`) | Planned for Phase 4A / 4C (Docker internal bridge only) |
| `[ ]` | HSTS configured (`max-age=31536000; includeSubDomains`) without auto-preload | Planned for Phase 4C / ADR-005 |
| `[ ]` | CSP deployed in Report-Only mode during initial rollout | Planned for Phase 4C / ADR-005 |
| `[ ]` | Host firewall (UFW) permitting only ports 80, 443, and SSH | Planned for Phase 4F host provisioning |
| `[?]` | Cloudflare edge proxy / DDoS protection layer integration | Requires user decision (Free tier Cloudflare recommended) |

---

## 3. Containerization & Runtime Security

| Status | Verification Item | Implementation Target |
| :---: | :--- | :--- |
| `[ ]` | Backend container builds as multi-stage unprivileged `appuser` (10001) | Planned for Phase 4A (`infrastructure/docker/Dockerfile.backend`) |
| `[ ]` | Backend base image pinned to verified baseline `python:3.11.18-slim-bookworm` | Planned for Phase 4A / ADR-006 |
| `[ ]` | Frontend container builds as multi-stage unprivileged `nextjs` (1001) | Planned for Phase 4A (`infrastructure/docker/Dockerfile.frontend`) |
| `[ ]` | Frontend base image pinned to Node.js LTS `node:26.1.0-alpine3.21` or `node:24.13.0-alpine3.21` | Planned for Phase 4A / ADR-001 |
| `[ ]` | Frontend utilizes Next.js standalone mode (`output: 'standalone'`) | Planned for Phase 4A (`frontend/next.config.js`) |
| `[ ]` | Backend ASGI runs production Gunicorn/Uvicorn multi-worker process | Planned for Phase 4A (`gunicorn -k uvicorn.workers.UvicornWorker`) |
| `[ ]` | Explicit CPU and memory limits on all Docker Compose services | Planned for Phase 4A (`deploy.resources.limits`) |
| `[ ]` | Container liveness and readiness healthchecks configured | Planned for Phase 4A & 4D (`/api/v1/health/*`) |
| `[ ]` | Clean, non-root volume permissions for artifacts (`0750`) | Planned for Phase 4B host directory setup |

---

## 4. Durable Workflows & Database Reliability

| Status | Verification Item | Implementation Target |
| :---: | :--- | :--- |
| `[x]` | PostgreSQL 18 schema fully managed under Alembic revisions 0001–0005 | Verified in `backend/alembic/versions/` |
| `[x]` | Loop-aware connection pooling preventing dead loop leaks | Verified in `backend/app/core/database.py` (Commit `f658533`) |
| `[x]` | LangGraph state checkpointing configured with `AsyncPostgresSaver` | Verified in `app.services.research_service` |
| `[ ]` | Transactional `research_jobs` queue table (Alembic migration 0006) | Planned for Phase 4B / ADR-002 |
| `[ ]` | Dedicated asynchronous research worker process (`app.workers.research_worker`) | Planned for Phase 4B / ADR-002 |
| `[ ]` | Worker claiming using PostgreSQL `FOR UPDATE SKIP LOCKED` | Planned for Phase 4B / ADR-003 |
| `[ ]` | Monotonic fencing token (`fence_token`) validation preventing zombie overwrites | Planned for Phase 4B / ADR-007 |
| `[ ]` | Worker heartbeat loop (15s) and crash reclamation supervisor | Planned for Phase 4B / ADR-003 |
| `[ ]` | LangGraph checkpoint resumption on retried / recovered jobs | Planned for Phase 4B / ADR-007 |
| `[ ]` | At-least-once execution with idempotent agent node side effects | Planned for Phase 4B / ADR-007 |
| `[ ]` | Frontend status polling against `GET /api/v1/research/{id}` | Planned for Phase 4B |
| `[ ]` | Official PostgreSQL 18 image `pgvector/pgvector:0.8.7-pg18-bookworm` with SCRAM-SHA-256 | Planned for Phase 4B / ADR-009 |
| `[ ]` | Named volume `acis_postgres_data` mounted at `/var/lib/postgresql` with `PGDATA=/var/lib/postgresql/18/docker` | Planned for Phase 4B / ADR-009 |
| `[ ]` | Automated database migration execution on container startup | Planned for Phase 4B entrypoint script |
| `[ ]` | Automated daily compressed logical backups (`pg_dump -Fc`) | Planned for Phase 4B (`infrastructure/scripts/backup-database.sh`) |
| `[ ]` | Backup encryption at rest via AES-256 / GPG before transport | Planned for Phase 4B backup pipeline |
| `[ ]` | Automated offsite backup synchronization (Cloudflare R2 / AWS S3) | Planned for Phase 4B sync script |
| `[ ]` | Weekly automated restore dry-run test into verification database | Planned for Phase 4B / 4F operational protocol |
| `[ ]` | Documented Disaster Recovery procedure with verified <1h RTO | Planned for Phase 4F operational runbook |

---

## 5. Observability & Telemetry

| Status | Verification Item | Implementation Target |
| :---: | :--- | :--- |
| `[x]` | Centralized application logger with correlation context | Verified in `app.core.logging` |
| `[ ]` | Structured JSON log formatting emitted to `stdout` in production | Planned for Phase 4D (`app.core.logging.configure_logging`) |
| `[ ]` | Sensitive credential & payload redaction in application logs | Planned for Phase 4D log filter |
| `[ ]` | Distinct Liveness (`/health`) and Readiness (`/health/readiness`) probes | Planned for Phase 4D API update |
| `[ ]` | Prometheus metrics endpoint (`/metrics`) exposing latency & pool stats | Planned for Phase 4D (`prometheus-fastapi-instrumentator`) |
| `[ ]` | Docker container log rotation limits (`max-size: 50m`, `max-file: 5`) | Planned for Phase 4D Docker daemon / compose setting |
| `[ ]` | Grafana dashboard monitoring API error spikes and queue latencies | Planned for Phase 4D monitoring setup |

---

## 6. CI/CD & Release Engineering

| Status | Verification Item | Implementation Target |
| :---: | :--- | :--- |
| `[x]` | Backend unit & integration test suite passing 100% (302/302 tests) | Verified in local test runner |
| `[x]` | Frontend unit & E2E tests passing 100% (28/28 tests) | Verified in local test runner |
| `[x]` | Frontend Next.js production build succeeds clean (14/14 routes) | Verified in local build runner |
| `[ ]` | Automated GitHub Actions CI workflow executing test matrix on PR | Planned for Phase 4E (`.github/workflows/ci.yml`) |
| `[ ]` | Automated secret scanning in pipeline (`gitleaks` / `trufflehog`) | Planned for Phase 4E (`.github/workflows/security-scan.yml`) |
| `[ ]` | Container image vulnerability scanning (`trivy`) prior to registry push | Planned for Phase 4E (`.github/workflows/release.yml`) |
| `[ ]` | Pre-release discovery and version-controlled pinning of immutable SHA256 container digests | Planned for Phase 4E / ADR-006 |
| `[ ]` | Automated pre-migration snapshot and rollback validation script | Planned for Phase 4E deployment script |

---

## 7. Mandatory Production Deployment Blockers

1. **Frontend Framework Modernization Gate:** Commercial production deployment is **strictly blocked** until the frontend is modernized from Next.js 14 to **Next.js 16** (or Next.js 15) with React 19, passing 100% of tests. Next.js 14 is permitted strictly for temporary local infrastructure testing in Phase 4A.
2. **PostgreSQL Backup Verification Gate:** Production deployment is blocked until an automated restore dry-run from an encrypted snapshot is successfully executed against an isolated verification container.
3. **KMS / HSM Encryption Key Protection Gate:** Production deployment is blocked until master keys for `DATA_ENCRYPTION_KEYS` are secured via a managed KMS, Vault, or HSM.
