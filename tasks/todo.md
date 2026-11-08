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
