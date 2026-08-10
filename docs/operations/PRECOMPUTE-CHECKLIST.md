# Pre-Compute Execution Checklist

## Phase 1: Home Server Pre-Compute

**Time estimate:** ~45 minutes total (browse 5-10m, orgs 15-25m, content <1m, FAISS 5-10m, archive 5m)

### Before Running

- [ ] Home server internet connection stable
- [ ] Disk space: `df -h ~/meritgiving/` shows >20GB free in `/home`
- [ ] Embeddings ready: `sqlite3 ~/meritgiving/data/merit_registry.db "SELECT COUNT(*) FROM org_embeddings;"`
  - Expected: ~1.8M rows
- [ ] Venv activated: `source ~/meritgiving/venv/bin/activate`

### Run Pre-Compute

```bash
cd ~/meritgiving
source venv/bin/activate
bash scripts/run_precompute.sh
```

Expected output:
```
========== PRE-COMPUTE ORCHESTRATION START ==========
Started at: 2026-06-05 14:30:00

Phase 1/4: Pre-computing browse results...
  A: CA processed
  A: NY processed
  ...

Phase 2/4: Pre-computing org detail pages...
  Loaded 1800000 embeddings
  Processed 50000/1811930
  ...

Phase 3/4: Pre-computing content pages...
  Generating homepage data...
  Generating methodology data...
  ...

Phase 4/4: Building FAISS index...
  Loading embeddings...
  Building FAISS index...
  Index saved: /home/akbar/meritgiving/precompute_output/faiss_index.bin

Packaging files for upload...
Archive created: /home/akbar/meritgiving/precompute_archive/precompute_20260605_143000.tar.gz (1.0GB)
Checksum: abc123def456...

========== PRE-COMPUTE COMPLETE ==========
Completed at: 2026-06-05 15:15:00

Output:
1.1G /home/akbar/meritgiving/precompute_output/browse/
3.2G /home/akbar/meritgiving/precompute_output/orgs/
50M /home/akbar/meritgiving/precompute_output/content/
300M /home/akbar/meritgiving/precompute_output/faiss_index.bin

Ready for upload:
  Archive: /home/akbar/meritgiving/precompute_archive/precompute_20260605_143000.tar.gz
  Size: 1.0GB
  Checksum: /home/akbar/meritgiving/precompute_archive/precompute_20260605_143000.tar.gz.sha256

Next step: Upload to droplet with:
  scp /home/akbar/meritgiving/precompute_archive/precompute_20260605_143000.tar.gz root@162.243.97.179:/opt/daanaa/staging/
  scp /home/akbar/meritgiving/precompute_archive/precompute_20260605_143000.tar.gz.sha256 root@162.243.97.179:/opt/daanaa/staging/
```

### Verify Output

- [ ] Archive created in `~/meritgiving/precompute_archive/`
- [ ] Archive size is ~1GB (not 100MB, not 10GB)
- [ ] Checksum file exists
- [ ] Contents verified:
  ```bash
  tar -tzf ~/meritgiving/precompute_archive/precompute_*.tar.gz | head -20
  # Should show: browse/A/CA_1.json.gz, orgs/000/..., content/...
  ```

---

## Phase 2: Droplet Deployment

**Time estimate:** ~30 minutes total (upload 10m, deploy script 5m, verification 10m)

### Droplet Pre-Setup (One-time)

On droplet (IP: 162.243.97.179):

```bash
ssh root@162.243.97.179

# Create directories
mkdir -p /opt/daanaa/staging /data/precompute /data/claims

# Copy deployment script
scp ~/meritgiving/scripts/deploy_droplet.sh root@162.243.97.179:/opt/daanaa/scripts/
chmod +x /opt/daanaa/scripts/deploy_droplet.sh

# Copy droplet API script (after testing)
scp ~/meritgiving/scripts/droplet_api.py root@162.243.97.179:/opt/daanaa/app/
```

### Upload Archive to Droplet

From home server:

```bash
# Set variables
ARCHIVE_DIR="$HOME/meritgiving/precompute_archive"
ARCHIVE=$(ls -t "$ARCHIVE_DIR"/precompute_*.tar.gz | head -1)
CHECKSUM="${ARCHIVE}.sha256"

# Upload (will take ~10 minutes for 1GB)
scp "$ARCHIVE" root@162.243.97.179:/opt/daanaa/staging/
scp "$CHECKSUM" root@162.243.97.179:/opt/daanaa/staging/

# Verify upload
ssh root@162.243.97.179 "ls -lh /opt/daanaa/staging/ | tail -5"
```

### Run Deployment Script

On droplet:

```bash
# SSH to droplet
ssh root@162.243.97.179

# Find the archive
ARCHIVE=$(ls /opt/daanaa/staging/precompute_*.tar.gz | head -1)

# Run deployment
bash /opt/daanaa/scripts/deploy_droplet.sh "$ARCHIVE"
```

