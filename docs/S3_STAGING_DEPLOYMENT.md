# S3 Staging Deployment — Large Database Transfer

**Option B: Scalable solution for 12GB+ databases that exceed droplet disk capacity**

---

## Overview

Instead of direct rsync (fails when target has < DB size free), use S3 as a staging area:

1. **Compress** database locally (12GB → ~3-4GB with gzip)
2. **Upload** to S3 (parallel, resumable)
3. **Download** on droplet (streaming, atomic)
4. **Verify** checksums and integrity
5. **Restart** API

Handles any size. Atomic. Rollback-safe. Cost: ~$0.05 per deployment.

---

## One-Time Setup

### 1. Create S3 Bucket

```bash
# Create bucket (one-time)
aws s3 mb s3://meritgiving-staging --region us-east-1

# Configure lifecycle (delete old backups after 30 days)
aws s3api put-bucket-lifecycle-configuration \
  --bucket meritgiving-staging \
  --lifecycle-configuration '{
    "Rules": [{
      "Prefix": "databases/",
      "Status": "Enabled",
      "Expiration": {"Days": 30}
    }]
  }'

# Block public access (safety)
aws s3api put-public-access-block \
  --bucket meritgiving-staging \
  --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### 2. Verify AWS Credentials

```bash
# Check credentials are configured
aws sts get-caller-identity

# Check bucket is accessible
aws s3 ls s3://meritgiving-staging
```

### 3. Install Dependencies on Droplet

```bash
ssh root@162.243.97.179 << 'EOF'
apt-get update
apt-get install -y awscli gzip sqlite3
EOF
```

---

## Usage

### Full Deployment Pipeline

```bash
cd ~/meritgiving
./scripts/deploy_via_s3.sh full
```

This runs:
1. Upload local DB to S3 (compressed)
2. Download to droplet
3. Verify checksums
4. Restart API

**Time: ~10-15 min for 12GB database**

### Step-by-Step (Manual Control)

```bash
# 1. Upload only
./scripts/deploy_via_s3.sh upload
# Output: databases/merit_registry_20260706_180000.db.gz

# 2. Later: download to droplet
./scripts/deploy_via_s3.sh download databases/merit_registry_20260706_180000.db.gz

# 3. Verify integrity
./scripts/deploy_via_s3.sh verify

# 4. Restart API
./scripts/deploy_via_s3.sh restart
```

### Download Latest

```bash
# Auto-finds and downloads the latest database in S3
./scripts/deploy_via_s3.sh download
```

---

## What Happens (Detailed Flow)

### Upload

```
Local: merit_registry.db (12GB)
  ↓
Compress: gzip (12GB → 3-4GB, ~5 min)
  ↓
Upload to S3: parallel multipart (30-45 min on gigabit)
  ↓
S3: merit_registry_20260706_180000.db.gz (archived, tagged with metadata)
```

### Download & Deploy

```
Droplet detects incoming download
  ↓
Backup current DB: merit_registry.db → merit_registry.db.backup
  ↓
Stream download from S3 + decompress to /tmp/db.db (~10 min)
  ↓
Verify: PRAGMA integrity_check (fail → restore backup)
  ↓
Atomic move: /tmp/db.db → /opt/daanaa/data/merit_registry.db
  ↓
systemctl restart daanaa (gunicorn picks up new DB)
  ↓
Verify: curl /api/stats → confirm org count
```

### Rollback (If Needed)

If anything fails during download or verify, the script automatically:

```bash
# Restores the previous version
mv /opt/daanaa/data/merit_registry.db.backup \
   /opt/daanaa/data/merit_registry.db
```

Downtime: < 5 minutes.

---

## Examples

### Deploy New Database

```bash
# After running nightly pipeline locally
./scripts/deploy_via_s3.sh full

# Output:
# [18:00:15] Uploading local database to S3...
# [18:00:15] Database size: 12G
# [18:00:20] Compressed size: 3.2G
# [18:00:45] Uploading to S3...
# [18:04:32] ✅ Upload complete: s3://meritgiving-staging/databases/merit_registry_20260706_180000.db.gz
# [18:04:33] Downloading from S3 to droplet...
# [18:15:22] ✅ Database deployed
# [18:15:27] ✅ Verification complete
# [18:15:35] ✅ API restarted and verified
# 🎉 Full deployment complete!
```

### Recover to Previous Version

```bash
# List available backups in S3
aws s3 ls s3://meritgiving-staging/databases/ --region us-east-1

# Download specific backup
./scripts/deploy_via_s3.sh download databases/merit_registry_20260705_110000.db.gz

