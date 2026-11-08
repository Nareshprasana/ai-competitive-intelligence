# ACIS Resource and Cost Estimates

**Project:** AI Competitive Intelligence System (ACIS)  
**Document:** Resource Allocation & Infrastructure Cost Modeling  
**Target Release:** Phase 4 Production Foundation  
**Assessment Date:** November 2026  
**Disclaimer:** All figures are operational engineering estimates based on current software architecture and market pricing as of late 2026.

---

## 1. Application Resource Consumption Breakdown

Based on empirical test profiles, container footprints, and application workload analysis:

| Component | Minimum Required RAM | Recommended Production RAM | Typical CPU Usage | Peak CPU Workload | Disk Footprint |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Next.js Frontend (Standalone)** | 250 MB | 512 MB – 1 GB | 2–5% idle / SSR | 30–50% during heavy SSR page render | ~200 MB container image |
| **FastAPI Backend (Gunicorn/Uvicorn)** | 512 MB | 1.5 GB – 2 GB | 5–10% idle | 60–80% during PDF generation & LangGraph runs | ~400 MB container image |
| **PostgreSQL 18 + pgvector** | 512 MB | 1.5 GB – 2 GB | 2–5% idle | 40–60% during complex analytical queries & vector indexing | 10 GB base + 1–5 GB / month growth |
| **Reverse Proxy (Caddy / NGINX)** | 50 MB | 128 MB | <1% | 5–10% under high SSL handshake concurrency | ~50 MB container image |
| **Artifact Storage (PDFs/Markdown)** | N/A (Disk only) | N/A | Negligible I/O | Negligible I/O | ~2–5 MB per generated research report |
| **Monitoring (Prometheus/Grafana)** | 200 MB | 512 MB | 1–3% | 5–10% during metric aggregation | ~5–10 GB metric storage |
| **Total Stack Footprint** | **~1.5 GB RAM** | **~4.5 – 6.0 GB RAM** | **10–20% baseline** | **Peak bursts up to 2–3 Cores** | **~30–50 GB total disk** |

---

## 2. Container Resource Limits & Reservations (Docker Compose)

To prevent noisy-neighbor starvation, memory leaks, or container crashes from destabilizing the host, Docker Compose must enforce explicit resource reservations and hard limits:

```yaml
services:
  reverse_proxy:
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 256M
        reservations:
          cpus: '0.10'
          memory: 64M

  frontend:
    deploy:
      resources:
        limits:
          cpus: '1.00'
          memory: 1024M
        reservations:
          cpus: '0.25'
          memory: 256M

  backend:
    deploy:
      resources:
        limits:
          cpus: '2.00'
          memory: 2560M
        reservations:
          cpus: '0.50'
          memory: 512M

  postgres:
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

## 4. Multi-Provider Monthly Cost Modeling

### 4.1 Tier 2: Recommended Initial Production (4 vCPU, 8 GB RAM)

| Provider | Infrastructure Breakdown | Compute & Storage Cost | Backup & Bandwidth Cost | Estimated Total Monthly Cost |
| :--- | :--- | :--- | :--- | :--- |
| **Hetzner Cloud (Recommended)** | CPX31 Instance (4 vCPU AMD, 8 GB RAM, 160 GB NVMe SSD, 20 TB Egress, Falkenstein/Helsinki/Ashburn) | €13.50 (~$14.50) / mo | €1.00 (Offsite S3/R2 backup storage) | **~$15.50 / month** |
| **DigitalOcean** | Standard Droplet (4 vCPU, 8 GB RAM, 160 GB SSD, 5 TB Egress) | $48.00 / mo | $5.00 (DO Spaces offsite backup) | **~$53.00 / month** |
| **Linode / Akamai** | Dedicated 4GB / Shared 8GB (4 vCPU, 8 GB RAM, 160 GB SSD) | $40.00 / mo | $5.00 (Object storage) | **~$45.00 / month** |
| **AWS (EC2 + EBS)** | `t4g.xlarge` (4 vCPU ARM Graviton, 8 GB RAM) + 80 GB gp3 EBS volume | ~$58.00 / mo | ~$3.00 (S3 Standard backups + Egress) | **~$61.00 / month** |
| **GCP (Compute Engine)** | `e2-standard-2` (2 vCPU, 8 GB RAM) + 80 GB Balanced Persistent Disk | ~$65.00 / mo | ~$4.00 (GCS backups) | **~$69.00 / month** |

### 4.2 Ancillary Service Costs (All Tiers)
- **Domain Name Registration:** ~$12.00 / year (~$1.00 / mo).
- **DNS & DDoS Protection (Cloudflare Free Tier):** $0.00 / mo.
- **SSL / TLS Certificates (Let's Encrypt / ZeroSSL):** $0.00 / mo.
- **Offsite Encrypted Backup Storage (Cloudflare R2 or AWS S3):** ~$0.50 – $2.00 / mo (billed at ~$0.015/GB/month for ~50 GB retained).
- **LLM API Usage (OpenRouter / DeepSeek):** Variable usage-based ($0.14 per 1M input tokens, $0.28 per 1M output tokens; typically ~$0.01 – $0.03 per completed competitive research report).

---

## 5. Cost Summary & Budget Recommendation

1. **Bootstrap / Initial Launch:** Deploying on **Hetzner Cloud CPX31 (4 vCPU, 8 GB RAM)** delivers enterprise-grade performance for **~$15.50 / month total infrastructure cost**, achieving over **75% savings** compared to equivalent AWS/GCP footprints without sacrificing security or isolation.
2. **US-Only / Enterprise Requirement:** If organizational compliance mandates domestic Tier-1 cloud presence, **DigitalOcean ($53/mo)** or **AWS t4g.xlarge ($61/mo)** serves as the direct alternative.
3. **No Unpredictable Cloud Surprises:** Running all services inside dedicated Docker Compose containers with local persistent volumes avoids surprise fees from serverless invocations, load balancer hourly fees, or NAT gateway egress bandwidth.
