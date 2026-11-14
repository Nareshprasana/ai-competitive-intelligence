# Implementation Plan: ACIS Phase 4A — Production-Ready Containerization Foundation

## Overview
Implement production-ready containerization for ACIS using multi-stage Docker builds, PostgreSQL 18 with pgvector, Next.js 14 standalone output, and Caddy reverse proxy routing. Ensure complete isolation between containerized environments and the local development database `acis_db`.

## Container Architecture

```
                       [ Host Ingress: :8080 ]
                                 │
                     ┌───────────▼───────────┐
                     │   Caddy Reverse Proxy │
                     │ (caddy:2.11.9-alpine@ │
                     │  sha256:003a9780...)  │
                     └─────┬───────────┬─────┘
           /api/*          │           │   /*
    ┌──────────────────────┘           └──────────────────────┐
    │                                                         │
┌───▼─────────────────────┐                       ┌───────────▼───────────┐
│     FastAPI Backend     │                       │    Next.js Frontend   │
│ (python:3.11.18-slim-   │                       │ (node:26.13.1-alpine  │
│  bookworm@sha256:a83b...,│                      │  3.24@sha256:6bd9a...,│
│  multi-stage runtime,   │                       │  standalone build,    │
│  non-root: appuser      │                       │  non-root: nextjs     │
│  UID 10001)             │                       │  UID 1001)            │
└───┬─────────────────────┘                       └───────────────────────┘
    │
    │  Internal Network (acis_phase4a_internal)
    │
┌───▼─────────────────────┐
│  PostgreSQL 18 Database │
│ (pgvector:0.8.7-pg18-   │
│  bookworm@sha256:c29f.) │
│  Mount: /var/lib/       │
│         postgresql      │
│  PGDATA: /var/lib/      │
│   postgresql/18/docker  │
│  DB: acis_phase4a_db    │
└─────────────────────────┘
```

## Implemented Deliverables

1. **Multi-Stage Backend Dockerfile (`infrastructure/docker/Dockerfile.backend`)**:
   - Builder stage: Installs build dependencies and wheels into `/install` prefix.
   - Runtime stage: Pinned `python:3.11.18-slim-bookworm@sha256:a83ba18aef0f865b1a4a611c2cf460fe446f2795673bbb9fe43be570439e3b39` with only runtime shared library `libpq5` and `curl`.
   - Dependency Separation: Runtime dependencies (`backend/requirements.txt`, including `reportlab==5.0.1`) separated from test-only tooling (`backend/requirements-dev.txt`). `pytest` and test files excluded from production runtime.
   - Security: Runs as non-root user `appuser` (UID 10001, GID 10001).
   - Container size: ~126MB compressed content size.
   - Built-in health check on `/api/v1/health`.

2. **Multi-Stage Frontend Dockerfile (`infrastructure/docker/Dockerfile.frontend`)**:
   - Standalone output enabled in `frontend/next.config.js`.
   - Stage 1 (`deps`): Installs dependencies with `npm ci`.
   - Stage 2 (`builder`): Compiles standalone Next.js build.
   - Stage 3 (`runner`): Pinned Active LTS `node:26.13.1-alpine3.24@sha256:6bd9ab43c0ec0190ca7b2d193906cb8b7edf6e7f4afa43ddeccd6452710bffb5` standalone server.
   - Security: Runs as non-root user `nextjs:nodejs` (UID 1001, GID 1001).
   - Container size: ~69.6MB compressed content size.
   - Built-in health check on root `/`.

3. **PostgreSQL 18 & pgvector (`docker-compose.phase4a.yml`)**:
   - Pinned official image `pgvector/pgvector:0.8.7-pg18-bookworm@sha256:c29f30688a9ad961691bdf0ec1650717cc132a5814619d80f80463d6e4c42e47`.
   - Named volume `acis_phase4a_postgres_data` mounted at `/var/lib/postgresql`.
   - Versioned directory `PGDATA=/var/lib/postgresql/18/docker`.
   - Isolated database `acis_phase4a_db` (zero host port publishing).
   - All 5 Alembic migrations applied and verified.
   - Extension `vector 0.8.7` enabled and verified.

4. **Caddy Reverse Proxy (`infrastructure/docker/Caddyfile`)**:
   - Pinned official image `caddy:2.11.9-alpine@sha256:003a97808e781aa9f7e75cc2f43d34d461099031faf5e20faefb9f61126836f0`.
   - Ingress on port 8080.
   - Header sanitization (`X-Forwarded-*`, `X-Real-IP`, `Host`).
   - Security headers: `X-Frame-Options DENY`, `X-Content-Type-Options nosniff`, `Referrer-Policy strict-origin-when-cross-origin`, `Permissions-Policy`.
   - Healthcheck on `/caddy-health`.

5. **Docker Compose & Configuration (`docker-compose.phase4a.yml`, `.env.phase4a.example`)**:
   - Private internal bridge network `acis_phase4a_internal`.
   - Isolated environment with template `.env.phase4a.example` and untracked `.env.phase4a`.
