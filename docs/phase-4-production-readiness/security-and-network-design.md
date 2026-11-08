# ACIS Security and Network Design

**Project:** AI Competitive Intelligence System (ACIS)  
**Document:** Security & Network Architecture (Audited & Hardened)  
**Target Release:** Phase 4 Production Foundation  
**Classification:** Security Architecture Specification

---

## 1. Network Segmentation & Ingress Architecture

The production deployment enforces defense-in-depth across the physical host, network layer, transport layer, and application runtime.

```mermaid
flowchart TD
    subgraph PublicZone ["Public Network (Untrusted)"]
        InternetTraffic["Incoming Internet Traffic\n(IPv4 / IPv6)"]
    end

    subgraph HostBoundary ["Production Host Boundary (Firewall / UFW)"]
        Firewall["Host Firewall (UFW / iptables)\nAllow Inbound: 80, 443, 22 (SSH keys only)\nDrop All Other Inbound Ports"]
        
        subgraph IngressBridge ["Docker Bridge Network: acis_ingress"]
            ProxyContainer["Reverse Proxy (Caddy:2.9 / NGINX:1.27)\n- Exposed: 0.0.0.0:80, 0.0.0.0:443\n- TLS 1.3 Termination\n- Strips spoofed X-Forwarded-* headers\n- Injects verified client IP"]
        end

        subgraph InternalBridge ["Docker Bridge Network: acis_internal (Isolated)"]
            FrontendContainer["Next.js Frontend Container\n- Internal Port: 3000\n- NO Host Port Mapping"]
            BackendContainer["FastAPI Backend Container\n- Internal Port: 8000\n- NO Host Port Mapping\n- Trusted Proxy: Only Reverse Proxy IP"]
            WorkerContainer["Durable Research Worker Container\n- Background Process (No exposed ports)\n- Dedicated DB pool"]
            PostgresContainer["PostgreSQL 18 Database Container\n(pgvector/pgvector:0.8.0-pg18)\n- Internal Port: 5432\n- NO Host Port Mapping\n- Isolated from public internet"]
        end
    end

    InternetTraffic -->|TCP 80 / 443| Firewall --> ProxyContainer
    ProxyContainer -->|HTTP :3000 (Internal)| FrontendContainer
    ProxyContainer -->|HTTP :8000 (Internal)| BackendContainer
    BackendContainer -->|TCP :5432 (Internal)| PostgresContainer
    WorkerContainer -->|TCP :5432 (Internal)| PostgresContainer
    FrontendContainer -.->|SSR / Internal API| ProxyContainer

    classDef public fill:#d32f2f,stroke:#b71c1c,color:#fff;
    classDef firewall fill:#e65100,stroke:#bf360c,color:#fff;
    classDef proxy fill:#0288d1,stroke:#01579b,color:#fff;
    classDef internal fill:#388e3c,stroke:#1b5e20,color:#fff;

    class PublicZone,InternetTraffic public;
    class HostBoundary,Firewall firewall;
    class IngressBridge,ProxyContainer proxy;
    class InternalBridge,FrontendContainer,BackendContainer,WorkerContainer,PostgresContainer internal;
```