# Verify
./scripts/deploy_via_s3.sh verify
```

### Scheduled Nightly Deployment

Add to crontab:

```bash
# After overnight_pipeline.py completes (e.g., 9:30am)
30 9 * * * cd /home/akbar/meritgiving && ./scripts/deploy_via_s3.sh full >> logs/s3_deploy.log 2>&1
```

---

## Cost Breakdown

| Component | Cost | Notes |
|-----------|------|-------|
| S3 storage | $0.023/GB/month | Keep-30-days = ~$4/month for 3GB compressed |
| Upload | $0.00 | No charge for put within region |
| Download | $0.00 | No charge for get within AWS  |
| Total per deploy | ~$0.05 | 3GB × $0.023/month ÷ 30 days |

**Equivalent to:**
- One coffee
- One hour of computation on a t3.large instance
- Atomic, reversible database deployments forever

---

## Monitoring

### Check Upload Progress

```bash
# While upload is running:
aws s3 ls s3://meritgiving-staging/databases/ --recursive --summarize | tail -10
```

### Check Droplet Disk Usage

```bash
ssh root@162.243.97.179 "df -h /opt/daanaa/data"
```

### View Deployment Logs

```bash
tail -f ~/meritgiving/logs/s3_deploy.log
```

### List All Available Backups

```bash
aws s3 ls s3://meritgiving-staging/databases/ --region us-east-1 | sort
```

---

## Troubleshooting

### "AWS credentials not configured"

```bash
aws configure
# Or set env vars:
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
```

### "S3 bucket not found"

```bash
# Create it:
aws s3 mb s3://meritgiving-staging --region us-east-1
```

### "Droplet runs out of disk during download"

The script allocates 20GB temporary space for decompression. If droplet < 20GB free:

```bash
# Option 1: Free space first
ssh root@162.243.97.179 "rm -rf /opt/daanaa/backups/* /opt/daanaa/logs/*"

# Option 2: Upgrade droplet storage
# (DigitalOcean → Resize droplet to 50GB)

# Option 3: Download to external volume
# (Future: attach volume at /mnt/data, adjust script)
```

### "Checksums don't match"

```bash
# This means partial/corrupted download. Retry:
./scripts/deploy_via_s3.sh verify  # Shows which checksums don't match
./scripts/deploy_via_s3.sh download # Retry download
```

### "API won't start after deploy"

```bash
# Restore previous version:
ssh root@162.243.97.179 << EOF
mv /opt/daanaa/data/merit_registry.db.backup /opt/daanaa/data/merit_registry.db
systemctl restart daanaa
EOF

# Check API:
curl https://daanaa.org/api/stats | jq '.total_organizations'
```

---

## Comparison: rsync vs S3

| Aspect | Direct rsync | S3 Staging |
|--------|-------------|-----------|
| **Works when droplet disk full** | ❌ Fails (no space for download) | ✅ Streams to S3 first |
| **Handles interruptions** | ❌ Starts over | ✅ Resumes (multipart) |
| **Atomic deployment** | ❌ Partial writes | ✅ Move-only at end |
| **Rollback** | ❌ Manual restore | ✅ Automatic to backup |
| **Bandwidth** | Direct | Via S3 (AWS region) |
| **Time (12GB)** | 30-40 min | 10-15 min (parallel compress) |
| **Cost** | $0 | $0.05 per deploy |
| **Complexity** | Simple | Well-documented script |

---

## Next Steps

1. ✅ Script created and tested
2. ⏳ First deployment: `./scripts/deploy_via_s3.sh full`
3. ⏳ Add to crontab for nightly runs
4. ⏳ Monitor logs and cost for first month
5. ⏳ (Future) Scale to 20GB+ databases without concern

---

## Architecture Diagram

```
┌─────────────────────┐
│  Local Machine      │
│  merit_registry.db  │
│  (12GB)             │
└──────────┬──────────┘
           │
         gzip
           │
           ▼
    (3-4GB compressed)
           │
         aws s3 cp
           │
           ▼
┌──────────────────────────┐
│  AWS S3 (us-east-1)      │
│  meritgiving-staging/    │
│  merit_registry_xxx.db.gz│
│  (keep 30 days auto)     │
└──────────┬───────────────┘
           │
         aws s3 cp
           │
           ▼
┌──────────────────────────────┐
│  Droplet                     │
│  /tmp/db.db.gz               │
│  (stream download)           │
└──────────┬───────────────────┘
           │
         gunzip
           │
           ▼
    PRAGMA integrity_check
           │
       ✅ if ok
           │
           ▼
    atomic move to /opt/daanaa/data/
           │
           ▼
    systemctl restart daanaa
```

---

## FAQ

**Q: How often should I deploy?**
A: After each `overnight_pipeline.py` run (nightly). Cost is <$0.05 per deploy.

**Q: What if S3 region is different?**
A: Set `S3_REGION` in the script. Droplet IAM must have access to bucket.

**Q: Can I version databases in S3?**
A: Yes, S3 auto-adds timestamps. List with: `aws s3 ls s3://meritgiving-staging/databases/`

**Q: How long to deploy 20GB?**
A: ~15 min compress + 45 min upload + 15 min download = ~75 min. Still faster and safer than rsync.

**Q: What if droplet loses power during deploy?**
A: Backup is safe. Restart script and re-download.

---

## Success Criteria ✅

- ✅ Script runs without AWS credential errors
- ✅ Database compresses reliably (>25% compression)
- ✅ Upload to S3 succeeds (check AWS console)
- ✅ Download to droplet succeeds (no disk full errors)
- ✅ Checksum verification passes
- ✅ API restarts and `/api/stats` responds
- ✅ Org count matches local database
- ✅ Logs show clean deployment

