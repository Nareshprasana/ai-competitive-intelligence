# ACIS Deployment Platform Comparison

**Project:** AI Competitive Intelligence System (ACIS)  
**Document:** Deployment Platform & Cloud Infrastructure Evaluation (Audited)  
**Target Release:** Phase 4 Production Foundation  
**Assessment Date:** November 2026

---

## 1. Evaluation Context & Constraints

The deployment platform evaluation balances budget prudence with enterprise security and operational reliability:
1. **Budget Discipline:** Avoid multi-hundred-dollar monthly cloud commitments prior to commercial customer traction.
2. **Resource Sizing:** The full application stack (FastAPI backend, Next.js frontend, research worker, PostgreSQL 18, and Caddy reverse proxy) requires **4 vCPU and 8 GB RAM** for stable production concurrency and PDF compilation.
3. **Security Invariants:** Strict network isolation (no public PostgreSQL), HTTPS/TLS 1.3 termination, encrypted storage, and tenant isolation must be guaranteed regardless of platform.
4. **Minimal Operational Overhead:** A lean engineering team must not be burdened with Kubernetes control plane management or complex multi-cloud VPC networking.

---

## 2. Comparative Matrix of Deployment Options

| Criteria | Option 1: Hardened Single VPS with Docker Compose | Option 2: Managed PaaS (Render / Railway / Fly.io) | Option 3: Hybrid (Managed PostgreSQL + Compute VPS / App Runner) | Option 4: Full Cloud (AWS EKS / GCP GKE - Kubernetes) |
| :--- | :--- | :--- | :--- | :--- |
| **Hosting Target** | Hetzner Cloud / DigitalOcean / Linode / AWS EC2 | Railway / Render / Fly.io | Managed DB (Supabase / RDS / Neon) + Host | AWS EKS / GCP GKE |
| **Estimated Monthly Cost** | **$18 – $28 / month** (Hetzner CPX31 estimate: ~$15–$18 base + backups + R2; DO: $55–$65/mo) | **$45 – $85 / month** (Billed per container memory & execution minutes) | **$55 – $105 / month** ($25–$35 DB + $30–$70 compute) | **$160 – $400+ / month** ($75 cluster control plane + nodes + NAT) |
| **Compute & Memory Fit** | **Excellent.** Dedicated allocation; zero container sleeping or cold starts; ample RAM for PDF exports. | Moderate. OOM risk during concurrent PDF generation without expensive tier upgrades. | Very good. Separates DB memory from application workloads. | Massive overkill for current scale. |
| **PostgreSQL Reliability** | High, provided automated `pg_dump` and offsite backup sync are configured. Operator responsible for OS updates. | Moderate to High. Automated backups provided by PaaS, but connection pooling limits apply. | **Highest.** Automated failover, PITR, automated security patching, zero DB ops. | High, but complex operators required (CloudNativePG / Zalando). |
| **Network & Security Isolation** | **Complete.** Internal Docker bridge networks with zero public DB port exposure; local UFW firewall. | Moderate. Services share PaaS internal networks; requires vigilance against public DB exposure. | **Very High.** Private VPC peering or SSL-enforced connection strings with IP allowlisting. | Complex. Requires NetworkPolicies, Calico, SecurityGroups, and IAM roles. |
| **Deployment Complexity** | **Low.** Simple `docker compose up -d` triggered via SSH or GitHub Actions runner. | **Lowest.** Git push to deploy; automated preview environments. | **Low to Moderate.** Deploy DB via managed console; deploy apps via Compose. | **Very High.** Helm charts, Ingress controllers, cert-manager, PVCs, YAML sprawl. |
| **Operational Maintenance** | Moderate. Requires automated Linux security updates (`unattended-upgrades`) and backup monitoring. | Low. Managed infrastructure, automated platform updates. | Low. Managed DB relieves primary operational burden. | **Extreme.** Kubernetes control plane upgrades, node pool rotation, CNI maintenance. |
| **Suitability for Initial Release** | **PRIMARY RECOMMENDATION (Self-Contained & Cost-Effective)** | Viable Alternative (Rapid prototype) | **RECOMMENDED ALTERNATIVE (If Managed DB is Preferred)** | **REJECTED (Premature Overhead)** |

