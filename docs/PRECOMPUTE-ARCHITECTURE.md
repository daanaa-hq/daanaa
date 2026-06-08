# Pre-Computed Results Architecture

## Overview

This document describes the new weekly pre-computed results system that replaces live database queries with fast, static file serving. This reduces response times from 2-10 seconds to 50-200ms across the site.

**Status:** Scripts created, ready for Phase 1 execution. Estimated Phase 1 (home server): ~1 hour. Phase 2 (droplet setup): ~30 min.

---

## Architecture

### Two-Server Design

```
HOME SERVER (Private, Ryzen 9700X + R9700)
├─ Full 19GB merit_registry.db with embeddings
├─ Weekly pre-compute (Sunday 22:00)
├─ Outputs: ~/meritgiving/precompute_output/
│  ├─ browse/ (100MB) — all category/state combos, paginated
│  ├─ orgs/ (3.2GB) — all 1.8M org details + similar orgs
│  ├─ content/ (50MB) — homepage, methodology, guides, etc.
│  ├─ faiss_index.bin (300MB) — semantic search index
│  └─ ein_map.json.gz — index to EIN mapping
└─ Archive & upload (Sunday 23:00)
   └─ precompute_YYYYMMDD_HHMMSS.tar.gz (~1GB gzipped)
       scp to → 162.243.97.179:/opt/daanaa/staging/

DROPLET (Public, 33GB DigitalOcean)
├─ Minimal Flask API (droplet_api.py)
├─ Weekly deploy (Sunday 23:30)
│  ├─ Receive archive
│  ├─ Verify checksum
│  ├─ Extract & health check
│  ├─ Atomic swap (v1→v0, v2→v1)
│  └─ Restart API
├─ Data directories:
│  ├─ /data/precompute/v0/ (7 days old — rollback point)
│  ├─ /data/precompute/v1/ (LIVE)
│  └─ /data/claims/ (daily org_claims exports)
└─ Serves all endpoints as static JSON
   GET /api/organizations?ntee=A&state=CA&page=1
   GET /api/organizations/{EIN} (+ merged claims)
   GET /api/search?q=query (via FAISS)
   GET /api/sector-health, /api/guides, etc.
```

### Data Flow

```
Sunday 22:00 on Home Server:
  registry_enriched (1.8M orgs)
    ↓
  [precompute_browse.py]    → /browse/{NTEE1}/{STATE}_{PAGE}.json.gz
  [precompute_orgs.py]      → /orgs/{EIN_PREFIX}/{EIN}.json.gz
  [precompute_content.py]   → /content/{page_name}.json.gz
  [build_faiss_index.py]    → /faiss_index.bin, /ein_map.json.gz
    ↓
  [run_precompute.sh]       → Archives to precompute_*.tar.gz
    ↓
  scp to Droplet:/opt/daanaa/staging/

Sunday 23:00 on Home Server:
  Monitor upload completion
    ↓

Sunday 23:30 on Droplet:
  [deploy_droplet.sh] receives archive
    ↓
  Verify checksum
  Extract to temp dir
  Health checks (parse sample files, load FAISS)
    ↓
  Atomic swap:
    /data/precompute/v0 ← remove old backup
    /data/precompute/v1 ← /data/precompute/v0 (7-day backup)
    /tmp/staging → /data/precompute/v1 (LIVE)
    ↓
  Restart Flask API
  Verify health endpoint
    ↓
  Success! API now serving ~3.8GB static results

Daily (Droplet - automated):
  [org_claims table] → changes
    ↓
  Export daily claims to /data/claims/{EIN}.json
    ↓
  On GET /api/organizations/{EIN}:
    Load base org from /orgs/{EIN}.json.gz
    Merge any claims from /claims/{EIN}.json
    Return merged result
```

---

## Phase 1: Home Server Pre-Compute (Scripts Created)

### Scripts

All scripts are in `scripts/`:

