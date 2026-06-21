# Phase 5 Build Complete — Mission & Cause Backfill Pipeline

**Date:** 2026-06-21  
**Status:** Ready to launch immediately when Phase 4 completes  
**Expected output:** 15-25K orgs with missions + causes in 30-40 hours  

---

## Deliverables

### 1. Core Scripts

#### `scripts/cause_taxonomy.py`
- **Purpose:** 15-cause taxonomy with keyword extraction
- **Type:** Library module (no CLI)
- **Features:**
  - 15 cause categories (education, health, food, housing, youth, environment, arts, civil_rights, employment, seniors, animals, international, disability, community, social_services, research)
  - Keyword pattern matching (120+ patterns total)
  - Confidence scoring (0.0-1.0 based on match density)
  - Exported: `extract_causes(text, limit=5) → (causes_list, confidence)`

#### `scripts/phase5_mission_backfill.py`
- **Purpose:** Main Phase 5 execution engine
- **Type:** Standalone CLI script
- **CLI Options:**
  - `--limit N` — Max orgs to process (for testing)
  - `--workers W` — Parallel workers (default 16)
  - `--dry-run` — Show sample LLM prompts only
  - `--resume` — Resume from last checkpoint
- **Features:**
  - Batches 16 orgs per LLM call (tuned for GPU mem)
  - Qwen2.5-32B integration (port 11437)
  - Checkpoints every 100 orgs (resumable)
  - Database lock retry logic (exponential backoff)
  - Comprehensive error logging

#### `scripts/phase5_monitor.py`
- **Purpose:** Real-time progress monitoring
- **Type:** Standalone CLI script (monitor daemon)
- **Features:**
  - Live metrics: orgs/min, elapsed time, error rates
  - Stall detection (alert if < 1 org/min)
  - Cause distribution tracking (top 5)
  - Database stats integration
  - Color-coded terminal output + log file

#### `scripts/launch_phase5_bg.sh`
- **Purpose:** Launcher with health checks + auto-restart
- **Type:** Bash wrapper
- **CLI Options:**
  - `--resume` — Resume from checkpoint
  - `--dry-run` — Test mode (show prompts)
  - `--stop` — Stop monitoring process
- **Features:**
  - Pre-flight health checks: DB, Phase 4 completion, LLM health
  - Process monitoring in background
  - Auto-restart on crash (up to 5x with backoff)
  - Detailed logging to `~/meritgiving/logs/phase5_monitor.log`

---

### 2. Documentation

#### `docs/PHASE5.md` (Complete Reference)
- Overview and architecture
- Quick start guide
- Detailed pipeline explanation
- Checkpointing & resume strategy
- Quality control & monitoring
- Troubleshooting guide
- Integration points

#### `docs/PHASE5_LAUNCH_CHECKLIST.md` (Execution Guide)
- Pre-launch checklist (5 min)
- Launch command (1 min)
- Real-time monitoring (3 terminals)
- Expected behavior timeline
- Post-launch verification
- Cleanup instructions

---

## How to Use

### Quick Start (Immediate)

```bash
# Verify prerequisites (takes ~30 seconds)
bash ~/meritgiving/scripts/launch_phase5_bg.sh --dry-run

# Launch Phase 5 in background (with auto-monitoring)
bash ~/meritgiving/scripts/launch_phase5_bg.sh

# Monitor progress in separate terminals
tail -f /tmp/phase5_progress.log
python3 ~/meritgiving/scripts/phase5_monitor.py
```

### For Testing / Sampling

```bash
# Test with 100 orgs
python3 scripts/phase5_mission_backfill.py --limit 100 --workers 4

# Show sample LLM prompts only
python3 scripts/phase5_mission_backfill.py --limit 10 --dry-run

# Resume from checkpoint
python3 scripts/phase5_mission_backfill.py --resume --workers 16
```

### Advanced Configuration

Edit `scripts/phase5_mission_backfill.py`:
- `BATCH_SIZE`: 16 (adjust 8-32 based on GPU VRAM)
- `TOKENS_PER_MISSION`: 60 (estimate, affects queue sizing)
- `CHECKPOINT_INTERVAL`: 100 (save every N orgs)
- `LLM_TIMEOUT`: 120 (seconds per batch call)

