# ACIS Resource and Cost Estimates

**Project:** AI Competitive Intelligence System (ACIS)  
**Document:** Resource Allocation & Infrastructure Cost Modeling (Audited)  
**Target Release:** Phase 4 Production Foundation  
**Assessment Date:** November 2026  
**Disclaimer:** All figures are operational engineering estimates based on application profiling, container footprint analysis, and prevailing market pricing as of late 2026. Figures do not constitute contractual provider quotes.

---

## 1. Application Resource Consumption Breakdown

Based on empirical test profiles, container footprints, and application workload analysis:

| Component | Minimum Required RAM | Recommended Production RAM | Typical CPU Usage | Peak CPU Workload | Disk Footprint |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Next.js Frontend (Standalone)** | 250 MB | 512 MB – 1 GB | 2–5% idle / SSR | 30–50% during heavy SSR page render | ~180 MB container image |
| **FastAPI Backend (Gunicorn/Uvicorn)** | 350 MB | 1.0 GB – 1.5 GB | 3–8% idle | 40–60% during PDF generation & API routing | ~400 MB container image |
| **Durable Research Worker** | 400 MB | 1.0 GB – 1.5 GB | <1% polling | 60–80% during multi-agent LangGraph runs | ~400 MB container image |
| **PostgreSQL 18 + pgvector** | 512 MB | 1.5 GB – 2.0 GB | 2–5% idle | 40–60% during complex analytical queries & vector indexing | 10 GB base + 1–5 GB / month growth |
| **Reverse Proxy (Caddy / NGINX)** | 50 MB | 128 MB | <1% | 5–10% under high SSL handshake concurrency | ~50 MB container image |
| **Artifact Storage (PDFs/Markdown)** | N/A (Disk only) | N/A | Negligible I/O | Negligible I/O | ~2–5 MB per generated research report |
| **Monitoring (Prometheus/Grafana)** | 200 MB | 512 MB | 1–3% | 5–10% during metric aggregation | ~5–10 GB metric storage |
| **Total Stack Footprint** | **~1.8 GB RAM** | **~4.5 – 6.5 GB RAM** | **10–20% baseline** | **Peak bursts up to 2.5–3.5 Cores** | **~30–50 GB total disk** |

---

## 2. Container Resource Limits & Reservations (Docker Compose)

To prevent noisy-neighbor starvation, memory leaks, or container crashes from destabilizing the host, Docker Compose enforces explicit resource reservations and hard limits:

```yaml
services:
  reverse_proxy:
    image: caddy:2.9.1-alpine
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 256M
        reservations:
          cpus: '0.10'
          memory: 64M

  frontend:
    image: acis-frontend:0.1.0
    deploy:
      resources:
        limits:
          cpus: '1.00'
          memory: 1024M
        reservations:
          cpus: '0.25'
          memory: 256M

  backend:
    image: acis-backend:0.1.0
    deploy:
      resources:
        limits:
          cpus: '1.50'
          memory: 1536M
        reservations:
          cpus: '0.25'
          memory: 384M

  research_worker:
    image: acis-backend:0.1.0
    command: ["python", "-m", "app.workers.research_worker"]
    deploy:
      resources:
        limits:
          cpus: '2.00'
          memory: 2048M
        reservations:
          cpus: '0.50'
          memory: 512M

  postgres:
    image: ankane/pgvector:v0.8.0-pg18
    deploy:
      resources:
        limits:
          cpus: '1.50'
          memory: 2048M
        reservations:
          cpus: '0.25'
          memory: 512M
```

---

## 3. Deployment Tier Sizing

### Tier 1: Minimum Viable Deployment (Staging / Internal Pilot)
- **Target Specification:** 2 vCPU, 4 GB RAM, 40–50 GB SSD storage.
- **Capacity:** Supports 5–10 concurrent internal users, ~50 research reports/day.
- **Constraints:** Limited concurrency during intensive PDF compilation. Single host, local backup copies.

### Tier 2: Recommended Initial Production Deployment (Commercial Launch)
- **Target Specification:** 4 vCPU, 8 GB RAM, 80–160 GB NVMe SSD storage.
- **Capacity:** Supports 50–100 active users, 200–500 research reports/day, full Prometheus/Grafana metrics, automated offsite backup sync.
- **Redundancy:** Automated offsite backups, zero memory thrashing, ample buffer cache for PostgreSQL.