| Script | Purpose | Input | Output | Time |
|--------|---------|-------|--------|------|
| `precompute_browse.py` | Export all category/state browse combos | registry_enriched | ~/precompute_output/browse/ (100MB) | 5-10 min |
| `precompute_orgs.py` | Export all 1.8M org details + similar | registry_enriched + org_embeddings | ~/precompute_output/orgs/ (3.2GB) | 15-25 min |
| `precompute_content.py` | Export static content pages | registry_enriched | ~/precompute_output/content/ (50MB) | <1 min |
| `build_faiss_index.py` | Build semantic search index | org_embeddings | ~/precompute_output/faiss_index.bin (300MB) | 5-10 min |
| `run_precompute.sh` | Master orchestration + archive | all above | ~/precompute_archive/precompute_YYYYMMDD.tar.gz (1GB) | ~45 min total |

### Running Phase 1

```bash
# 1. On home server, activate venv and run orchestration
cd ~/meritgiving
source venv/bin/activate
bash scripts/run_precompute.sh

# This will:
# - Run all 4 pre-compute scripts sequentially
# - Create ~/precompute_output/ with browse/, orgs/, content/, FAISS files
# - Archive to ~/precompute_archive/precompute_YYYYMMDD_HHMMSS.tar.gz
# - Generate SHA256 checksum
# - Print upload instructions

# 2. Monitor output
# Watch for:
# - "Pre-compute complete!" ✓
# - Archive size (~1GB gzipped)
# - Checksum printed
```

### Expected Output Structure

```
~/meritgiving/precompute_output/
├── browse/
│   ├── A/
│   │   ├── CA_1.json.gz
│   │   ├── CA_2.json.gz
│   │   ├── NY_1.json.gz
│   │   └── ...
│   ├── B/
│   │   └── ...
│   └── [Z]/
│       └── ...
├── orgs/
│   ├── 000/
│   │   ├── 000000001.json.gz
│   │   ├── 000000002.json.gz
│   │   └── ...
│   ├── 001/
│   │   └── ...
│   └── [ZZZ]/
│       └── ...
├── content/
│   ├── homepage.json.gz
│   ├── methodology.json.gz
│   ├── sector_health.json.gz
│   ├── how_it_works.json.gz
│   ├── guides.json.gz
│   ├── faqs.json.gz
│   ├── about.json.gz
│   └── legal.json.gz
├── faiss_index.bin (300MB)
└── ein_map.json.gz

~/meritgiving/precompute_archive/
└── precompute_20260605_220000.tar.gz (1GB)
    └── precompute_20260605_220000.tar.gz.sha256
```

### Data Sizes

| Component | Size | # Files | Notes |
|-----------|------|---------|-------|
| browse/ | 100MB | ~3,250 files (26 cats × 50 states, paginated) | Gzipped JSON |
| orgs/ | 3.2GB | 1,811,930 files | Gzipped JSON + similar orgs |
| content/ | 50MB | 8 files | Gzipped JSON |
| faiss_index.bin | 300MB | 1 file | Binary FAISS index |
| ein_map.json.gz | 50MB | 1 file | EIN → index mapping |
| **Total** | **3.8GB** | | Expands to ~12GB when extracted |

---

## Phase 2: Droplet Deployment (Scripts Ready)

### Pre-Deployment Setup (Droplet, one-time)

```bash
# SSH to droplet
ssh root@162.243.97.179

# Create directories
mkdir -p /opt/daanaa/staging /data/precompute /data/claims

# Copy deployment script
scp ~/meritgiving/scripts/deploy_droplet.sh root@162.243.97.179:/opt/daanaa/scripts/

# Set up systemd service for droplet_api.py (see next section)
# Copy droplet_api.py to /opt/daanaa/app/droplet_api.py
```

### Deployment Steps

```bash
# 1. On home server, upload archive to droplet
scp ~/meritgiving/precompute_archive/precompute_YYYYMMDD.tar.gz \
    root@162.243.97.179:/opt/daanaa/staging/
scp ~/meritgiving/precompute_archive/precompute_YYYYMMDD.tar.gz.sha256 \
    root@162.243.97.179:/opt/daanaa/staging/

# 2. SSH to droplet and run deployment
ssh root@162.243.97.179
bash /opt/daanaa/scripts/deploy_droplet.sh /opt/daanaa/staging/precompute_YYYYMMDD.tar.gz

# Deployment will:
# - Verify checksum
# - Extract to /tmp
# - Run health checks (parse browse files, load FAISS)
# - Stop API
# - Swap: v1 → v0, v2 → v1
# - Restart API
# - Verify health endpoint
# - Print rollback instructions

# 3. Test from home server
curl -s http://162.243.97.179:5000/health | jq .
curl -s http://162.243.97.179:5000/api/stats | jq '.total_organizations'
```

