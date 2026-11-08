# ACIS Production Readiness Checklist

**Project:** AI Competitive Intelligence System (ACIS)  
**Document:** Production Readiness Audit & Verification Checklist  
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
| `[x]` | HttpOnly, Secure, and SameSite=Lax cookie issuance | Verified in `app.api.v1.endpoints.auth` & `app.core.config` |
| `[x]` | Mandatory multi-tenant isolation (`X-Organization-ID` + JWT check) | Verified in `app.security.auth.require_tenant_access` |
| `[x]` | Repository-level SQL query scoping by `organization_id` | Verified in `app.repositories.*` |
| `[x]` | AES-256-GCM encryption of sensitive database columns at rest | Verified in `app.security.crypto` & Alembic revision `0005` |
| `[x]` | Safe artifact storage with regex validation and path traversal defenses | Verified in `app.services.artifact_storage` |
| `[x]` | IP and user rate limiting middleware (`enforce_rate_limit`) | Verified in `app.main.py` middleware stack |
| `[x]` | Request payload size enforcement (4MB streaming cutoff) | Verified in `app.main.py` middleware stack |
| `[x]` | Fail-closed memory fallback policy (disabled in prod/staging) | Verified in `app.core.config.validate_production_security` |
| `[x]` | Correlation tracking via `X-Request-ID` and audit event logging | Verified in `app.main.py` (`AuditEvent` persistence) |
| `[ ]` | Real client IP extraction from behind trusted reverse proxy | Planned for Phase 4C (`--proxy-headers` / trusted IP subnets) |
| `[?]` | Multi-Factor Authentication (MFA / TOTP) requirement for admin users | Requires user decision (Post-Phase 4 roadmap item) |

---

## 2. Ingress & Network Hardening

| Status | Verification Item | Implementation Target |
| :---: | :--- | :--- |
| `[ ]` | Edge reverse proxy (Caddy / NGINX) terminates TLS 1.3 | Planned for Phase 4C |
| `[ ]` | Automated ACME certificate issuance and 60-day renewal hooks | Planned for Phase 4C (Let's Encrypt / ZeroSSL) |
| `[ ]` | Complete elimination of public PostgreSQL port mapping (`5432`) | Planned for Phase 4A / 4C (Docker internal bridge only) |
| `[ ]` | Complete elimination of public backend ASGI port mapping (`8000`) | Planned for Phase 4A / 4C (Docker internal bridge only) |
| `[ ]` | Strict HTTP security headers (HSTS, CSP, X-Frame-Options, nosniff) | Planned for Phase 4C reverse proxy configuration |
| `[ ]` | Host firewall (UFW) permitting only ports 80, 443, and SSH | Planned for Phase 4F host provisioning |
| `[?]` | Cloudflare edge proxy / DDoS protection layer integration | Requires user decision (Free tier Cloudflare recommended) |

---

## 3. Containerization & Runtime Security

| Status | Verification Item | Implementation Target |
| :---: | :--- | :--- |
| `[ ]` | Backend container builds as multi-stage unprivileged `appuser` (10001) | Planned for Phase 4A (`infrastructure/docker/Dockerfile.backend`) |
| `[ ]` | Frontend container builds as multi-stage unprivileged `nextjs` (1001) | Planned for Phase 4A (`infrastructure/docker/Dockerfile.frontend`) |
| `[ ]` | Frontend utilizes Next.js 14 `output: 'standalone'` mode (~180MB) | Planned for Phase 4A (`frontend/next.config.js`) |
| `[ ]` | Backend ASGI runs production Gunicorn/Uvicorn multi-worker process | Planned for Phase 4A (`gunicorn -k uvicorn.workers.UvicornWorker`) |
| `[ ]` | Explicit CPU and memory limits on all Docker Compose services | Planned for Phase 4A (`deploy.resources.limits`) |
| `[ ]` | Container liveness and readiness healthchecks configured | Planned for Phase 4A & 4D (`/api/v1/health/*`) |
| `[ ]` | Clean, non-root volume permissions for artifacts (`0750`) | Planned for Phase 4B host directory setup |

---

## 4. Database Reliability & Disaster Recovery

| Status | Verification Item | Implementation Target |
| :---: | :--- | :--- |
| `[x]` | PostgreSQL 18 schema fully managed under Alembic revisions 0001–0005 | Verified in `backend/alembic/versions/` |
| `[x]` | Loop-aware connection pooling preventing dead loop leaks | Verified in `backend/app/core/database.py` (Commit `f658533`) |
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
| `[ ]` | Grafana dashboard monitoring API error spikes and LLM run durations | Planned for Phase 4D monitoring setup |

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
| `[ ]` | Tagged immutable Docker image publishing to private container registry | Planned for Phase 4E release pipeline |
| `[ ]` | Automated pre-migration snapshot and rollback validation script | Planned for Phase 4E deployment script |

---

## 7. Operational Decisions Required

1. **Hosting Provider Selection:** Confirm deployment on **Hetzner Cloud CPX31 (~$15.50/mo)** or **DigitalOcean Droplet (~$53/mo)** for Phase 4 launch.
2. **Offsite Backup Storage Target:** Confirm target object store for encrypted daily backups (Cloudflare R2 recommended for zero egress fees, or AWS S3 Standard).
3. **Domain Name & DNS Provisioning:** Select primary domain (e.g. `acis.company.com` or `app.acis.ai`) and confirm DNS nameserver management via Cloudflare.
4. **LangGraph Execution Concurrency:** Approve Stage 1 backgrounding strategy (`FastAPI BackgroundTasks` + polling) for long-running live LLM research workflows.