### 1.1 Ingress & Port Exposure Rules
- **Publicly Accessible Ports:**
  - `443/tcp`: HTTPS (TLS 1.3 / 1.2).
  - `80/tcp`: HTTP (Permanent 301 redirect to HTTPS; Let's Encrypt ACME challenges).
  - `22/tcp` (or non-standard port): SSH (Key-based authentication only, password auth disabled, fail2ban active).
- **Prohibited Port Mappings:**
  - `5432/tcp` (PostgreSQL): **Strictly internal.** Binding to `0.0.0.0:5432` or any public interface is blocked by container configuration and host firewall.
  - `8000/tcp` (FastAPI backend): Internal only. Public access is mediated entirely through the reverse proxy.
  - `3000/tcp` (Next.js frontend): Internal only.

---

## 2. Reverse Proxy, TLS & Ingress Security Headers

### 2.1 TLS 1.3 Transport Security
- **Protocols:** TLS 1.3 (primary) and TLS 1.2 (for legacy compatibility). All legacy protocols (SSLv2, SSLv3, TLS 1.0, TLS 1.1) are explicitly disabled.
- **Cipher Suites:** Modern PFS (Perfect Forward Secrecy) ciphers:
  - `TLS_AES_256_GCM_SHA384`, `TLS_CHACHA20_POLY1305_SHA256`, `TLS_AES_128_GCM_SHA256`
  - `ECDHE-ECDSA-AES256-GCM-SHA384`, `ECDHE-RSA-AES256-GCM-SHA384`
- **Certificate Lifecycle:** Automated issuance and renewal using Let's Encrypt ACME via Caddy or NGINX + Certbot with automated 60-day renewal hooks.

### 2.2 HSTS Strategy & Preload Prerequisites
- **Initial Production Setting:**
  ```http
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  ```
- **HSTS Preload Policy:** **Do NOT enable HSTS preload automatically.**
  - *Prerequisites for Preload:*
    1. Valid certificate on root domain and all subdomains.
    2. HTTP-to-HTTPS redirect on port 80 for all subdomains.
    3. Minimum 90 days of stable production HTTPS operation without certificate expiration.
    4. Explicit submission to `hstspreload.org`.
  - *Operational Warning:* Once a domain is accepted into the global browser HSTS preload list, removing it or serving HTTP for legacy subdomains requires months of browser engine vendor coordination.

### 2.3 Content Security Policy (CSP): Report-Only First
To prevent Next.js hydration failures, inline style blocking, or dynamic script breakage:
- **Phase 1 (Staging & Initial Production):** Deploy in `Report-Only` mode:
  ```http
  Content-Security-Policy-Report-Only: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; report-uri /api/v1/telemetry/csp-reports;
  ```
- **Phase 2 (Hardened Enforcement):** After 30 days of clean violation logs, enforce blocking `Content-Security-Policy`.

### 2.4 Anti-Clickjacking & MIME Protection
```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
```

### 2.5 Trusted Proxy & Anti-Spoofing Configuration
1. **Header Stripping:** The reverse proxy sanitizes and rewrites all incoming `X-Forwarded-*` headers before forwarding requests.
2. **FastAPI Trusted Proxy Settings:**
   - In production, FastAPI/Uvicorn is executed with `--proxy-headers` and `--forwarded-allow-ips=172.16.0.0/12,192.168.0.0/16,10.0.0.0/8` (restricting trusted proxy signals to internal Docker bridge subnets).
3. **Correlation ID Propagation:** The reverse proxy generates an `X-Request-ID` (UUIDv4) if absent, which FastAPI binds to `request.state.request_id` and attaches to all outgoing responses and audit logs.

---

## 3. Cookie Security, CSRF Defense-in-Depth & Authentication

### 3.1 Cookie Security & Defense-in-Depth CSRF Model
All refresh token cookies issued by `/api/v1/auth/login` and `/api/v1/auth/refresh` enforce:
- `HttpOnly: true` (inaccessible to JavaScript).
- `Secure: true` (transmitted only over HTTPS).
- `SameSite: Strict` (preventing cookie transmission on cross-site navigations).

> [!CRITICAL]
> **SameSite=Strict is defense-in-depth, NOT a replacement for CSRF protection.**  
> Browser bugs, same-site subdomains, and top-level navigation edge cases can bypass SameSite. ACIS enforces defense-in-depth CSRF controls:

1. **Mandatory CSRF Token Header (`X-CSRF-Token`):** Every mutating request (POST, PUT, PATCH, DELETE) must present an `X-CSRF-Token` header that cryptographically matches the session CSRF secret.
2. **Origin & Referer Validation:** Middleware strictly validates the `Origin` and `Referer` headers against `BACKEND_CORS_ORIGINS`.
3. **Refresh Token Rotation:** Every refresh issuance invalidates the prior refresh token.
4. **Replay Detection & Session Revocation:** If an already-used or revoked refresh token is presented, ACIS immediately revokes all refresh tokens belonging to that user family, terminating all active sessions.

---

## 4. Tenant Isolation and Organization Authorization

> [!IMPORTANT]
> **A client-supplied organization identifier (`X-Organization-ID`) must NEVER independently establish tenant identity or authorization.**

The authorized organization must be derived from the authenticated user's validated organization membership and authorization context.

### 4.1 Universal 8-Layer Tenant Enforcement Matrix

| Enforcement Layer | Mechanism & Implementation | Violation Response |
| :--- | :--- | :--- |
| **1. Auth Middleware** | Decodes JWT; verifies `user_id` and active memberships. `X-Organization-ID` acts as a context selector and is verified against user's confirmed organizations in PostgreSQL. | HTTP 403 Forbidden (if user not in org) |
| **2. API / Route Layer** | Endpoint dependencies inject `TenantContext` containing validated `organization_id` and role permissions. | HTTP 403 Forbidden |
| **3. Service Facades** | `ResearchService` and domain services accept only validated `TenantContext`; caller cannot override tenant scope. | ValueError / HTTP 403 |
| **4. Repository Layer** | All SQL queries in `ResearchRepository`, `TenantRepository`, etc., enforce mandatory parameter binding: `WHERE organization_id = :org_id`. | HTTP 404 Not Found (Cross-tenant access returns 404 to prevent resource enumeration) |
| **5. Job Queue Operations** | `research_jobs` table records `organization_id`. Workers claim and process jobs strictly within tenant scope. | Job rejected; `AuditEvent` logged |
| **6. Checkpoint Storage** | LangGraph thread namespaces are strictly scoped: `thread_id = f"{org_id}:{research_id}"`. | Checkpoint inaccessible |
| **7. Artifact Storage** | Filesystem path strictly bounded: `/data/artifacts/{org_id}/{artifact_name}` with regex validation (`^[a-zA-Z0-9_\-]+$`) and `Path.is_relative_to()` containment check. | Path traversal exception |
| **8. Audit Logging** | Every mutating action records an immutable `AuditEvent` with actor `user_id`, validated `organization_id`, and `request_id`. | Recorded as security failure event |

---

## 5. Production Secrets & Encryption Key Management

### 5.1 Independent Secrets Categories & Rotation Protocols

| Secret Category | Configuration Keys | Rotation Procedure | Rotation Frequency |
| :--- | :--- | :--- | :--- |
| **1. Database Credentials** | `DATABASE_URL` (PostgreSQL user password) | 1. Create secondary DB role password.<br/>2. Update app configuration & restart containers.<br/>3. Drop old password. | 90 days or on personnel departure. |
| **2. Authentication Token Keys** | `AUTH_JWT_SIGNING_KEY`, `AUTH_EMAIL_LOOKUP_KEY` | 1. Introduce dual-key validation in backend.<br/>2. Sign with new key; accept old key during 10m access token TTL grace period.<br/>3. Retire old key. | 180 days. |
| **3. Sensitive Data Encryption** | `DATA_ENCRYPTION_KEYS`, `DATA_ENCRYPTION_ACTIVE_KEY_ID` | 1. Append new key ID to `DATA_ENCRYPTION_KEYS` JSON.<br/>2. Update `DATA_ENCRYPTION_ACTIVE_KEY_ID`.<br/>3. Existing rows decrypt via legacy key ID; new rows write with active key.<br/>4. Optional background migration rewrites legacy rows. | Annual or on compromise. |
| **4. External Provider APIs** | `OPENROUTER_API_KEY` | Generate new API key in provider console; update container secret; revoke old key. | 90 days. |

### 5.2 KMS / HSM-Backed Protection Requirement
For production deployments handling enterprise customer intelligence:
- The master key protecting `DATA_ENCRYPTION_KEYS` must be protected by a **Hardware Security Module (HSM)** or managed **KMS** (AWS KMS, GCP Cloud KMS, or Vault Transit engine).
- Plaintext data encryption keys must never be stored in persistent disk files alongside the encrypted database.