### Droplet API Service Configuration

Create `/etc/systemd/system/daanaa.service`:

```ini
[Unit]
Description=Daanaa API (Pre-Computed Results)
After=network.target
Restart=on-failure
RestartSec=5s

[Service]
Type=simple
User=app
WorkingDirectory=/opt/daanaa/app
Environment="FLASK_ENV=production"
ExecStart=/usr/bin/python3 /opt/daanaa/app/droplet_api.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable daanaa
sudo systemctl start daanaa
sudo systemctl status daanaa
```

---

## Phase 3: Testing & Verification

### Test 1: Browse Endpoint

```bash
# From home server
curl -s http://162.243.97.179:5000/api/organizations?ntee=A&state=CA&page=1 \
  | jq '.organizations[0] | {EIN, organization_name, merit_tier}'

# Expected: <200ms, returns 25 orgs
```

### Test 2: Org Detail with Similar Orgs

```bash
curl -s http://162.243.97.179:5000/api/organizations/942930591 \
  | jq '.similar_organizations | length'

# Expected: <200ms, returns org + 12 similar orgs
```

### Test 3: Content Pages

```bash
curl -s http://162.243.97.179:5000/api/methodology \
  | jq '.version'

# Expected: "v4.0"
```

### Test 4: Search (FAISS)

```bash
curl -s "http://162.243.97.179:5000/api/search?q=food%20bank" \
  | jq '.total'

# Expected: Query embedding → FAISS NN → load org details → <300ms
```

### Test 5: Load Performance

Use `apache2-utils` or similar:

```bash
# 50 concurrent requests, 1000 total
ab -c 50 -n 1000 'http://162.243.97.179:5000/api/organizations?ntee=A&state=CA&page=1'

# Expected: <200ms 50th percentile, <500ms 95th percentile
```

---

## Daily Updates (Automated)

### Org Claims Export (Droplet)

Daily cron job (0 0 * * *):

```bash
#!/bin/bash
# Export new/updated claims from org_claims table to /data/claims/

sqlite3 /data/merit_registry.db << 'EOF'
  SELECT EIN, status, verified_at, verified_fields
  FROM org_claims
  WHERE updated_at >= date('now', '-1 day')
EOF
```

Each claim saved as `/data/claims/{EIN}.json`:

```json
{
  "ein": "123456789",
  "status": "verified",
  "verified_at": "2026-06-05T12:00:00Z",
  "verified_fields": {
    "mission": "claimed",
    "donate_url": "verified"
  }
}
```

### Merge in GET /api/organizations/{EIN}

In `droplet_api.py`:

```python
def merge_claims(org_data, ein):
    """Merge daily claims into org data if exists."""
    claims_file = CLAIMS_DIR / f"{ein}.json"
    if not claims_file.exists():
        return org_data
    
    with open(claims_file, 'r') as f:
        claims = json.load(f)
        org_data['claim_status'] = claims.get('status')
        org_data['verified_at'] = claims.get('verified_at')
        org_data['verified_fields'] = claims.get('verified_fields', {})
    
    return org_data
```

---

## Rollback & Safety

### Keeping Multiple Versions

On droplet at `/data/precompute/`:

- `v0/` — Previous week (7 days old) — **BACKUP**
- `v1/` — **LIVE**
- `v2/` — Staging (during upload)

### Atomic Swap (Zero Downtime)

```bash
# Before swap
systemctl stop daanaa

# Swap
rm -rf /data/precompute/v0
mv /data/precompute/v1 /data/precompute/v0
mv /tmp/staging /data/precompute/v1

# After swap
systemctl start daanaa
```

### Rollback (30 seconds)

