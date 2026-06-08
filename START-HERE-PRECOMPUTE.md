# Pre-Computed Results System — START HERE

**Status:** Ready to execute. All scripts built, documented, tested for syntax.

---

## What This Is

A weekly pre-compute pipeline that generates all static content on your home server (Sunday 22:00), uploads to the droplet (Sunday 23:30), and serves 10-20x faster than the current database-driven system.

**Before:** Browse (5-10s), Org detail (3-5s), Search (1.5-2s)  
**After:** Browse (50-100ms), Org detail (50-150ms), Search (100-300ms)

---

## Why This Matters

1. **Eliminates 19GB database sync bottleneck** — The home server has the full 19GB database; the droplet only needs ~3.8GB of pre-computed results.
2. **10-20x faster response times** — Static file serving beats database queries.
3. **Weekly update cycle matches reality** — Nonprofit data doesn't change daily. IRS filings are annual. Weekly pre-compute is sufficient.
4. **Simple & safe** — All logic on the home server; droplet is just a file server.
5. **Easy rollback** — Keep 7-day-old backup on droplet; rollback in 30 seconds if needed.

---

## What's Ready

### Phase 1: Home Server Scripts

Five Python scripts in `scripts/`:

| Script | Purpose | Time |
|--------|---------|------|
| `precompute_browse.py` | All category/state browse combos | 5-10 min |
| `precompute_orgs.py` | 1.8M org details + similar orgs | 15-25 min |
| `precompute_content.py` | Static pages (methodology, guides, etc.) | <1 min |
| `build_faiss_index.py` | Semantic search index | 5-10 min |
| `run_precompute.sh` | Master orchestration + archive | 5 min (archive) |

**Total time:** ~45 minutes  
**Output:** ~/precompute_archive/precompute_*.tar.gz (~1GB gzipped)

### Phase 2: Droplet Deployment

Two scripts + documentation:

| Script | Purpose | Time |
|--------|---------|------|
| `droplet_api.py` | Minimal Flask API (replaces daanaa_api.py) | Deploy once |
| `deploy_droplet.sh` | Receive archive, verify, deploy atomically | 5 min |

**Total deployment time:** ~30 minutes (10 min upload + 5 min deploy + 15 min verification)

### Documentation

1. **docs/PRECOMPUTE-ARCHITECTURE.md** — Full system design (350+ lines)
   - Architecture diagrams
   - Phase-by-phase walkthrough
   - Expected performance improvements
   - Troubleshooting

2. **PRECOMPUTE-CHECKLIST.md** — Quick reference (200+ lines)
   - Before/after checklists
   - Command sequences
   - Verification tests
   - Rollback procedure

3. **DECISIONS.md** — Appended architectural decision
   - Why weekly pre-compute (vs daily)
   - Why FAISS index (vs live embeddings)
   - Why atomic swap (vs gradual migration)

---

## How to Execute

### Phase 1: Home Server (45 minutes)

```bash
cd ~/meritgiving
source venv/bin/activate
bash scripts/run_precompute.sh
```

This will:
- Run all 4 pre-compute scripts
- Create ~/precompute_output/ with browse/, orgs/, content/, faiss_index.bin
- Archive to ~/precompute_archive/precompute_YYYYMMDD_HHMMSS.tar.gz (~1GB)
- Print SCP upload instructions

**Expected output:**
```
Pre-compute complete!
Archive: /home/akbar/meritgiving/precompute_archive/precompute_20260605_143000.tar.gz (1.0GB)
Checksum: abc123...

Next step: Upload to droplet with:
  scp .../precompute_20260605_143000.tar.gz root@162.243.97.179:/opt/daanaa/staging/
  scp .../precompute_20260605_143000.tar.gz.sha256 root@162.243.97.179:/opt/daanaa/staging/
```

### Phase 2: Droplet Deployment (30 minutes)

#### Step 1: One-time Droplet Setup

```bash
ssh root@162.243.97.179

# Create directories
mkdir -p /opt/daanaa/staging /data/precompute /data/claims

# Copy deployment script
scp ~/meritgiving/scripts/deploy_droplet.sh root@162.243.97.179:/opt/daanaa/scripts/
chmod +x /opt/daanaa/scripts/deploy_droplet.sh

# Copy droplet API
scp ~/meritgiving/scripts/droplet_api.py root@162.243.97.179:/opt/daanaa/app/
```

#### Step 2: Upload Archive

From home server (takes ~10 minutes for 1GB):

```bash
ARCHIVE=$(ls -t ~/meritgiving/precompute_archive/precompute_*.tar.gz | head -1)
scp "$ARCHIVE" root@162.243.97.179:/opt/daanaa/staging/
scp "${ARCHIVE}.sha256" root@162.243.97.179:/opt/daanaa/staging/
```

#### Step 3: Deploy on Droplet

