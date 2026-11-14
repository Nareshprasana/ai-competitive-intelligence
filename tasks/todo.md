# Task List: ACIS Phase 4A — Production-Ready Containerization Foundation

## Stage A: Docker & Environment Verification
- [x] Inspect local Docker Desktop and Docker Compose availability (`docker version 29.4.3`, `compose v5.1.3`)
- [x] Verify upstream image availability:
  - [x] `pgvector/pgvector:0.8.7-pg18-bookworm` (digest: sha256:c29f3068...)
  - [x] `python:3.11-slim-bookworm` (Python 3.11.18 runtime, digest: sha256:a83ba18a...)
  - [x] `node:24-alpine` (Node.js v24.22.2, Alpine 3.24.4, digest: sha256:a34ab6d7...)
  - [x] `caddy:2-alpine` (Caddy v2.11.9, digest: sha256:78bd3502...)

## Stage B: Context & Ignore Optimization
- [x] Create root `.dockerignore` to exclude `.git`, `venv`, `node_modules`, `.next`, `.env*`
- [x] Create `backend/.dockerignore` and `frontend/.dockerignore`
- [x] Configure `.gitignore` to track `.dockerignore` while keeping `.env.phase4a` strictly untracked

## Stage C: Backend Multi-Stage Containerization
- [x] Implement multi-stage `infrastructure/docker/Dockerfile.backend` (builder + runtime)
- [x] Resolve dependency versions in `backend/requirements.txt` (`pytest==8.4.2`, `reportlab==5.0.1`)
- [x] Enforce non-root execution (`appuser:appgroup` UID 10001, GID 10001)
- [x] Configure container health probe (`curl -f http://localhost:8000/api/v1/health`)
- [x] Verify backend image builds cleanly (126MB compressed)

## Stage D: Frontend Multi-Stage Containerization
- [x] Enable standalone build in `frontend/next.config.js` (`output: 'standalone'`)
- [x] Create `frontend/public/.gitkeep` for standard Next.js asset directory
- [x] Implement multi-stage `infrastructure/docker/Dockerfile.frontend` (`deps`, `builder`, `runner`)
- [x] Enforce non-root execution (`nextjs` UID 1001)
- [x] Configure container health probe (`curl -f http://localhost:3000/`)
- [x] Verify frontend image builds cleanly (69.6MB compressed)

## Stage E: PostgreSQL 18 & pgvector Foundation
- [x] Configure PostgreSQL 18 with `pgvector/pgvector:0.8.7-pg18-bookworm`
- [x] Apply official PostgreSQL 18 volume mount: `acis_phase4a_postgres_data:/var/lib/postgresql`
- [x] Apply official PostgreSQL 18 data directory: `PGDATA=/var/lib/postgresql/18/docker`
- [x] Verify database isolation (`acis_phase4a_db`, no host port published)
- [x] Apply all 5 Alembic migrations against `acis_phase4a_db`
- [x] Verify `vector` extension version 0.8.7
- [x] Verify data persistence across container restart (tested with organization record insert and reboot)

## Stage F: Caddy Reverse Proxy & Security Ingress
- [x] Implement `infrastructure/docker/Caddyfile` with reverse proxy routes
  - [x] Ingress proxy on port 8080 (`"${ACIS_HTTP_PORT:-8080}:80"`)
  - [x] `/caddy-health` -> health probe endpoint (200 OK)
  - [x] `/api/*` -> backend:8000 with header sanitization
  - [x] `/*` -> frontend:3000
- [x] Enforce security headers: `X-Frame-Options DENY`, `X-Content-Type-Options nosniff`, `Referrer-Policy strict-origin-when-cross-origin`, `Permissions-Policy`

## Stage G & H: Compose Orchestration & Environment Configuration
- [x] Create `docker-compose.phase4a.yml` with private bridge network `acis_phase4a_internal`
- [x] Create `.env.phase4a.example` template
- [x] Create local untracked `.env.phase4a` with cryptographically long keys
- [x] Launch full stack with `docker compose -f docker-compose.phase4a.yml up -d`
- [x] Verify all 4 containers healthy (`backend`, `frontend`, `postgres`, `caddy`)