```bash
# If issues detected immediately after swap:
systemctl stop daanaa
rm -rf /data/precompute/v1
mv /data/precompute/v0 /data/precompute/v1
systemctl start daanaa
```

If you want to roll back further (e.g., after 2 days), you'll need a separate backup. Consider automated weekly backup to S3.

---

## Performance Expectations

### Before (Current)

| Endpoint | Time | Why |
|----------|------|-----|
| Browse (25 orgs) | 5-10s | 1.7GB DB query + Gunicorn GC |
| Org detail | 3-5s | org + similar org joins |
| Search | 1.5-2s | 546K embeddings cosine scan |
| Content pages | 2-3s | Aggregation queries |

### After (Pre-Computed)

| Endpoint | Time | Why |
|----------|------|-----|
| Browse (25 orgs) | 50-100ms | Load 2KB gzipped JSON |
| Org detail | 50-150ms | Load 3KB + merge claims |
| Search | 100-300ms | FAISS NN + load 12 orgs |
| Content pages | 50ms | Load 50KB gzipped JSON |

**10-20x faster.** P95 under 500ms across all endpoints.

---

## Troubleshooting

### Pre-Compute Script Fails

```bash
# Check database integrity
sqlite3 ~/meritgiving/data/merit_registry.db "PRAGMA quick_check;" | head

# Check disk space
df -h ~/meritgiving/

# Check embeddings table
sqlite3 ~/meritgiving/data/merit_registry.db "SELECT COUNT(*) FROM org_embeddings;"

# Rerun just the failing script
python3 scripts/precompute_browse.py
```

### Deployment Fails

```bash
# SSH to droplet
ssh root@162.243.97.179

# Check extracted files
ls -la /opt/daanaa/staging/precompute_*/

# Check FAISS index manually
python3 -c "import faiss; idx = faiss.read_index('/opt/daanaa/staging/precompute_*/faiss_index.bin'); print(idx.ntotal)"

# Rollback if needed
bash /opt/daanaa/scripts/deploy_droplet.sh --rollback
```

### API Not Responding

```bash
# Check service
sudo systemctl status daanaa
sudo journalctl -u daanaa -n 50

# Check port
lsof -i :5000

# Verify data directory
ls -la /data/precompute/v1/ | head

# Test health endpoint
curl http://localhost:5000/health
```

---

## Next Steps

### Immediate (Phase 1 - Ready)

1. Run `bash scripts/run_precompute.sh` on home server
2. Monitor output for completion
3. Verify archive size ~1GB
4. Document first run time (for scheduling)

### Short-term (Phase 2 - Ready)

1. Set up droplet directories
2. Install `droplet_api.py` + systemd service
3. Run deployment script
4. Run tests from Phase 3

### Medium-term (Phase 3 - After Verification)

1. Automate home server pre-compute with cron (Sunday 22:00 CST)
2. Automate droplet deployment with cron (Sunday 23:00 CST) or webhook
3. Automate daily claims export (droplet, 00:00 daily)
4. Monitor response times and disk usage

### Long-term (Optimization)

1. Add incremental updates for claims/donations (don't rebuild whole browsee)
2. Cache response files in CDN (Cloudflare)
3. Archive old `v0/` backups to S3 weekly
4. Implement A/B testing framework (serve v0 vs v1 to different users)

---

## Storage Roadmap

```
Current (Live Database):
  Droplet: 1.7GB DB synced nightly

New (Pre-Computed):
  Droplet: 3.8GB × 2 versions (v0 + v1) = 7.6GB
  + room for v2 staging = ~9-10GB

On 33GB Droplet:
  ✓ /data/ (10GB) + /var/lib/ (1GB) + /root/ (1GB) + OS (2GB) = 14GB used, 19GB free

Recommendation:
  Current: 33GB ✓ (fits with breathing room)
  At scale (3M orgs): ~6GB + backups = 12GB (still fits)
  Safe threshold: upgrade to 64GB if adding other services
```

---

## Questions?

See `CLAUDE.md` for architecture notes, `STEWARDSHIP.md` for principles this respects (transparency, small-org parity, data integrity).
