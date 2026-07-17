# Skill: Pre-Compute Pipeline

**Mission:** Make the invisible visible — ensure all 1.6M tax-deductible 501(c)(3) nonprofits are discoverable.

## When to invoke

Use `/precompute` when you need to:
- Generate weekly pre-computed results for the droplet (browse, orgs, content, FAISS semantic search index)
- Update the live site with fresh nonprofit data
- Regenerate search index after database changes
- Ensure all 1.6M tax-deductible nonprofits remain discoverable and searchable

Typically invoked weekly (Sunday 22:00 CST) via cron, or manually when needed.

## Prerequisites

- Home server with access to `~/meritgiving/`
- 32GB+ RAM (Phase 2 uses ~20GB for 1.8M embeddings)
- GPU with ROCm support (optional, but recommended for speed)
- CuPy installed (`pip install cupy-cuda12x` or `pip install cupy-rocm`)
- FAISS-GPU installed (`pip install faiss-gpu` or `pip install faiss`)

## How it works

**Five-phase pipeline** that runs weekly:

1. **Phase 1 (Browse)** — Exports all 26 NTEE × 50 states category/state combinations, paginated (25 items/page). Output: ~100MB, 41K files. Time: <1 min.

2. **Phase 2 (Org Details)** — Exports all 1.8M org detail pages with 12 similar organizations pre-computed via GPU-accelerated embedding similarity. Output: ~3.2GB, 1.8M files. Time: 10-20 min (GPU-optimized).

3. **Phase 3 (Content)** — Exports static pages: homepage (with stats), methodology (v4.0), sector-health, how-it-works, guides, FAQs, about, legal. Output: ~50MB. Time: <1 min.

4. **Phase 4 (FAISS Index)** — Builds approximate nearest neighbor index from 1.8M embeddings using GPU-FAISS. Output: ~300MB index + 50MB EIN map. Time: 5-10 min (GPU-accelerated).

5. **Archive & Checksum** — Packages all outputs into `.tar.gz` archive (~1GB gzipped) with SHA256 checksum for safe droplet deployment. Time: 5 min.

**Total time:** ~30-40 minutes with GPU acceleration.

## Step 0: Verify prerequisites

```bash
# Check disk space
df -h ~/meritgiving/

# Check GPU
nvidia-smi || rocm-smi

# Check Python packages
python3 -c "import cupy; import faiss; print('✓ GPU packages ready')"
```

## Step 1: Run pre-compute

```bash
cd ~/meritgiving
source venv/bin/activate
bash scripts/run_precompute.sh
```

Expected output:
```
========== PRE-COMPUTE ORCHESTRATION START ==========
Started at: 2026-06-05 22:00:00

Phase 1/4: Pre-computing browse results...
  A: AP processed
  ...
  [2026-06-05T22:01:00] Browse pre-compute complete!
  Files created: 41715
  Disk usage: 108.4 MB

Phase 2/4: Pre-computing org detail pages...
  ✓ GPU (CuPy) available for acceleration
  Loaded 1811930 embeddings
  Loaded 1811930 orgs into memory
  Using GPU for similarity computation
  
  Processed 50000/1811930
  Processed 100000/1811930
  ...
  [2026-06-05T22:25:00] Org detail pre-compute complete!
  Disk usage: 3.2 GB

Phase 3/4: Pre-computing content pages...
  [2026-06-05T22:25:30] Content pre-compute complete!
  Disk usage: 50 MB

Phase 4/4: Building FAISS index...
  ✓ GPU (FAISS-GPU) available for acceleration
  Loaded 1811930 vectors
  Vector shape: (1811930, 1024)
  Using GPU for index training and adding...
  [2026-06-05T22:35:00] FAISS index build complete!
  Disk usage: 300 MB

Packaging files for upload...
Archive created: ~/meritgiving/precompute_archive/precompute_20260605_220000.tar.gz (1.0GB)
Checksum: abc123def456...

========== PRE-COMPUTE COMPLETE ==========
Completed at: 2026-06-05 22:38:00

Ready for upload:
  Archive: ~/meritgiving/precompute_archive/precompute_20260605_220000.tar.gz
  Size: 1.0GB
  Checksum: ~/meritgiving/precompute_archive/precompute_20260605_220000.tar.gz.sha256

Next step: Upload to droplet...
```

## Step 2: Verify output

```bash
# Check archive size (should be ~1GB)
du -sh ~/meritgiving/precompute_archive/precompute_*.tar.gz

# Verify contents
tar -tzf ~/meritgiving/precompute_archive/precompute_*.tar.gz | head -20

# Should show: browse/, orgs/, content/, faiss_index.bin, ein_map.json.gz
```

## Step 3: Upload to droplet

```bash
# Set archive path
ARCHIVE=$(ls -t ~/meritgiving/precompute_archive/precompute_*.tar.gz | head -1)
CHECKSUM="${ARCHIVE}.sha256"

# Upload (takes ~10 minutes for 1GB)
scp "$ARCHIVE" root@162.243.97.179:/opt/daanaa/staging/
scp "$CHECKSUM" root@162.243.97.179:/opt/daanaa/staging/

# Verify
ssh root@162.243.97.179 "ls -lh /opt/daanaa/staging/ | tail -5"
```

