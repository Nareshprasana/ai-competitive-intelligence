# Continuous Engineering Task List: Container Infrastructure & Security Hardening

## Container Environment & Upstream Image Verification
- [x] Inspect local Docker Desktop and Docker Compose availability (`docker version 29.4.3`, `compose v5.1.3`)
- [x] Pin upstream image base versions with full SHA-256 digests:
  - [x] `pgvector/pgvector:0.8.7-pg18-bookworm@sha256:c29f30688a9ad961691bdf0ec1650717cc132a5814619d80f80463d6e4c42e47`
  - [x] `python:3.11.18-slim-bookworm@sha256:a83ba18aef0f865b1a4a611c2cf460fe446f2795673bbb9fe43be570439e3b39`
  - [x] `node:26.13.1-alpine3.24@sha256:6bd9ab43c0ec0190ca7b2d193906cb8b7edf6e7f4afa43ddeccd6452710bffb5` (Active LTS baseline)
  - [x] `caddy:2.11.9-alpine@sha256:003a97808e781aa9f7e75cc2f43d34d461099031faf5e20faefb9f61126836f0`

## Build Context & Ignore Optimization
- [x] Create root `.dockerignore` to exclude `.git`, `venv`, `node_modules`, `.next`, `.env*`
- [x] Create `backend/.dockerignore` and `frontend/.dockerignore`
- [x] Configure `.gitignore` to track `.dockerignore` while keeping `.env.*` credentials strictly untracked

## Backend Multi-Stage Containerization & Hardening
- [x] Implement multi-stage `infrastructure/docker/Dockerfile.backend` (builder + runtime)
- [x] Separate runtime dependencies (`backend/requirements.txt`) from test tooling (`backend/requirements-dev.txt`)
- [x] Verify `reportlab==5.0.1` remains available in production backend runtime
- [x] Enforce non-root execution (`appuser:appgroup` UID 10001, GID 10001)
- [x] Configure container health probe (`curl -f http://localhost:8000/api/v1/health`)
- [x] Verify backend image builds cleanly (126MB compressed)

## Frontend Multi-Stage Containerization & Hardening
- [x] Enable standalone build in `frontend/next.config.js` (`output: 'standalone'`)
- [x] Create `frontend/public/.gitkeep` for standard Next.js asset directory
- [x] Implement multi-stage `infrastructure/docker/Dockerfile.frontend` (`deps`, `builder`, `runner`)
- [x] Enforce non-root execution (`nextjs:nodejs` UID 1001, GID 1001)
- [x] Configure container health probe (`curl -f http://localhost:3000/`)
- [x] Verify frontend image builds cleanly (69.6MB compressed)

## PostgreSQL 18 & pgvector Storage Isolation
- [x] Configure PostgreSQL 18 with `pgvector/pgvector:0.8.7-pg18-bookworm`
- [x] Mount volume at `/var/lib/postgresql` with data directory `PGDATA=/var/lib/postgresql/18/docker`
- [x] Ensure complete database isolation (zero host port publishing, preserving host `acis_db`)
- [x] Apply all 5 Alembic migrations to isolated container database
- [x] Verify `vector` extension version 0.8.7
- [x] Verify persistent volume preservation across container restarts

## Caddy Reverse Proxy & Dual-Protocol Ingress
- [x] Implement `infrastructure/docker/Caddyfile` with reverse proxy routes
  - [x] Ingress proxy on port 8080 (HTTP) and port 8443 (HTTPS with `tls internal`)
  - [x] `/caddy-health` -> health probe endpoint (200 OK)
  - [x] `/api/*` -> backend:8000 with sanitized headers
  - [x] `/*` -> frontend:3000
- [x] Enforce security headers: `X-Frame-Options DENY`, `X-Content-Type-Options nosniff`, `Referrer-Policy strict-origin-when-cross-origin`, `Permissions-Policy`
- [x] Verify local HTTPS TLS handshake and backend routing via Caddy

## Compose Orchestration & Production Configuration
- [x] Standardize root `docker-compose.yml` with private bridge network `acis_internal`
- [x] Standardize container names: `acis_postgres`, `acis_backend`, `acis_frontend`, `acis_caddy`
- [x] Create `.env.docker.example` template with clean variable naming
- [x] Remove legacy milestone-based file artifacts (`docker-compose.phase4a.yml`, `.env.phase4a.example`)
- [x] Verify stack startup and health status via `docker compose --env-file .env.docker up -d`

## Security Control Verification & Ingress Audit
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
- [x] Non-root execution verified across all services:
  - [x] Backend: `appuser:appgroup` (UID 10001, GID 10001)
  - [x] Frontend: `nextjs:nodejs` (UID 1001, GID 1001)
  - [x] Postgres: `postgres` (UID 999)
- [x] Rate limiting verified: 429 Too Many Requests enforced through Caddy

## Browser-Level Authentication & Session Verification
- [x] Browser automated verification of live authentication flows in Chromium:
  - [x] Login via browser at `http://localhost:8080/login` and `https://localhost:8443/login`
  - [x] Verification of cookie storage (`acis_refresh_token`: HttpOnly=true, Secure=true, SameSite=Strict; `acis_csrf_token`: HttpOnly=false, Secure=true, SameSite=Strict)
  - [x] Session restoration on browser reload (silent refresh token exchange returning 200 OK)
  - [x] User logout and return to login screen (refresh token invalidated and cleared from browser storage)
  - [x] Fixed API client relative routing in `frontend/lib/api.js` for reverse-proxy architectures

## Regression Test Categorization & Continuous Verification
- [x] Audit all historical exit code 1 failures from transcripts
- [x] Categorize failure root causes (environmental, test assumptions, image characteristics, test ordering)
- [x] Verify that all genuine controls pass without regressions