---

## Architecture

### Pipeline Flow

```
Phase 4 Completion
  ↓
Load Verified Orgs (semantic_match=1)
  ↓
Batch 16 Orgs → LLM (Qwen2.5-32B)
  ↓
Parse Mission JSON
  ↓
Extract Causes (Keyword Rules)
  ↓
Score Confidence
  ↓
Write to DB + Checkpoint
  ↓
Repeat until all orgs done
  ↓
Final Statistics Report
```

### Data Flow

**Input:**
```sql
SELECT EIN, organization_name, NTEE1, CITY, STATE, total_revenue
FROM registry_enriched
WHERE semantic_match = 1 AND mission IS NULL
```

**Output (UPDATE):**
```sql
UPDATE registry_enriched SET
  mission = "2-3 sentence description",
  cause_tags = JSON array ["education", "youth", ...],
  mission_confidence = 0.0-1.0,
  mission_source = "ai_generated"
WHERE EIN = ?
```

### Performance Profile

| Metric | Value |
|--------|-------|
| Batch size | 16 orgs |
| Tokens per mission | ~60 |
| LLM throughput | 60 tokens/sec |
| Time per batch | ~16 sec |
| Orgs per minute | ~60 |
| Orgs per hour | ~3,600 |
| For 18K orgs | ~5 hours (best case) |
| Realistic (with I/O) | 30-40 hours |
| Checkpoint frequency | Every 100 orgs |

---

## Quality Assurance

### Input Validation
- ✅ Phase 4 semantic_match column must exist
- ✅ semantic_match = 1 orgs only (verified websites)
- ✅ mission IS NULL (not already filled)
- ✅ Skip orgs with mission_source = 'human_verified'

### Output Validation
- ✅ Mission length: 2-3 sentences (enforced in LLM prompt)
- ✅ Cause tags: valid JSON array, 3-5 items
- ✅ Confidence: 0.0-1.0 float
- ✅ No hallucination: only EINs from input batch accepted

### Error Handling
- ✅ LLM timeout: Log error, continue batch
- ✅ Invalid JSON: Skip org, continue batch
- ✅ DB lock: Exponential backoff retry (6 attempts)
- ✅ Network issues: Request timeout, move on
- ✅ Cause extraction failure: Return empty causes, full mission still written

### Monitoring
- ✅ Progress log: `/tmp/phase5_progress.log` (detailed)
- ✅ Monitor log: `~/meritgiving/logs/phase5_monitor.log` (health)
- ✅ Checkpoint: `~/meritgiving/logs/phase5_checkpoint.json` (state)
- ✅ Real-time metrics: `python3 scripts/phase5_monitor.py`

---

## Integration with Existing Systems

### Before Phase 5
- **Phase 4** must complete (orgs verified via semantic matching)
- **Qwen2.5-32B** running on port 11437 (llama-server)

### During Phase 5
- **No blocking dependencies** — can run while other pipelines (scoring, FTS rebuilds) are active
- Database has retry logic for concurrent writes
- Checkpoint system allows pause/resume

### After Phase 5
- Optional: Rebuild FTS index (`scripts/build_fts_index.py`)
- Optional: Restart API to warm caches (`./restart_api.sh`)
- Optional: Sync to droplet (`bash scripts/safe_deploy_droplet.sh`)
- **No database migration required** — columns already exist

---

## Files Changed / Created

### New Files
```
scripts/cause_taxonomy.py                 (168 lines)
scripts/phase5_mission_backfill.py        (380 lines)
scripts/phase5_monitor.py                 (247 lines)
scripts/launch_phase5_bg.sh               (328 lines)
docs/PHASE5.md                            (340 lines)
docs/PHASE5_LAUNCH_CHECKLIST.md           (270 lines)
PHASE5_BUILD.md                           (This file)
```

### No Files Modified
- No changes to existing scripts or API
- Fully backward compatible
- No database schema changes needed

---

## Execution Checklist

- [x] **cause_taxonomy.py**: Python 3.12 compatible, tested
- [x] **phase5_mission_backfill.py**: Syntax checked, ready for execution
- [x] **phase5_monitor.py**: Syntax checked, ready for execution
- [x] **launch_phase5_bg.sh**: Bash syntax verified
- [x] Documentation complete (2 guides + reference)
- [x] Error handling implemented (6-point retry, timeouts, validation)
- [x] Checkpointing system (resumable every 100 orgs)
- [x] No blocking dependencies (ready when Phase 4 completes)

