# Phase 5: Mission & Cause Backfill

**Status:** Ready to launch immediately when Phase 4 completes.

**Expected output:** 15-25K orgs with missions + causes (30-40 hours on GPU).

---

## Overview

Phase 5 generates mission statements and extracts cause tags for organizations verified by Phase 4 (semantic_match=1).

### Input
- Orgs WHERE semantic_match=1 (Phase 4 verified, have valid websites)
- mission IS NULL (not yet backfilled)

### Output
- **mission**: 2-3 sentence description of what the org does
- **cause_tags**: JSON array of 3-5 cause categories (e.g., ["education", "youth"])
- **mission_confidence**: 0.0-1.0 confidence score for the cause extraction

### Infrastructure
- **LLM**: Qwen2.5-32B-Instruct on port 11437 (GPU, llama-server)
- **Speed**: ~60 tokens/sec → 15-25K orgs in 30-40 hours
- **Batch size**: 16 orgs per LLM call (tuned for GPU mem)
- **Checkpoints**: Every 100 orgs (resumable on crash)

---

## Quick Start

### Prerequisites

1. **Phase 4 must be complete** (semantic_match column exists, orgs verified)
2. **Qwen2.5-32B running** on port 11437:
   ```bash
   llama-server -m /mnt/models/Qwen2.5-32B-Instruct-Q4_K_M.gguf \
     -ngl 80 -t 8 -c 4096 --port 11437
   ```
3. **Python venv activated**:
   ```bash
   source ~/meritgiving/venv/bin/activate
   ```

### Launch Phase 5

```bash
# Fresh start
bash scripts/launch_phase5_bg.sh

# With --resume flag (if interrupted)
bash scripts/launch_phase5_bg.sh --resume

# Dry run (show sample prompts)
bash scripts/launch_phase5_bg.sh --dry-run

# Direct launch (no monitoring)
python3 scripts/phase5_mission_backfill.py --workers 16
```

### Monitor Progress

In a separate terminal:
```bash
# Real-time monitor
python3 scripts/phase5_monitor.py

# Watch progress log
tail -f /tmp/phase5_progress.log

# Watch launcher log
tail -f ~/meritgiving/logs/phase5_monitor.log
```

### Stop Phase 5

```bash
bash scripts/launch_phase5_bg.sh --stop
```

---

## How It Works

### 1. Fetch Verified Orgs (Phase 4 Output)

```sql
SELECT EIN, organization_name, NTEE1, CITY, STATE, total_revenue
FROM registry_enriched
WHERE semantic_match = 1
  AND (mission IS NULL OR mission = '')
  AND mission_source IS NULL
```

Expected: 15-25K orgs (depends on Phase 4 verification rate).

### 2. Generate Missions (LLM)

For each batch of 16 orgs:
- Build prompt with org name, sector (NTEE1), location, revenue size
- Call Qwen2.5-32B: `POST http://127.0.0.1:11437/v1/chat/completions`
- Extract mission from JSON response
- Validate: only accept EINs from input batch (prevent hallucinations)

**Example LLM input:**
```
Write 1-2 sentence mission descriptions. Use org NAME first, then sector and location.
...
Organizations:
  ein="12-3456789", name="Tech for All", sector="education", location="San Francisco, CA", size="$500K annual revenue"
  ein="98-7654321", name="Food Pantry Network", sector="food", location="Chicago, IL", size="community-based"
```

**LLM output:**
```json
[
  {"ein": "12-3456789", "mission": "Provides coding education and tech mentorship to underserved youth in San Francisco Bay Area."},
  {"ein": "98-7654321", "mission": "Distributes fresh food to families experiencing food insecurity across Chicago."}
]
```

### 3. Extract Causes (Keyword Rules)

For each generated mission:
- Run keyword pattern matching (15 cause categories)
- Extract top 3-5 causes with highest match count
- Score confidence: `(total_matches / text_words) * 0.5`, capped at 1.0

**Cause categories:**
- education
- health
- food
- housing
- youth
- environment
- arts
- civil_rights
- employment
- seniors
- animals
- international
- disability
- community
- social_services
- research

### 4. Write to Database

```sql
UPDATE registry_enriched
SET mission=?, cause_tags=?, mission_confidence=?, mission_source='ai_generated'
WHERE EIN=?
```

Retry loop handles database locks (common with concurrent pipelines).

---

## Checkpointing & Resume

Checkpoint saved every 100 orgs:
```json
{
  "processed_eins": [list of EINs already done],
  "start_time": "2026-06-21T12:00:00Z",
  "generated_count": 1523,
  "skipped_count": 127,
  "timestamp": "2026-06-21T14:30:00Z"
}
```

**File:** `~/meritgiving/logs/phase5_checkpoint.json`

**Resume from checkpoint:**
```bash
python3 scripts/phase5_mission_backfill.py --resume
```

---

## Logging

### Progress Log
**File:** `/tmp/phase5_progress.log`

```
[2026-06-21T12:00:00Z] Phase 5 Mission & Cause Backfill starting...
[2026-06-21T12:00:01Z]   LLM: Qwen2.5-32B-Instruct-Q4_K_M on port 11437
[2026-06-21T12:00:01Z]   Workers: 16
[2026-06-21T12:00:01Z]   Batch size: 16
[2026-06-21T12:00:01Z]   Dry run: False
[2026-06-21T12:00:01Z]   Resume: False
[2026-06-21T12:00:02Z] Found 18432 orgs to backfill (semantic_match=1, mission IS NULL)
[2026-06-21T12:00:03Z] Batch 1: Processing 16 orgs...
[2026-06-21T12:00:15Z] Batch 2: Processing 16 orgs...
...
[2026-06-21T14:30:00Z] Checkpoint saved. Processed: 1600, Generated: 1523, Skipped: 77
...
```

