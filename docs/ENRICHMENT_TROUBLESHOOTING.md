# Enrichment Pipeline Troubleshooting Guide

Common issues and solutions for the nonprofit enrichment pipeline.

---

## Issue 1: "Batch MISSING" from monitor_batch.py

**Symptom:**
```
=== Enrichment Batch Health (2026-07-05) ===

⚠ Batch MISSING (2026-07-05)
Quality: No recent metrics
```

**Root Causes:**

1. **Nightly cron job did not run**
   - Check cron installation: `crontab -l | grep enrich`
   - Check logs: `tail logs/enrich_batch_20260705.log`
   - Verify database is accessible: `sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM enrichment_run;"`

2. **Cron job ran but no enrichments were generated**
   - All orgs may already have cause tags and websites
   - Query the database: 
     ```sql
     SELECT COUNT(*) FROM registry_enriched 
     WHERE cause_tags IS NULL OR website IS NULL;
     ```
   - If count is 0, there's nothing to enrich

3. **Cron job ran but failed silently**
   - Check the log file for errors: `cat logs/enrich_batch_20260705.log`
   - Look for Python stack traces or connection errors
   - If log is empty, the cron job may not have been triggered

**Solution:**
```bash
# Manually run the enrichment to test
cd /home/akbar/meritgiving
bash scripts/cron_enrich_nightly.sh

# Check logs
tail -50 logs/enrich_batch_*.log

# Verify results were written
sqlite3 data/merit_registry.db \
  "SELECT COUNT(*) FROM enrichment_run WHERE run_date = DATE('now');"
```

---

## Issue 2: Mock Inference Functions (Not Real HTTP Servers)

**Context:**

The current CLI (`scripts/enrich_batch.py`) uses placeholder mock functions for Qwen inference and embeddings lookups. These are intentional for development/dry-run use.

**What's mocked:**

- `get_mock_qwen_fn()` — Returns synthetic tags and websites (deterministic based on input)
- `get_embeddings_fn()` — Returns deterministic random embeddings (seeded by input text)

**Why this matters:**

1. **Dry-runs and manual testing:** Use mocks (safe, fast, no dependencies)
2. **Test suite:** Uses real mock fixtures from `tests/fixtures.py` (not CLI mocks)
3. **Production cron jobs:** Currently use mocks; real HTTP integration to ports 11437/11436 is a pending implementation

**How to verify you're using mocks:**
```bash
grep -n "get_mock_qwen_fn\|get_embeddings_fn" scripts/enrich_batch.py
# Output: Lines 223-224 show the mocks are being used
```

**When production HTTP integration is ready:**

1. Modify `enrich_batch.py` main() to pass real inference functions (not mocks)
2. Ensure llama-server instances are running on ports 11437/11436
3. Add connection health checks to `cron_enrich_nightly.sh`
4. Document the new production setup in this runbook

**Current expected behavior with mocks:**

```bash
python3 scripts/enrich_batch.py --dry-run --max-orgs 10
```

Output: Cause tags like "Education, Community Development, Mentorship"; websites like "myorg.org" (all synthetic, not ML-generated).

---

## Issue 3: No Enrichments Written to Database

**Symptom:**
```bash
python3 scripts/enrich_batch.py --max-orgs 100
# Runs successfully but enrichment_run table remains empty or unchanged
```

**Root Causes:**

1. **Confidence threshold too high**
   - Currently, enrichments are written if they pass basic checks (not empty)
   - Confidence scores are hardcoded to 0.7
   - The `cause_tags_min_confidence` threshold (0.65) in `enrich_batch_config.json` is NOT yet used to filter writes
   - **This is expected; threshold filtering is a future enhancement**

2. **All orgs already enriched**
   ```sql
   SELECT COUNT(*) FROM registry_enriched 
   WHERE cause_tags IS NULL AND website IS NULL;
   ```
   If this returns 0, there are no unenriched orgs to process.

3. **Database connection issue**
   - Verify database is accessible: `sqlite3 data/merit_registry.db ".tables"`
   - Check for lock timeout: `sqlite3 data/merit_registry.db "PRAGMA journal_mode;"`

