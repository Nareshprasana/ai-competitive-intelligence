# ACIS Deployment Platform Comparison

**Project:** AI Competitive Intelligence System (ACIS)  
**Document:** Deployment Platform & Cloud Infrastructure Evaluation  
**Target Release:** Phase 4 Production Foundation  
**Assessment Date:** November 2026

---

## 1. Evaluation Context & Constraints

The deployment platform choice must respect core project constraints:
1. **Limited Initial Budget:** Avoid high recurring cloud baselines before customer traction is established.
2. **Resource Efficiency:** The entire stack (Next.js, FastAPI, PostgreSQL, and proxy) requires approximately 2–4 vCPU and 4–8 GB RAM for initial production.
3. **Security Invariants:** Strict network isolation (no public PostgreSQL), HTTPS/TLS 1.3 termination, encrypted storage, and tenant isolation must be guaranteed regardless of platform.
4. **Minimal Operational Burden:** A small engineering team cannot spend significant hours managing Kubernetes clusters or complex multi-cloud VPCs.

---

## 2. Comparative Matrix of Deployment Options

| Criteria | Option 1: Hardened Single VPS with Docker Compose | Option 2: Managed PaaS (Render / Railway / Fly.io) | Option 3: Hybrid (Managed PostgreSQL + VPS / App Runner) | Option 4: Full Cloud (AWS EKS / GCP GKE - Kubernetes) |
| :--- | :--- | :--- | :--- | :--- |
| **Hosting Target** | Hetzner Cloud / DigitalOcean / Linode / AWS EC2 | Railway / Render / Fly.io | Managed DB (Supabase / RDS / Neon) + Host | AWS EKS / GCP GKE |
| **Estimated Monthly Cost** | **$12 – $25 / month** (Hetzner: ~$14/mo for 4 vCPU / 8GB RAM; DO: $24/mo) | **$35 – $75 / month** (Billed per container memory & build minutes) | **$45 – $90 / month** ($25 DB + $20–$40 compute) | **$150 – $350+ / month** ($75 cluster control plane + nodes + NAT) |
| **Compute & Memory Fit** | Excellent. Full dedicated allocation; zero container sleeping or cold starts. | Good. Auto-scaling options, but memory limits can trigger sudden OOM restarts during PDF generation. | Very good. Isolates DB memory from application workloads. | Massive overkill for current scale. |
| **PostgreSQL Reliability** | High, provided automated `pg_dump` and offsite backup sync are configured. Operator responsible for OS updates. | Moderate to High. Automated backups provided by PaaS, but connection pooling limits apply. | **Highest.** Automated failover, PITR, automated security patching, zero DB ops. | High, but complex operators required (CloudNativePG / Zalando). |
| **Network & Security Isolation** | **Complete.** Internal Docker bridge networks with zero public DB port exposure; local UFW firewall. | Moderate. Services share PaaS internal networks, but public DB exposure is common if not carefully restricted. | **Very High.** Private VPC peering or SSL-enforced connection strings with IP allowlisting. | Complex. Requires NetworkPolicies, Calico, SecurityGroups, and IAM roles. |
| **Deployment Complexity** | **Low.** Simple `docker compose up -d` triggered via SSH or GitHub Actions runner. | **Lowest.** Git push to deploy; automated preview environments. | **Low to Moderate.** Deploy DB via managed console; deploy apps via Compose. | **Very High.** Helm charts, Ingress controllers, cert-manager, PVCs, YAML sprawl. |
| **Operational Maintenance** | Moderate. Requires automated Linux security updates (`unattended-upgrades`) and backup monitoring. | Low. Managed infrastructure, automated platform updates. | Low. Managed DB relieves primary operational burden. | **Extreme.** Kubernetes control plane upgrades, node pool rotation, CNI maintenance. |
| **Suitability for Initial Release** | **PRIMARY RECOMMENDATION (Budget-Conscious & Self-Contained)** | Viable Alternative (Rapid prototype) | **RECOMMENDED ALTERNATIVE (If Managed DB is Preferred)** | **REJECTED (Premature Overhead)** |

---

## 3. In-Depth Platform Analysis