Expected output:
```
========== DROPLET DEPLOYMENT START ==========
Started at: 2026-06-05 15:30:00

Step 1/5: Verifying checksum...
✓ Checksum verified

Step 2/5: Extracting archive...
✓ Extracted to /tmp/tmp.abc123/

Step 3/5: Running health checks...
✓ A/CA_1.json.gz: 25 orgs
✓ B/NY_2.json.gz: 20 orgs
✓ FAISS index loaded: 1800000 vectors

Step 4/5: Performing atomic swap...
  Stopping API service...
  Backing up v1 → v0...
  Promoting v2 (staging) → v1 (live)...
✓ Atomic swap complete

Step 5/5: Restarting API...
✓ API restarted successfully

========== DEPLOYMENT COMPLETE ==========
Completed at: 2026-06-05 15:35:00

Status:
  Live data: /data/precompute/v1
  Backup: /data/precompute/v0 (7 days old)
  Archive: /opt/daanaa/staging/precompute_20260605_143000.tar.gz

Rollback command (if needed):
  systemctl stop daanaa && rm -rf /data/precompute/v1 && mv /data/precompute/v0 /data/precompute/v1 && systemctl start daanaa
```

### Verify Deployment

From home server:

```bash
# Health check
curl -s http://162.243.97.179:5000/health | jq .

# Expected: {"status":"ok","version":"droplet-v1"}

# Stats check
curl -s http://162.243.97.179:5000/api/stats | jq '.total_organizations'

# Expected: 1811930

# Browse check (should be <200ms)
time curl -s 'http://162.243.97.179:5000/api/organizations?ntee=A&state=CA&page=1' | jq '.organizations | length'

# Expected: 25 orgs, <200ms

# Org detail check (should be <200ms)
time curl -s 'http://162.243.97.179:5000/api/organizations/942930591' | jq '.similar_organizations | length'

# Expected: 12 similar orgs, <200ms
```

### Troubleshooting Deployment

If deployment fails:

```bash
# Check deployment logs
journalctl -u daanaa -n 100

# Check API error
curl -v http://localhost:5000/health

# Manual rollback
systemctl stop daanaa
rm -rf /data/precompute/v1
mv /data/precompute/v0 /data/precompute/v1
systemctl start daanaa
systemctl status daanaa
```

---

## Phase 3: Testing & Verification

**Time estimate:** ~15 minutes

### Quick Tests

```bash
# 1. Health
curl -s http://162.243.97.179:5000/health | jq .

# 2. Stats
curl -s http://162.243.97.179:5000/api/stats | jq '{total_organizations, with_revenue, avg_revenue}'

# 3. Browse (5 pages)
for page in 1 2 3 4 5; do
  curl -s "http://162.243.97.179:5000/api/organizations?ntee=O&state=CA&page=$page" | jq '.page, .organizations[0].organization_name'
done

# 4. Org detail (pick a random EIN)
curl -s 'http://162.243.97.179:5000/api/organizations/942930591' | jq '{EIN, organization_name, similar_organizations: (.similar_organizations | length)}'

# 5. Content pages
curl -s http://162.243.97.179:5000/api/methodology | jq '.version'
curl -s http://162.243.97.179:5000/api/sector-health | jq '.sectors | length'

# 6. Load test (50 concurrent requests)
ab -c 50 -n 500 'http://162.243.97.179:5000/api/organizations?ntee=A&state=CA&page=1'
# Expected: <200ms mean, <500ms p95
```

### Frontend Testing

1. Open http://162.243.97.179 (or daanaa.org if DNS updated)
2. Test directory filters
   - Category: Works? <200ms?
   - State: Works? <200ms?
   - Sort by revenue: Works?
3. Test org detail page
   - Click on an org
   - See similar orgs? <200ms?
   - Click on similar org
4. Test search
   - Search for "food bank"
   - Results appear? <300ms?
   - Click on result
5. Test methodology page
   - Loads? <100ms?
   - Shows 8 operating models?

---

## Checklist Summary

### Home Server (Phase 1)
- [ ] Run `bash scripts/run_precompute.sh`
- [ ] Archive created (~1GB)
- [ ] Contents verified

### Droplet (Phase 2)
- [ ] Directories created
- [ ] Archive uploaded (~10 min)
- [ ] Deployment script ran successfully
- [ ] Health check passes
- [ ] Stats endpoint returns 1.8M orgs
- [ ] Browse endpoints <200ms
- [ ] Org detail endpoints <200ms

### Frontend (Phase 3)
- [ ] Directory works
- [ ] Org detail works
- [ ] Search works
- [ ] Content pages load
- [ ] All endpoints <300ms

---

## Rollback Procedure

If anything goes wrong after deployment:

```bash
# SSH to droplet
ssh root@162.243.97.179

# Stop API
sudo systemctl stop daanaa

# Restore v0 (7-day-old version)
rm -rf /data/precompute/v1
mv /data/precompute/v0 /data/precompute/v1

# Start API
sudo systemctl start daanaa

# Verify
curl -s http://localhost:5000/health
```

This takes <30 seconds and restores the previous week's pre-computed results.

---

## Contact

If issues occur, check:
1. Disk space: `df -h /data`
2. API logs: `journalctl -u daanaa -n 100`
3. Pre-compute data: `ls -la /data/precompute/v1 | head`
4. Archive upload: `sha256sum -c /opt/daanaa/staging/precompute_*.tar.gz.sha256`