## Stage I & J: Verification & Regressions
- [x] Test Caddy health endpoint via `curl.exe` -> 200 OK
- [x] Test backend health API via Caddy (`http://localhost:8080/api/v1/health`) -> 200 OK, database connected
- [x] Test frontend login page via Caddy (`http://localhost:8080/login`) -> 200 OK, full SSR HTML rendered
- [x] Run backend test suite (`pytest`) -> 302 passed out of 302 tests (100% pass rate)
- [x] Run frontend unit/integration tests -> 20 passed out of 20 tests (100% pass rate)
- [x] Run browser user journeys -> 8 passed out of 8 tests (100% pass rate)

## Stage K: Final Security & Compliance Audit
- [x] Audit container image pins and replace floating tags with exact patch tags and verified SHA-256 digests:
  - [x] `pgvector/pgvector:0.8.7-pg18-bookworm@sha256:c29f30688a9ad961691bdf0ec1650717cc132a5814619d80f80463d6e4c42e47`
  - [x] `python:3.11.18-slim-bookworm@sha256:a83ba18aef0f865b1a4a611c2cf460fe446f2795673bbb9fe43be570439e3b39`
  - [x] `node:26.13.1-alpine3.24@sha256:6bd9ab43c0ec0190ca7b2d193906cb8b7edf6e7f4afa43ddeccd6452710bffb5` (Active LTS verified compatible with Next.js 14)
  - [x] `caddy:2.11.9-alpine@sha256:003a97808e781aa9f7e75cc2f43d34d461099031faf5e20faefb9f61126836f0`
- [x] Audit dependency separation:
  - [x] Created `backend/requirements-dev.txt` with test tooling (`pytest==8.4.2`, `pytest-asyncio==0.26.0`)
  - [x] Separated test tooling from `backend/requirements.txt`
  - [x] Verified `reportlab==5.0.1` remains available in production backend runtime
  - [x] Verified production backend image excludes `pytest` and test directories
- [x] Audit secret & image-layer isolation:
  - [x] Verified `.env.phase4a` remains untracked and excluded in `.gitignore`
  - [x] Verified `.dockerignore` excludes `tests/`, `pytest.ini`, env files, caches, and test artifacts
  - [x] Verified no credentials in image layers or build history
- [x] Audit database & volume isolation:
  - [x] Preserved existing development database `acis_db` on host PostgreSQL 18
  - [x] Verified Phase 4A uses only `acis_phase4a_db` and volume `acis_phase4a_postgres_data`
  - [x] Verified PostgreSQL 18 volume mount `/var/lib/postgresql` and `PGDATA=/var/lib/postgresql/18/docker`
  - [x] Verified `vector 0.8.7` extension installed and working
  - [x] Verified data persistence across container restarts
  - [x] Verified database port 5432 is internal only (zero host port publishing)
- [x] Audit authentication, authorization, and reverse-proxy security (12/12 passing):
  - [x] 1. Login through public local ingress (`/api/v1/auth/login`) -> 200 OK
  - [x] 2. HttpOnly refresh cookie behavior -> `HttpOnly` present on refresh cookie
  - [x] 3. Secure cookie behavior -> `Secure` attribute enforced in configured environment
  - [x] 4. SameSite Strict remains intact -> `SameSite=Strict` on auth cookies
  - [x] 5. Refresh token rotation & token theft detection -> single-use rotation, replay detection, and session revocation cascade
  - [x] 6. Logout and session revocation -> 204 No Content, cookies cleared, session revoked
  - [x] 7. CSRF validation -> 403 Forbidden on missing/mismatched `X-CSRF-Token`
  - [x] 8. Origin validation -> 403 Forbidden on disallowed or missing `Origin`
  - [x] 9. Cross-tenant authorization and 404 behavior -> 404 Not Found on cross-tenant resource lookup (enumeration prevented); 403 on tenant spoofing
  - [x] 10. Forwarded-header sanitization and trusted proxy handling -> `Via: 1.1 Caddy` header, upstream sanitized
  - [x] 11. Request correlation IDs -> `X-Request-Id` generated/propagated on all responses
  - [x] 12. Backend error sanitization -> 404 and 422 errors sanitized without stack traces or internal secrets
- [x] Non-root execution verified:
  - [x] Backend: `appuser:appgroup` (UID 10001, GID 10001)
  - [x] Frontend: `nextjs:nodejs` (UID 1001, GID 1001)
  - [x] Postgres: `postgres` (UID 999)
- [x] Rate limiting verified: 429 Too Many Requests enforced through Caddy