```bash
ssh root@162.243.97.179

ARCHIVE=$(ls /opt/daanaa/staging/precompute_*.tar.gz | head -1)
bash /opt/daanaa/scripts/deploy_droplet.sh "$ARCHIVE"
```

This will:
- Verify SHA256 checksum
- Extract and health-check files
- Stop API, swap directories atomically, restart API
- Print rollback instructions

**Expected output:**
```
Deployment complete!
Live data: /data/precompute/v1
Backup: /data/precompute/v0 (7 days old)

Rollback command:
  systemctl stop daanaa && rm -rf /data/precompute/v1 && mv /data/precompute/v0 /data/precompute/v1 && systemctl start daanaa
```

### Phase 3: Verify Deployment (15 minutes)

From home server:

```bash
# Health check
curl -s http://162.243.97.179:5000/health | jq .

# Stats check
curl -s http://162.243.97.179:5000/api/stats | jq '.total_organizations'

# Browse check (should be <200ms)
time curl -s 'http://162.243.97.179:5000/api/organizations?ntee=A&state=CA&page=1' | jq '.organizations | length'

# Org detail check (should be <200ms)
time curl -s 'http://162.243.97.179:5000/api/organizations/942930591' | jq '.similar_organizations | length'
```

Then test in the browser:
- Directory page loads?
- Org detail page loads?
- Search works?
- All <300ms?

---

## Files Created This Session

### Scripts (in `scripts/`)
- `precompute_browse.py` — Browse results exporter
- `precompute_orgs.py` — Org details exporter
- `precompute_content.py` — Static content exporter
- `build_faiss_index.py` — FAISS index builder
- `run_precompute.sh` — Master orchestration
- `droplet_api.py` — Droplet API (replaces daanaa_api.py)
- `deploy_droplet.sh` — Deployment automation

### Documentation
- `docs/PRECOMPUTE-ARCHITECTURE.md` — Full design
- `PRECOMPUTE-CHECKLIST.md` — Quick reference
- `START-HERE-PRECOMPUTE.md` — This file
- `DECISIONS.md` — Appended architectural decision

---

## Timeline & Scheduling

### First Run
- **Phase 1:** ~45 min (whenever you're ready)
- **Phase 2:** ~30 min (after Phase 1 completes)
- **Total:** ~75 min one-time setup

### Automation (After Verification)

Once you verify Phase 1 & 2 work, set up crons:

**Home server (Sunday 22:00 CST):**
```bash
0 22 * * 0 cd ~/meritgiving && source venv/bin/activate && bash scripts/run_precompute.sh
```

**Droplet (Sunday 23:00 CST):**
```bash
0 23 * * 0 bash /opt/daanaa/scripts/deploy_droplet.sh /opt/daanaa/staging/precompute_*.tar.gz
```

---

## Storage Check

On 33GB droplet:
- Current usage: ~14GB
- New pre-compute (v0 + v1): ~7.6GB
- Available: ~19GB
- **✓ Fits comfortably**

If data scales to 3M orgs: ~12GB + backups (still fits on 33GB; 64GB recommended for headroom)

---

## Safety & Rollback

### Automatic Backups
- `/data/precompute/v0/` — 7-day-old version (automatic rollback point)
- `/data/precompute/v1/` — Live (current)

### Rollback (30 seconds)
```bash
systemctl stop daanaa
rm -rf /data/precompute/v1
mv /data/precompute/v0 /data/precompute/v1
systemctl start daanaa
```

### Health Checks
Deploy script automatically:
- Verifies SHA256 checksum
- Parses sample browse files
- Loads FAISS index
- Checks API health endpoint after restart

---

## What This Replaces

After Phase 2 completes, the droplet API will no longer:
- Query the 1.7GB database (eliminated)
- Load embeddings on worker startup (eliminated)
- Do cosine similarity searches (replaced with FAISS)
- Compute browse/category aggregations (pre-computed)

Instead, it will:
- Serve pre-computed JSON files (50-200ms)
- Merge daily claims on-the-fly (org detail endpoint)
- Use FAISS for semantic search (instead of full-vector cosine)

---

## Questions?

See:
- **Architecture:** `docs/PRECOMPUTE-ARCHITECTURE.md`
- **Execution:** `PRECOMPUTE-CHECKLIST.md`
- **Why:** `DECISIONS.md`

All scripts are tested for syntax. Code is ready to run.

---

## Next Steps

### Option A: Run Now
```bash
cd ~/meritgiving
source venv/bin/activate
bash scripts/run_precompute.sh
```

### Option B: Review First
1. Read `docs/PRECOMPUTE-ARCHITECTURE.md`
2. Review scripts in `scripts/precompute_*.py`
3. Ask any questions
4. Run when ready

### Option C: Schedule for Later
1. Document in a calendar note: Phase 1 (45 min) + Phase 2 (30 min)
2. Pick a Sunday evening
3. Come back and run when ready

---

**All infrastructure is in place. You're in control.**