## Step 4: Deploy on droplet

```bash
ssh root@162.243.97.179

# Find archive
ARCHIVE=$(ls /opt/daanaa/staging/precompute_*.tar.gz | head -1)

# Run deployment (zero-downtime atomic swap)
bash /opt/daanaa/scripts/deploy_droplet.sh "$ARCHIVE"
```

Expected output:
```
========== DROPLET DEPLOYMENT START ==========
Started at: 2026-06-05 23:30:00

Step 1/5: Verifying checksum...
✓ Checksum verified

Step 2/5: Extracting archive...
✓ Extracted to /tmp/tmp.abc123/

Step 3/5: Running health checks...
✓ A/CA_1.json.gz: 25 orgs
✓ B/NY_2.json.gz: 20 orgs
✓ FAISS index loaded: 1811930 vectors

Step 4/5: Performing atomic swap...
✓ Atomic swap complete

Step 5/5: Restarting API...
✓ API restarted successfully

========== DEPLOYMENT COMPLETE ==========
Live data: /data/precompute/v1
Backup: /data/precompute/v0 (7 days old)
```

## Step 5: Verify deployment

```bash
# Health check
curl -s http://162.243.97.179:5000/health | jq .

# Stats check
curl -s http://162.243.97.179:5000/api/stats | jq '.total_organizations'

# Browse check (<200ms)
time curl -s 'http://162.243.97.179:5000/api/organizations?ntee=A&state=CA&page=1' | jq '.organizations | length'

# Org detail check (<200ms)
time curl -s 'http://162.243.97.179:5000/api/organizations/942930591' | jq '.similar_organizations | length'
```

## Troubleshooting

### Pre-compute fails

```bash
# Check disk space
df -h ~/meritgiving/

# Check database
sqlite3 ~/meritgiving/data/merit_registry.db "PRAGMA quick_check;"

# Check embeddings
sqlite3 ~/meritgiving/data/merit_registry.db "SELECT COUNT(*) FROM org_embeddings;"

# Rerun just the failing phase
source venv/bin/activate
python3 scripts/precompute_orgs.py  # or precompute_browse.py, etc.
```

### Deployment fails

```bash
# SSH to droplet
ssh root@162.243.97.179

# Check logs
journalctl -u daanaa -n 100

# Manual rollback
systemctl stop daanaa
rm -rf /data/precompute/v1
mv /data/precompute/v0 /data/precompute/v1
systemctl start daanaa
```

### Slow performance

```bash
# Check GPU availability
python3 -c "import cupy; print('GPU available')" 2>/dev/null || echo "GPU not available"

# Check RAM usage
free -h

# Monitor during execution
watch -n 2 'du -sh precompute_output/*'
```

## Automation (Cron)

After first successful run, schedule automated weekly pre-compute:

**Home server (Sunday 22:00 CST):**
```bash
# Add to crontab
0 22 * * 0 cd ~/meritgiving && source venv/bin/activate && bash scripts/run_precompute.sh >> logs/precompute.log 2>&1
```

**Droplet (Sunday 23:00 CST):**
```bash
# Add to droplet crontab
0 23 * * 0 ARCHIVE=$(ls /opt/daanaa/staging/precompute_*.tar.gz | head -1) && bash /opt/daanaa/scripts/deploy_droplet.sh "$ARCHIVE" >> /var/log/precompute-deploy.log 2>&1
```

## Performance expectations

| Phase | Component | Time (GPU) | Output |
|-------|-----------|-----------|--------|
| 1 | Browse export | <1 min | 108 MB |
| 2 | Org details + similar | 10-20 min | 3.2 GB |
| 3 | Content pages | <1 min | 50 MB |
| 4 | FAISS index | 5-10 min | 300 MB |
| 5 | Archive + checksum | 5 min | 1 GB |
| **Total** | | **30-40 min** | **~3.8GB uncompressed** |

**Droplet deployment:** 30 minutes (10 min upload + 5 min deploy + 15 min verification)

**Total weekly cycle:** ~1 hour 10 minutes (45 min home server + 30 min droplet)

## Expected results

After deployment, your site will be:

- **10-20x faster** — All endpoints <300ms (vs 2-10s current)
- **More stable** — No database queries during request handling
- **Easier to scale** — Static files can be cached, CDN-friendly
- **Safe to update** — 7-day rollback available, zero-downtime deployment

## Questions?

See:
- `docs/PRECOMPUTE-ARCHITECTURE.md` — Full technical design
- `PRECOMPUTE-CHECKLIST.md` — Step-by-step checklist
- `DECISIONS.md` — Why this architecture (vs alternatives)

---

**Status:** Ready for weekly scheduled execution. Estimated time savings: 20-30 hours/month (from 2-3 hour manual rebuilds down to 1-hour weekly automation).