### Monitor Log
**File:** `~/meritgiving/logs/phase5_monitor.log`

Real-time speed, health, and error tracking.

---

## Configuration

### Tuning Performance

Edit `scripts/phase5_mission_backfill.py`:

```python
BATCH_SIZE = 16              # Orgs per LLM call (8-32)
TOKENS_PER_MISSION = 60      # Est. tokens per org (50-100)
CHECKPOINT_INTERVAL = 100    # Save after N orgs
LLM_TIMEOUT = 120            # Seconds per LLM call (60-300)
```

### Expected Speed

- **Speed**: ~60 tokens/sec (Qwen2.5-32B on GPU)
- **Tokens per org**: ~60
- **Time per batch (16 orgs)**: ~16 seconds
- **Throughput**: ~60 orgs/min = 3,600/hr
- **Time for 18K orgs**: ~5 hours (best case)
- **Realistic (with I/O + retries)**: 30-40 hours

### Hardware Requirements

- **GPU**: NVIDIA A100 / RTX 4090 / AMD R9 7900 XTX (24GB+ VRAM)
- **CPU**: 8+ cores for I/O and embeddings
- **Disk**: 500GB+ for database + logs
- **RAM**: 32GB+ (Qwen2.5-32B needs ~30GB quantized)

---

## Quality Control

### Skipped Orgs

Orgs are skipped if:
- mission IS NOT NULL (already has a mission)
- mission_source = 'human_verified' (hand-curated)
- semantic_match ≠ 1 (Phase 4 didn't verify)

### Error Handling

1. **LLM timeout**: Org logged as error, batch continues
2. **Invalid JSON**: Org skipped, batch continues
3. **Database lock**: Retry with exponential backoff (up to 6x)
4. **Invalid cause_tags JSON**: Batch rolled back, re-queued

### Monitoring for Quality

```bash
# Check generated missions
sqlite3 ~/meritgiving/data/merit_registry.db \
  "SELECT EIN, organization_name, mission, mission_confidence FROM registry_enriched \
   WHERE mission_source='ai_generated' LIMIT 10;"

# Check cause distribution
sqlite3 ~/meritgiving/data/merit_registry.db \
  "SELECT cause_tags, COUNT(*) FROM registry_enriched \
   WHERE cause_tags IS NOT NULL GROUP BY cause_tags LIMIT 5;"

# Check confidence distribution
sqlite3 ~/meritgiving/data/merit_registry.db \
  "SELECT ROUND(mission_confidence, 1), COUNT(*) FROM registry_enriched \
   WHERE mission_confidence IS NOT NULL GROUP BY 1 ORDER BY 1;"
```

---

## Integration with Other Phases

### After Phase 5 Completes

1. **FTS Index Rebuild** (optional, if search is broken):
   ```bash
   python3 scripts/build_fts_index.py
   ```

2. **API Restart** (to cache new missions):
   ```bash
   pkill -f "gunicorn daanaa_api" || pkill -f "python3 daanaa_api"
   ~/meritgiving/restart_api.sh
   ```

3. **Droplet Sync** (if running droplet):
   ```bash
   bash scripts/safe_deploy_droplet.sh
   ```

---

## Troubleshooting

### "Phase 4 not complete" Error

The `semantic_match` column doesn't exist in the database yet.

**Solution:** Run Phase 4 first:
```bash
python3 scripts/phase4_semantic_verification.py
```

### "LLM not responding" Error

Qwen2.5-32B is not running on port 11437.

**Solution:** Start the LLM server:
```bash
# Using llama-server (recommended)
llama-server -m /mnt/models/Qwen2.5-32B-Instruct-Q4_K_M.gguf \
  -ngl 80 -t 8 -c 4096 --port 11437

# Or using Ollama
ollama run qwen2.5:32b
# Then update PHASE5 scripts to use port 11434
```

### "No verified orgs found" Error

Phase 4 ran but didn't verify any orgs.

**Solution:** Check Phase 4 progress:
```bash
tail -f ~/meritgiving/logs/phase4_progress.log
python3 scripts/phase4_monitor.py
```

### Process Keeps Restarting

LLM is crashing or timing out frequently.

**Solution:**
1. Check LLM logs: `journalctl -u llama-server` or check console
2. Reduce batch size: `BATCH_SIZE = 8` in phase5_mission_backfill.py
3. Increase LLM timeout: `LLM_TIMEOUT = 180`

### Database Locked

Other scripts are writing to the database.

**Solution:**
- Check for concurrent jobs: `pgrep -f "python3 scripts" | wc -l`
- Increase retry backoff: Edit `write_batch()` function
- Wait for other jobs to finish before starting Phase 5

---

## API Response Changes

After Phase 5, all org detail responses will include:

```json
{
  "EIN": "12-3456789",
  "organization_name": "Tech for All",
  "mission": "Provides coding education and tech mentorship to underserved youth.",
  "cause_tags": ["education", "youth", "stem"],
  "mission_confidence": 0.82,
  "mission_source": "ai_generated",
  ...
}
```

Frontend can use `mission_confidence` to show uncertainty indicators if needed.

---

## Next Steps (Future Phases)

- **Phase 6**: Re-embedding with updated missions (org_embeddings refresh)
- **Phase 7**: Cause-based filtering + search ranking
- **Phase 8**: Hidden gems mechanic re-tuning (factor in cause visibility)

---

## References

- Cause taxonomy: `scripts/cause_taxonomy.py`
- Main script: `scripts/phase5_mission_backfill.py`
- Monitor: `scripts/phase5_monitor.py`
- Launcher: `scripts/launch_phase5_bg.sh`
- Phase 4: `docs/PHASE4.md`