### Option 1: Hardened Single VPS with Docker Compose (Recommended Primary)
- **Architecture:** A single virtual private server (e.g., Hetzner CPX31: 4 vCPU, 8 GB RAM, 160 GB NVMe SSD @ ~$14.50/mo; or DigitalOcean 4GB droplet @ $24/mo).
- **Service Composition:** Docker Compose runs Caddy/NGINX, FastAPI backend, Next.js frontend, and PostgreSQL 18 + pgvector.
- **Advantages:**
  - **Exceptional Price-to-Performance:** Full hardware control with fast local NVMe storage and high bandwidth (20TB included).
  - **Zero Vendor Lock-in:** The entire deployment is encapsulated in standard `Dockerfile` and `docker-compose.yml` configurations that can be migrated between any host in minutes.
  - **Predictable Costs:** Flat monthly fee with no unexpected egress or API bill spikes.
  - **Self-Contained Isolation:** Internal Docker bridge network guarantees that PostgreSQL is physically unreachable from the public internet.
- **Drawbacks:**
  - Single point of failure (hardware/host outage). Mitigated by offsite encrypted backups and fast scripted re-provisioning (<1 hour RTO).
  - Operator must manage host OS security patches.

### Option 2: Managed PaaS (Render / Railway)
- **Architecture:** Next.js deployed as a web service; FastAPI deployed as a backend web service; managed PostgreSQL provisioned via PaaS dashboard.
- **Advantages:**
  - One-click Git deploy, instant branch preview environments.
  - No Linux OS administration required.
- **Drawbacks:**
  - Disproportionate cost scaling as memory needs grow (PDF compilation and LangGraph execution require memory headroom).
  - Free/cheap tiers experience cold starts or strict connection pool limits.
  - Vendor lock-in to proprietary PaaS networking models.

### Option 3: Hybrid (Managed PostgreSQL + Compute VPS / App Runner)
- **Architecture:** Managed PostgreSQL via Supabase, Neon, or AWS RDS ($25–$35/mo) combined with an application container host (VPS or AWS App Runner / GCP Cloud Run).
- **Advantages:**
  - Database reliability, automated point-in-time recovery (PITR), and automated security patching are fully offloaded to specialized DB providers.
  - Application servers can be destroyed, recreated, or scaled horizontally without risking state or persistence.
- **Drawbacks:**
  - Slightly higher monthly baseline ($50–$80/mo).
  - Cross-network latency between compute host and database provider if not in the same cloud region.

### Option 4: Full Cloud & Kubernetes (AWS EKS / GCP GKE)
- **Evaluation:** **Firmly Rejected for Phase 4.**
- **Rationale:** A full Kubernetes deployment introduces a minimum baseline cost of $150–$300/month just for idle control planes, load balancers, and NAT gateways. It introduces immense configuration complexity (Helm charts, ingress controllers, certificate managers, CSI storage drivers) without any demonstrated traffic need.

---

## 4. Final Architectural Recommendation & Migration Path

### Phase 4 Initial Deployment: **Option 1 (Hardened VPS with Docker Compose)**
- **Target Host:** 4 vCPU, 8 GB RAM Linux VM (Ubuntu 24.04 LTS) hosted on Hetzner Cloud or DigitalOcean.
- **Configuration:** Caddy (automated TLS), Next.js standalone container, FastAPI Gunicorn container, PostgreSQL 18 container with persistent volume.
- **Backup Target:** Nightly encrypted `pg_dump` synced to Cloudflare R2 or AWS S3 (cost: <$1/month).
- **Total Initial Infrastructure Cost:** **$15 – $25 / month.**

### Future Migration Triggers (Evolution to Option 3 or Multi-Node):
1. **Trigger A (Database Scale):** When active database size exceeds 20 GB or transaction volume requires dedicated HA failover -> Migrate PostgreSQL to AWS RDS / Supabase; keep application containers on compute host.
2. **Trigger B (High Traffic / Multi-Region):** When monthly active users exceed 5,000 or high concurrency causes CPU saturation -> Split frontend and backend onto horizontally scaled container instances behind a cloud load balancer (AWS ALB / Cloudflare).
