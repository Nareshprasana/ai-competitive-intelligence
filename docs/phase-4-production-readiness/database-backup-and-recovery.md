# ACIS Database Backup and Disaster Recovery Strategy

**Project:** AI Competitive Intelligence System (ACIS)  
**Document:** Database Backup, Disaster Recovery & Migration Safety  
**Target Release:** Phase 4 Production Foundation  
**Target Engine:** PostgreSQL 18 with `pgvector`

---

## 1. Disaster Recovery Objectives & SLA

Disaster recovery targets are established based on operational reality for the initial production deployment:

| Metric | Initial Production Target (Tier 1) | Advanced Scale Target (Tier 2) | Technical Enabler |
| :--- | :--- | :--- | :--- |
| **Recovery Point Objective (RPO)** | **<= 24 Hours** | **<= 15 Minutes** | Tier 1: Daily logical snapshots (`pg_dump`).<br/>Tier 2: Continuous Write-Ahead Log (WAL) archiving via `pgBackRest` or Barman. |
| **Recovery Time Objective (RTO)** | **<= 1 Hour** | **<= 30 Minutes** | Tier 1: Scripted container restore from compressed logical dump.<br/>Tier 2: Point-In-Time Recovery (PITR) with automated volume attachment. |
| **Integrity Assurance** | **100% Verified** | **100% Verified** | SHA-256 checksums, encrypted at rest (AES-256 / GPG), and periodic dry-run restores into an isolated verification database. |

---

## 2. Backup Architecture & Data Flow

```mermaid
flowchart TD
    subgraph ProductionCluster ["ACIS Production Environment"]
        PGService["PostgreSQL 18 Database Container\n(Database: acis_db, Volume: acis_postgres_data)"]
        CronRunner["Backup Automation Job\n(Systemd Timer / Container Cron)\nExecutes: backup-database.sh"]
        ArtifactsVolume["Artifacts Volume\n(/app/data/artifacts)"]
    end

    subgraph BackupPipeline ["Local Backup Pipeline (/opt/acis/backups)"]
        DumpStep["1. pg_dump -Fc (Custom Format)\nExtracts relational tables, JSONB & pgvector"]
        TarStep["2. tar -czf Artifacts\nArchive tenant report files"]
        ChecksumStep["3. sha256sum Generation\nGenerate cryptographic manifests"]
        EncryptStep["4. GPG / OpenSSL Encryption\nEncrypt archives with AES-256-CBC"]
    end

    subgraph StorageDestinations ["Storage & Offsite Retention"]
        LocalStage["Local Encrypted Archive\n/opt/acis/backups/encrypted/\n(Retained 7 days)"]
        OffsiteCloud["Offsite Secure Object Storage\n(AWS S3 / Cloudflare R2 / GCP GCS)\n- Immutable Object Lock (WORM)\n- Versioning enabled"]
        ColdStorage["Long-term Cold Storage\n(S3 Glacier / Monthly archive)"]
    end

    CronRunner -->|Executes pg_dump| PGService
    CronRunner -->|Archives data| ArtifactsVolume
    PGService --> DumpStep
    ArtifactsVolume --> TarStep
    DumpStep & TarStep --> ChecksumStep --> EncryptStep --> LocalStage
    LocalStage -->|Automated Rclone / AWS CLI Sync| OffsiteCloud
    OffsiteCloud -.->|Lifecycle Rule (30+ days)| ColdStorage

    classDef prod fill:#2e7d32,stroke:#1b5e20,color:#fff;
    classDef pipe fill:#0288d1,stroke:#01579b,color:#fff;
    classDef dest fill:#e65100,stroke:#bf360c,color:#fff;

    class ProductionCluster,PGService,CronRunner,ArtifactsVolume prod;
    class BackupPipeline,DumpStep,TarStep,ChecksumStep,EncryptStep pipe;
    class StorageDestinations,LocalStage,OffsiteCloud,ColdStorage dest;
```

---

## 3. Automated Backup Pipeline Implementation

### 3.1 Logical Backup (`pg_dump`)
- **Format:** Custom PostgreSQL archive format (`-Fc`), enabling parallel restoration, per-table selective extraction, and built-in zlib compression.
- **Command Specification:**
  ```bash
  docker exec -t acis_postgres pg_dump \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -Fc \
    --exclude-table-data='audit_events' \
    -f "/backups/acis_db_${TIMESTAMP}.dump"
  ```
  *(Note: `audit_events` can be dumped in a secondary partition if log volume is extensive).*

### 3.2 Backup Encryption at Rest
- Raw backup dumps must never sit unencrypted on local disks or offsite buckets.
- Every dump is encrypted using symmetric AES-256 or asymmetric GPG public key before transport:
  ```bash
  gpg --symmetric --cipher-algo AES256 --batch --passphrase-file /etc/acis/backup.pass \
    -o "/backups/acis_db_${TIMESTAMP}.dump.gpg" "/backups/acis_db_${TIMESTAMP}.dump"
  ```