**Solution:**

```bash
# Check how many orgs need enrichment
cd /home/akbar/meritgiving
source venv/bin/activate
sqlite3 data/merit_registry.db \
  "SELECT COUNT(*) AS unenriched FROM registry_enriched 
   WHERE (cause_tags IS NULL OR cause_tags = '') 
      OR (website IS NULL OR website = '');"

# If count > 0, run enrichment with max-orgs smaller than result
python3 scripts/enrich_batch.py --max-orgs 100 --workers 1

# Verify writes
sqlite3 data/merit_registry.db \
  "SELECT COUNT(*) FROM enrichment_run WHERE run_date = DATE('now');"
```

**Known Limitation:**

Confidence filtering is NOT implemented in `_enrich_layer()` yet. All generated enrichments are written regardless of confidence score. This will be enhanced in a future task to respect `cause_tags_min_confidence` from the config.

---

## Issue 4: Quality Metrics Missing or All Zero

**Symptom:**
```bash
python3 scripts/monitor_batch.py
# Output: "Quality: No recent metrics"

# Or in logs, see:
# [2026-07-06] Quality measured: {}  (empty dict)
```

**Root Cause (Expected):**

Quality measurement currently uses **placeholder empty dicts** for corrections and validations:

```python
# From scripts/measure_quality_cron.py (lines 54-55)
tag_corrections = {}      # Placeholder: no real corrections wired in
website_validations = {}  # Placeholder: no real website validations wired in

metrics = measurer.measure_daily_quality(
    run_date=str(date.today()),
    tag_corrections=tag_corrections,
    website_validations=website_validations
)
```

**Why this is expected:**

- Quality measurement requires corrections from the `org_claims` table (verification pipeline)
- Website validation requires results from the `donate_url_pipeline`
- These systems are not yet integrated with enrichment quality tracking
- Until they are wired in, quality metrics will be empty

**When corrections ARE available:**

The `measure_quality_cron.py` script will automatically compute accuracy:

```python
# Future integration point
tag_corrections = {
    'org_ein_1': {'actual_tags': ['Education', 'Mentorship'], 'correct': True},
    'org_ein_2': {'actual_tags': ['Community'], 'correct': False},
    ...
}

metrics = measurer.measure_daily_quality(
    run_date='2026-07-06',
    tag_corrections=tag_corrections,
    website_validations=website_validations
)
# Result: {'cause_tag_accuracy': 0.82, 'website_validity': 0.75, ...}
```

**To unblock quality measurement:**

1. Implement a corrections fetcher that queries `org_claims` table
2. Implement a website validator that checks donation link health
3. Update `measure_quality_cron.py` to call these fetchers instead of using empty dicts
4. Re-enable prompt improvement (which depends on quality metrics)

**For now:**

Quality metrics will remain empty. This is not an error — it's expected until corrections are wired in. The enrichment pipeline will continue to run and generate cause tags/websites; they just won't be measured or improved yet.

---

## Issue 5: GPU Memory / Out of Memory Errors

**Symptom:**
```
RuntimeError: CUDA out of memory
# or
torch.cuda.OutOfMemoryError: CUDA out of memory.
```

**Root Causes:**

1. **Embedding batch size too large**
   - Each embedding is 1024 dimensions × 4 bytes (float32) = ~4 KB
   - 1000 embeddings ≈ 4 MB; 100K embeddings ≈ 400 MB
   - With model weights (~3 GB), peak memory = ~4 GB
   - If your GPU has 8 GB, you should be fine for reasonable batch sizes

2. **Qwen model too large for available VRAM**
   - Qwen2.5-32B quantized (Q4_K_M) ≈ 20 GB
   - Qwen2.5-14B quantized ≈ 10 GB
   - If available GPU memory < model size, you'll get OOM errors

3. **Multiple processes competing for GPU memory**
   - If other jobs are running (video encoding, other ML tasks), GPU may be starved

**Solution:**