### Tier 3: Future Scaled Architecture (Multi-Tenant Growth)
- **Target Specification:** Split tier architecture:
  - Frontend/Backend Compute: 2x Application Nodes (4 vCPU, 8 GB RAM each) behind Cloud Load Balancer.
  - Database: Managed HA PostgreSQL cluster (e.g. AWS RDS 2 vCPU, 8 GB RAM with Multi-AZ replica).
  - Storage: Cloud Object Storage (AWS S3 / Cloudflare R2) for PDF artifacts.
- **Capacity:** 5,000+ active users, 5,000+ reports/day, zero-downtime rolling updates.

---

## 4. Itemized Monthly Cost Modeling (Verified & Estimated Breakdown)

### 4.1 Tier 2 Production Host Breakdown (Hetzner vs. DigitalOcean vs. AWS)

| Cost Category | Hetzner Cloud CPX31 (Estimate) | DigitalOcean Droplet (Estimate) | AWS EC2 t4g.xlarge (Estimate) | Notes & Assumptions |
| :--- | :--- | :--- | :--- | :--- |
| **Compute & Memory (4 vCPU / 8 GB RAM)** | €13.50 – €15.00 / mo (~$14.50 – $16.50) | $48.00 / mo | ~$48.50 / mo (t4g.xlarge 3-yr Savings or on-demand $58/mo) | Baseline server hardware allocation. |
| **Primary NVMe Storage** | Included (160 GB NVMe) | Included (160 GB SSD) | ~$6.50 / mo (80 GB gp3 @ $0.08/GB) | Fast root filesystem and database volume. |
| **Host Automated Server Backups** | ~€2.70 – €3.00 / mo (~$3.00 – $3.30) | $9.60 / mo (20% of droplet fee) | ~$4.00 / mo (EBS snapshots via Data Lifecycle Manager) | Full host-level system restore snapshot. |
| **Network Egress / Bandwidth** | €0.00 (20 TB included) | $0.00 (5 TB included) | ~$2.00 – $5.00 / mo ($0.09/GB egress) | Application traffic and API responses. |
| **Offsite Encrypted Backup Storage** | ~$1.00 / mo (Cloudflare R2 / AWS S3) | ~$1.00 / mo (DO Spaces / R2) | ~$1.00 / mo (S3 Standard / Glacier) | ~50 GB retained snapshots with zero egress on R2. |
| **Domain Registration & DNS** | ~$1.25 / mo ($15/yr domain) | ~$1.25 / mo ($15/yr domain) | ~$1.25 / mo ($15/yr domain) | Cloudflare Free DNS (zero monthly cost). |
| **Uptime & Health Monitoring** | $0.00 (Self-hosted Prometheus + free UptimeRobot) | $0.00 | $0.00 (Self-hosted Prometheus + CloudWatch alarms) | External ping monitoring and alert notifications. |
| **Estimated Total Monthly Baseline** | **~$20.00 – $25.00 / month** | **~$59.85 – $65.00 / month** | **~$63.25 – $75.00 / month** | **All prices are engineering estimates, not contracted quotes.** |

### 4.2 Ancillary Service Costs (Variable Usage)
- **LLM API Tokens (OpenRouter / DeepSeek):** Billed directly per token ($0.14/M input, $0.28/M output). A standard research run uses ~40k tokens (~$0.01 – $0.02 per report).
- **SSL / TLS Certificates:** $0.00 (Automated Let's Encrypt / ZeroSSL via Caddy).

---

## 5. Cost Summary & Budget Recommendation

1. **Prudent Launch Target:** Hetzner Cloud CPX31 provides the most cost-effective foundation at **~$20 – $25/month fully loaded** (including host backups and offsite R2 replication).
2. **Domestic US Requirement:** If organizational requirements mandate US Tier-1 hosting, DigitalOcean at **~$60/month** or AWS at **~$70/month** represents the appropriate allocation.
3. **Budget Variance Buffer:** Stakeholders should budget a 15–20% buffer above these estimates to accommodate variable network spikes or accelerated database snapshot retention.