### 3.3 Retention Policy (Grandfather-Father-Son)
- **Daily Snapshots (Son):** Retained for **7 days** locally and on remote storage.
- **Weekly Snapshots (Father):** Captured every Sunday; retained for **4 weeks**.
- **Monthly Snapshots (Grandfather):** Captured on the 1st of each month; retained for **12 months**.
- Automated purge scripts run daily, removing expired snapshots according to this lifecycle.

---

## 4. Backup Verification & Usability Testing

> [!CRITICAL]
> A backup file that has never been restored is an untested hypothesis, not a backup.

Verifying that a `.dump` file exists is insufficient; backups can suffer from bit-rot, missing extension binaries (`pgvector`), or decryption failures.

### 4.1 Automated Verification Protocol
Once weekly, an automated or operator-driven restore test is executed against a temporary, isolated database container:
1. **Decryption Verification:** Decrypt the latest backup file using the production decryption key; confirm exit code 0.
2. **Checksum Verification:** Run `sha256sum -c manifest.sha256`; verify hash matches the origin creation hash.
3. **Sandbox Container Provisioning:** Launch an ephemeral verification instance:
   ```bash
   docker run --name acis_restore_test -e POSTGRES_PASSWORD=test_restore_pwd -d ankane/pgvector:latest
   ```
4. **Schema & Data Restoration:**
   ```bash
   docker exec -i acis_restore_test pg_restore -U postgres -d postgres /backups/test.dump
   ```
5. **Integrity Query Validation:** Execute automated SQL assertions verifying key tables and row counts:
   ```sql
   SELECT count(*) FROM alembic_version;       -- Must equal 1
   SELECT count(*) FROM organizations;         -- Must be > 0
   SELECT count(*) FROM users;                 -- Must be > 0
   SELECT count(*) FROM research_records;      -- Must be >= historical baseline
   ```
6. **Teardown:** Destroy the temporary test container and log the verification result with timestamp and operator/runner ID.

---

## 5. Step-by-Step Disaster Recovery Procedure

In the event of database corruption, ransomware, or catastrophic host loss:

### Step 1: Provision Clean Host & Environment
1. Deploy fresh host VM with hardened OS (Ubuntu 24.04 LTS / Debian 12).
2. Install Docker Engine and Docker Compose.
3. Clone repository at the approved release commit (`f658533` or latest production tag).
4. Restore `/opt/acis/.env.production` from secured offline password vault.

### Step 2: Fetch and Decrypt Latest Backup
```bash
# 1. Download latest archive from offsite storage
aws s3 cp s3://acis-offsite-backups/prod/acis_backup_latest.tar.gpg /tmp/

# 2. Decrypt archive
gpg --decrypt --batch --passphrase-file /etc/acis/backup.pass \
  -o /tmp/acis_backup_latest.tar /tmp/acis_backup_latest.tar.gpg

# 3. Extract dump and artifacts
tar -xf /tmp/acis_backup_latest.tar -C /tmp/restore/
```

### Step 3: Initialize Database & Restore Data
```bash
# 1. Start PostgreSQL service in isolation
docker compose up -d postgres

# 2. Wait for database readiness
until docker exec acis_postgres pg_isready -U postgres; do sleep 2; done

# 3. Restore database schema and data
docker exec -i acis_postgres pg_restore \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --clean \
  --if-exists \
  /tmp/restore/acis_db.dump

# 4. Restore file artifacts
mkdir -p /opt/acis/data/artifacts
cp -r /tmp/restore/artifacts/* /opt/acis/data/artifacts/
chown -R 10001:10001 /opt/acis/data/artifacts
```

### Step 4: Verify Application Health & Startup
```bash
# 1. Start full application stack
docker compose up -d

# 2. Verify health endpoint
curl -f http://localhost:8000/api/v1/health

# 3. Verify latest research and login via frontend
```

---

## 6. Database Migration Safety & Rollback Protocol

Alembic migrations must follow a strict zero-downtime safety checklist:

### 6.1 Pre-Migration Gate
1. **Mandatory Snapshot:** An immediate pre-migration snapshot is triggered before `alembic upgrade head` is executed.
2. **Backward-Compatible DDL:**
   - Never drop columns in the same release that removes application code references.
   - Adding columns must always provide default values or permit `NULL`.
   - Index creation on large tables must use `CONCURRENTLY` (or run during low-traffic maintenance windows).

### 6.2 Rollback Protocol
If an Alembic migration encounters an error during deployment:
1. The migration transaction aborts automatically.
2. If partial execution occurred, execute `alembic downgrade -1` or restore from the pre-migration snapshot.
3. Keep the previous application container running until post-migration health probes report HTTP 200.