---

## 3. In-Depth Platform Analysis

### Option 1: Hardened Single VPS with Docker Compose (Recommended Primary)
- **Architecture:** A single virtual private server running Ubuntu 24.04 LTS with Docker Engine and Docker Compose.
- **Service Composition:** Caddy (TLS 1.3), Next.js frontend (standalone), FastAPI backend (Gunicorn/Uvicorn), dedicated research worker, and PostgreSQL 18 with `pgvector`.
- **Advantages:**
  - **Unmatched Price-to-Performance:** Full hardware control with fast local NVMe storage and high bandwidth.
  - **Zero Vendor Lock-in:** The entire deployment is encapsulated in standard `Dockerfile` and `docker-compose.yml` configurations that can be migrated to any host or cloud in minutes.
  - **Predictable Costs:** Flat monthly fee with no unexpected egress or API bill spikes.
  - **Self-Contained Isolation:** Internal Docker bridge network guarantees that PostgreSQL is physically unreachable from the public internet.
- **Drawbacks:**
  - Single point of failure (hardware/host outage). Mitigated by offsite encrypted backups and fast scripted re-provisioning (<1 hour RTO).
  - Operator must manage host OS security patches.

### Option 2: Managed PaaS (Render / Railway / Fly.io)
- **Evaluation:** Viable for rapid staging, but costs scale disproportionately with RAM requirements. Running Next.js, FastAPI, a background research worker, and PostgreSQL requires 4GB+ RAM, easily pushing monthly PaaS costs to $50–$80/month while imposing strict connection limits.

### Option 3: Hybrid (Managed PostgreSQL + Compute VPS / App Runner)
- **Evaluation:** The ideal evolutionary step when active database size exceeds 20 GB or when regulatory compliance mandates managed multi-AZ database replication.
- **Architecture:** Managed PostgreSQL via AWS RDS, Supabase, or Neon combined with an application container host.

### Option 4: Full Cloud & Kubernetes (AWS EKS / GCP GKE)
- **Evaluation:** **Firmly Rejected for Phase 4.**
- **Rationale:** A full Kubernetes deployment introduces a minimum baseline cost of $160–$350/month just for idle control planes, load balancers, and NAT gateways. It introduces immense configuration complexity without any demonstrated traffic need.

---

## 4. Final Architectural Recommendation & Migration Path

### Phase 4 Initial Deployment: **Option 1 (Hardened VPS with Docker Compose)**
- **Target Host:** 4 vCPU, 8 GB RAM Linux VM (Ubuntu 24.04 LTS) hosted on Hetzner Cloud or DigitalOcean.
- **Configuration:** Caddy (automated TLS), Next.js standalone container, FastAPI Gunicorn container, research worker container, PostgreSQL 18 container with persistent volume.
- **Backup Target:** Nightly encrypted `pg_dump` synced to Cloudflare R2 or AWS S3.
- **Estimated Total Infrastructure Cost:** **$18 – $28 / month (Hetzner)** or **$55 – $65 / month (DigitalOcean)**.

### Future Migration Triggers (Evolution to Option 3 or Multi-Node):
1. **Trigger A (Database Scale):** When active database size exceeds 20 GB or transaction volume requires dedicated HA failover -> Migrate PostgreSQL to AWS RDS / Supabase; keep application containers on compute host.
2. **Trigger B (High Traffic / Multi-Region):** When monthly active users exceed 5,000 or high concurrency causes CPU saturation -> Split frontend and backend onto horizontally scaled container instances behind a cloud load balancer (AWS ALB / Cloudflare).