```bash
# Check current GPU memory usage
nvidia-smi

# Reduce batch size (more gradual, less memory spike)
python3 scripts/enrich_batch.py --batch-size 5

# Reduce workers (fewer parallel requests)
python3 scripts/enrich_batch.py --workers 1

# Restart llama-server with explicit memory limits
# (Adjust --ctx-size and batch size)
llama-server -m model.gguf --port 11437 \
  --ctx-size 4096 \
  --ngl 40  # Layers on GPU (reduce if OOM)
```

**For long-running cron jobs:**

Add monitoring to `cron_enrich_nightly.sh` to check GPU memory before starting:

```bash
# Check if GPU has > 4 GB free
FREE_MEMORY=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)
if [ "$FREE_MEMORY" -lt 4000 ]; then
  echo "Insufficient GPU memory: ${FREE_MEMORY} MB < 4000 MB"
  exit 1
fi
```

---

## Issue 6: Cron Job Not Running (Not Installed)

**Symptom:**

Enrichment batch doesn't run at 8 PM; no logs are generated.

**Root Cause:**

Cron jobs are created but NOT automatically installed in the production crontab. Installation is a manual step.

**Verification:**

```bash
crontab -l | grep -c enrich
# Output: 0 means not installed
```

**Solution:**

Follow section 2 of the runbook to manually install cron jobs:

```bash
crontab -e
# Add the three cron job lines for enrichment (8 PM), quality (6 AM), and prompts (7 AM)
```

**Verify installation:**

```bash
crontab -l | grep enrich
# Should show 3 lines (or however many you added)
```

---

## Issue 7: Test Pollution (Temp File Conflicts)

**Symptom:**

Tests fail with errors like:
```
FileNotFoundError: [Errno 2] No such file or directory: '/root/meritgiving/...'
# or
PermissionError: [Errno 13] Permission denied: '/home/akbar/...'
```

**Root Cause (Known Issue from Task 8):**

Classes like `PromptImprovement` have default file paths pointing at `Path.home() / "meritgiving" / ...` (production locations). If tests don't override these with explicit temp paths, they may:
1. Try to write to paths they don't have permission for
2. Pollute production data with test artifacts
3. Fail in restricted environments

**Prevention:**

Always pass explicit temp paths when creating test objects:

```python
# WRONG: Uses default production path
improver = PromptImprovement(db_con=con, config=config)

# CORRECT: Uses temp path, safe to delete after
import tempfile
with tempfile.TemporaryDirectory() as tmpdir:
    improver = PromptImprovement(
        db_con=con,
        config=config,
        prompt_versions_file=str(Path(tmpdir) / "prompt_versions.json")
    )
    # Use improver; file is cleaned up after context exits
```

**Example test structure:**

```python
def test_prompt_improvement_with_temp_path(test_db_con):
    import tempfile
    from pathlib import Path
    from scripts.prompt_improvement import PromptImprovement
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = load_test_config()
        improver = PromptImprovement(
            db_con=test_db_con,
            config=config,
            prompt_versions_file=str(Path(tmpdir) / "versions.json")
        )
        
        # Test logic here
        assert improver.should_improve_prompts() in [True, False]
```

**Checking for test pollution:**

```bash
# After running tests, verify no unexpected files exist
ls -la data/enrichment/prompt_versions.json 2>&1
# Should show: No such file (unless you intentionally created it)

# If it exists, it may be a stray test artifact
# Option 1: Delete it (safe if you haven't manually run improvements)
rm data/enrichment/prompt_versions.json

# Option 2: Check its modification time to see if test created it
stat data/enrichment/prompt_versions.json
```

---

## Issue 8: Database Lock Timeout (Concurrent Access)

**Symptom:**
```
sqlite3.OperationalError: database is locked
```

**Root Cause:**

Another process has an exclusive lock on `merit_registry.db`. Common causes:
1. A previous enrichment run didn't finish cleanly
2. A long-running query (quality measurement) is blocking batch writes
3. Multiple cron jobs running in parallel

**Solution:**

```bash
# Check if the database is locked (safe read-only check)
sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM enrichment_run;"

# If that fails, check what processes are accessing it
lsof | grep merit_registry.db

# If stuck, kill the process (last resort)
pkill -f enrich_batch.py

# Verify database integrity
sqlite3 data/merit_registry.db "PRAGMA integrity_check;"
# Should output: ok
```