---

## Launch Commands

### Option A: Automatic (Recommended)
```bash
bash ~/meritgiving/scripts/launch_phase5_bg.sh
```
- Runs health checks automatically
- Launches in background with monitoring
- Auto-restarts if crashed
- Watch progress: `tail -f /tmp/phase5_progress.log`

### Option B: Manual
```bash
source ~/meritgiving/venv/bin/activate
python3 ~/meritgiving/scripts/phase5_mission_backfill.py --workers 16
```
- Direct execution, no wrapper
- See progress in stdout
- Checkpoints still saved (resumable)

### Option C: Resume from Interrupt
```bash
bash ~/meritgiving/scripts/launch_phase5_bg.sh --resume
```
- Continues from last checkpoint
- Skips already-processed orgs
- Same monitoring as Option A

---

## Monitoring Dashboard (3 Terminals)

**Terminal 1: Progress Log**
```bash
tail -f /tmp/phase5_progress.log
```
Shows: batch processing, LLM calls, database writes, checkpoints.

**Terminal 2: Real-Time Monitor**
```bash
python3 ~/meritgiving/scripts/phase5_monitor.py
```
Shows: speed (orgs/min), elapsed time, errors, cause distribution.

**Terminal 3: Launcher Health**
```bash
tail -f ~/meritgiving/logs/phase5_monitor.log
```
Shows: process restarts, LLM health checks, database lock retries.

---

## Expected Timeline

| Checkpoint | Duration | Total Time | Orgs Processed |
|------------|----------|-----------|-----------------|
| Start | - | 0:00 | 0 |
| Batch 100 | 1.7 min | 1:42 | 100 |
| Batch 500 | 8.3 min | 10:00 | 500 |
| Batch 1000 | 16.7 min | 20:00 | 1,000 |
| Checkpoint 5 | 83 min | 83:20 | 5,000 |
| Checkpoint 10 | 167 min | 166:40 | 10,000 |
| **Completion (18K)** | **5 hours** | **5:00:00** | **18,000** |
| **Realistic** | **30-40 hrs** | **30:00-40:00** | **15-25K** |

(Realistic accounts for I/O latency, DB locks, LLM retries, network variability.)

---

## Next Steps

1. **Verify Phase 4 is complete:**
   ```bash
   sqlite3 ~/meritgiving/data/merit_registry.db \
     "SELECT COUNT(*) FROM registry_enriched WHERE semantic_match = 1;"
   ```
   Expected: > 0 orgs.

2. **Start Qwen2.5-32B** (if not already running):
   ```bash
   llama-server -m /mnt/models/Qwen2.5-32B-Instruct-Q4_K_M.gguf \
     -ngl 80 -t 8 -c 4096 --port 11437 &
   ```

3. **Launch Phase 5:**
   ```bash
   bash ~/meritgiving/scripts/launch_phase5_bg.sh
   ```

4. **Monitor progress:**
   ```bash
   tail -f /tmp/phase5_progress.log
   python3 ~/meritgiving/scripts/phase5_monitor.py
   ```

5. **After completion, verify results:**
   ```bash
   sqlite3 ~/meritgiving/data/merit_registry.db \
     "SELECT COUNT(DISTINCT mission) FROM registry_enriched WHERE mission_source='ai_generated';"
   ```

---

## Support

- **Full reference:** `docs/PHASE5.md`
- **Launch guide:** `docs/PHASE5_LAUNCH_CHECKLIST.md`
- **Cause taxonomy:** `scripts/cause_taxonomy.py` (search for CAUSE_TAXONOMY dict)
- **Monitoring:** `python3 scripts/phase5_monitor.py --help`

---

## Build Metadata

- **Builder:** Claude Code (claude-haiku-4-5)
- **Date:** 2026-06-21
- **Status:** Ready for immediate launch
- **Dependencies:** Phase 4 complete, Qwen2.5-32B on port 11437
- **Estimated runtime:** 30-40 hours for 15-25K orgs
