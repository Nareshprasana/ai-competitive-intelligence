# Continuous Engineering Plan: Container Infrastructure & Security Hardening

## Overview
Standardize and maintain production-ready containerization for ACIS using multi-stage Docker builds, PostgreSQL 18 with pgvector, Next.js 14 standalone output, and Caddy reverse proxy routing with dual HTTP and TLS ingress. Ensure complete isolation between containerized environments and the local development database `acis_db`.

## Container Architecture

```
                       [ Host Ingress: 127.0.0.1:8080 (HTTP) | 127.0.0.1:8443 (HTTPS) ]
                                                   │
                                       ┌───────────▼───────────┐
                                       │   Caddy Reverse Proxy │
                                       │ (caddy:2.11.9-alpine@ │
                                       │  sha256:003a9780...)  │
                                       └─────┬───────────┬─────┘
                             /api/*          │           │   /*
                      ┌──────────────────────┘           └──────────────────────┐
                      │                                                         │
          ┌───────────▼───────────┐                                 ┌───────────▼───────────┐
          │     FastAPI Backend   │                                 │    Next.js Frontend   │
          │ (python:3.11.18-slim- │                                 │ (node:26.13.1-alpine  │
          │  bookworm@sha256:a83b,│                                 │  3.24@sha256:6bd9a,   │
          │  multi-stage runtime, │                                 │  standalone build,    │
          │  non-root: appuser    │                                 │  non-root: nextjs     │
          │  UID 10001)           │                                 │  UID 1001)            │
          └───────────┬───────────┘                                 └───────────────────────┘
                      │
                      │  Internal Network (acis_internal)
                      │
          ┌───────────▼───────────┐
          │ PostgreSQL 18 + Vector│
          │ (pgvector:0.8.7-pg18- │
          │  bookworm@sha256:c29f)│
          │  Mount: /var/lib/     │
          │         postgresql    │
          │  PGDATA: /var/lib/    │
          │   postgresql/18/docker│
          │  Volume: postgres_data│
          │ (legacy: acis_phase4a)│
          └───────────────────────┘
```

## Implemented Engineering Modules

1. **Multi-Stage Backend Containerization (`infrastructure/docker/Dockerfile.backend`)**:
   - Builder stage: Installs build dependencies and wheels into `/install` prefix.
   - Runtime stage: Pinned `python:3.11.18-slim-bookworm@sha256:a83ba18aef0f865b1a4a611c2cf460fe446f2795673bbb9fe43be570439e3b39` with only runtime shared library `libpq5` and `curl`.
   - Dependency Separation: Runtime dependencies (`backend/requirements.txt`, including `reportlab==5.0.1`) separated from test-only tooling (`backend/requirements-dev.txt`). `pytest` and test files excluded from production runtime.
   - Security: Runs as non-root user `appuser` (UID 10001, GID 10001).
   - Container size: ~126MB compressed content size.
   - Built-in health check on `/api/v1/health`.

2. **Multi-Stage Frontend Containerization (`infrastructure/docker/Dockerfile.frontend`)**:
   - Standalone output enabled in `frontend/next.config.js`.
   - Stage 1 (`deps`): Installs dependencies with `npm ci`.
   - Stage 2 (`builder`): Compiles standalone Next.js build.
   - Stage 3 (`runner`): Pinned Active LTS `node:26.13.1-alpine3.24@sha256:6bd9ab43c0ec0190ca7b2d193906cb8b7edf6e7f4afa43ddeccd6452710bffb5` standalone server.
   - Security: Runs as non-root user `nextjs:nodejs` (UID 1001, GID 1001).
   - Container size: ~69.6MB compressed content size.
   - Built-in health check on root `/`.

3. **PostgreSQL 18 & pgvector Storage Foundation (`docker-compose.yml`)**:
   - Pinned official image `pgvector/pgvector:0.8.7-pg18-bookworm@sha256:c29f30688a9ad961691bdf0ec1650717cc132a5814619d80f80463d6e4c42e47`.
   - Named volume `postgres_data` (mapped to legacy storage identifier `acis_phase4a_postgres_data` to preserve existing state and prevent data loss) mounted at `/var/lib/postgresql`.
   - Versioned directory `PGDATA=/var/lib/postgresql/18/docker`.
   - Isolated database instance (zero host port publishing). Host database `acis_db` strictly preserved on host port 5432.
   - All 5 Alembic migrations applied and verified.
   - Extension `vector 0.8.7` enabled and verified.

4. **Caddy Reverse Proxy & Security Ingress (`infrastructure/docker/Caddyfile`, `Caddyfile.production`)**:
   - Pinned official image `caddy:2.11.9-alpine@sha256:003a97808e781aa9f7e75cc2f43d34d461099031faf5e20faefb9f61126836f0`.
   - Local ingress bound strictly to loopback (`127.0.0.1:8080` HTTP and `127.0.0.1:8443` HTTPS with `tls internal`).
   - Separate production configuration template in `infrastructure/docker/Caddyfile.production` supporting public CA-issued TLS certificates, TLS 1.3 enforcement, and HSTS.
   - Header sanitization (`Host`, `X-Real-IP`, `X-Forwarded-*`).
   - Security headers: `X-Frame-Options DENY`, `X-Content-Type-Options nosniff`, `Referrer-Policy strict-origin-when-cross-origin`, `Permissions-Policy`.
   - Healthcheck on `/caddy-health`.

5. **Docker Compose Orchestration & Configuration (`docker-compose.yml`, `.env.docker.example`)**:
   - Private internal bridge network `acis_internal`.
   - Clean production-grade naming for all services (`postgres`, `backend`, `frontend`, `caddy`).
   - Ingress ports restricted to `127.0.0.1` (no public network exposure).
   - Isolated environment with template `.env.docker.example` and untracked `.env.docker`.

## Production-Readiness Backlog & Operational Requirements

The following operational capabilities are tracked as continuous engineering requirements prior to public production deployment:

1. **Durable Background Job Execution**:
   - Decouple long-running LLM research and report generation workflows into durable asynchronous worker queues with retry policies, state checkpointing, and execution timeouts.
2. **Automated Encrypted Database Backups**:
   - Implement scheduled automated backups of PostgreSQL 18 with client-side GPG/AES-256 encryption before streaming to off-site object storage.
3. **Restore Testing**:
   - Establish automated restore verification drills to validate backup integrity, verify pgvector extension re-indexing, and guarantee Recovery Time Objectives (RTO).
4. **Artifact Backup & Recovery**:
   - Secure and replicate generated report files, evidence payloads, and research exports with versioned lifecycle rules.
5. **KMS / Vault / HSM Key Management**:
   - Migrate application data encryption keys and JWT signing secrets from local environment variables to hardware-backed or managed key management systems (AWS KMS, GCP Cloud KMS, or HashiCorp Vault) with automatic key rotation.
6. **Production TLS & Certificate Lifecycle**:
   - Deploy `infrastructure/docker/Caddyfile.production` with automated ACME certificate management (Let's Encrypt / ZeroSSL), enforcing TLS 1.3 and HSTS preloading.
7. **Structured Logging & Monitoring**:
   - Standardize JSON application logs, OpenTelemetry trace context propagation across Caddy/FastAPI/Next.js, and Prometheus metrics for request rate, error rate, and duration (RED metrics).
8. **Deployment & Rollback Procedures**:
   - Automate blue/green or rolling container deployment pipelines with health-gated rollbacks and zero-downtime database schema migration compatibility.
9. **Disaster Recovery**:
   - Formalize Recovery Point Objective (RPO <= 1 hour) and Recovery Time Objective (RTO <= 30 minutes) runbooks and failure drills.