**Prevention:**

- Increase timeout in database connections (already set to 180s in scripts)
- Stagger cron jobs to avoid overlap:
  - 8:00 PM — Enrichment batch (runs ~5-10 min)
  - 6:00 AM — Quality measurement (runs ~1-2 min)
  - 7:00 AM — Prompt improvement (runs ~1 min)
- Monitor cron logs for hung processes

---

## Issue 9: Inference Server Not Running

**Symptom:**

```bash
python3 scripts/enrich_batch.py --max-orgs 10
# Completes successfully but generates synthetic data (not ML-inferred)
```

**Context (Expected):**

The current CLI uses mock inference functions, not real HTTP servers. If you want to test with real inference:

1. **Start llama-server instances**

   ```bash
   # Terminal 1: Qwen (port 11437)
   llama-server -m Qwen2.5-32B-Instruct-Q4_K_M.gguf \
     --port 11437 \
     --ngl 99 \
     --main-gpu 0 \
     --ctx-size 8192
   
   # Terminal 2: mxbai-embed-large (port 11436)
   llama-server -m mxbai-embed-large.Q6_K.gguf \
     --port 11436 \
     --embedding \
     --ngl 99 \
     --main-gpu 0
   ```

2. **Modify enrich_batch.py to use real servers** (future task)

   Currently, `main()` calls `get_mock_qwen_fn()` and `get_embeddings_fn()`. To use real servers:
   ```python
   # In enrich_batch.py main(), replace:
   qwen_fn = get_mock_qwen_fn()  # Mock
   embeddings_fn = get_embeddings_fn()  # Mock
   
   # With (pseudo-code for future):
   qwen_fn = make_qwen_http_client(port=11437)  # Real HTTP client
   embeddings_fn = make_embeddings_http_client(port=11436)  # Real HTTP client
   ```

3. **Verify server health**

   ```bash
   # Qwen health check
   curl http://localhost:11437/health

   # Embeddings health check
   curl -X POST http://localhost:11436/v1/embeddings \
     -H "Content-Type: application/json" \
     -d '{"input": "test"}'
   ```

**For now (with mocks):**

The pipeline is fully functional for testing and dry-runs. Production real-inference integration is a future step.

---

## Quick Reference: Common Commands

```bash
# Dry-run (safe)
bash scripts/run_enrichment_dryrun.sh

# Check batch health
python3 scripts/monitor_batch.py

# Run full batch
python3 scripts/enrich_batch.py --workers 4

# View enrichment results
sqlite3 data/merit_registry.db \
  "SELECT * FROM enrichment_run WHERE run_date = DATE('now') LIMIT 5;"

# View quality metrics
sqlite3 data/merit_registry.db \
  "SELECT * FROM quality_log ORDER BY date DESC LIMIT 5;"

# Check how many orgs need enrichment
sqlite3 data/merit_registry.db \
  "SELECT COUNT(*) FROM registry_enriched 
   WHERE (cause_tags IS NULL OR cause_tags = '') 
      OR (website IS NULL OR website = '');"

# View cron logs
tail -f logs/enrich_batch_*.log
tail -f logs/quality_cron_*.log

# Verify cron jobs are installed
crontab -l | grep enrich
```

---

## Escalation: When to Ask for Help

If you encounter errors not covered here, check:

1. **Logs first** — Look at `logs/enrich_batch_*.log`, `logs/quality_cron_*.log`, etc.
2. **Database integrity** — Run `sqlite3 data/merit_registry.db "PRAGMA integrity_check;"`
3. **Recent commits** — Check git history for recent changes: `git log --oneline -10`
4. **Test suite** — Run tests to verify nothing is broken: `pytest tests/test_enrichment*.py -v`

If all else fails, escalate with:
- The error message (full stack trace from logs)
- Which command failed (enrich_batch.py, monitor_batch.py, cron job, etc.)
- When it last worked (date/time)
- Current git commit hash: `git rev-parse HEAD`
