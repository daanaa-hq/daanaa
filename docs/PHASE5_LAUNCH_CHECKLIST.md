# Phase 5 Launch Checklist

Complete this checklist before launching Phase 5 mission & cause backfill.

---

## Pre-Launch (5 min)

- [ ] **Phase 4 Complete?**
  ```bash
  sqlite3 ~/meritgiving/data/merit_registry.db \
    "SELECT COUNT(*) FROM registry_enriched WHERE semantic_match = 1;"
  ```
  Expected: > 0 orgs verified.

- [ ] **Qwen2.5-32B Running?**
  ```bash
  curl http://127.0.0.1:11437/health
  ```
  Expected: HTTP 200 or similar health response.

- [ ] **Database Accessible?**
  ```bash
  sqlite3 ~/meritgiving/data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched;"
  ```
  Expected: No errors, returns org count.

- [ ] **Logs Directory Exists?**
  ```bash
  mkdir -p ~/meritgiving/logs
  ```

- [ ] **Python Venv Activated?**
  ```bash
  source ~/meritgiving/venv/bin/activate
  python3 --version
  ```
  Expected: Python 3.10+

---

## Launch (1 min)

```bash
# Fresh start
bash ~/meritgiving/scripts/launch_phase5_bg.sh

# OR resume from checkpoint (if interrupted)
bash ~/meritgiving/scripts/launch_phase5_bg.sh --resume
```

Expected output:
```
[OK] Database OK (18432 verified orgs)
[OK] LLM responding
[OK] All health checks passed

[OK] Started with PID 12345
Progress: tail -f /tmp/phase5_progress.log
Monitor: tail -f ~/meritgiving/logs/phase5_monitor.log
```

---

## Monitoring (Ongoing)

### Terminal 1: Progress Log
```bash
tail -f /tmp/phase5_progress.log
```

### Terminal 2: Real-Time Monitor
```bash
python3 ~/meritgiving/scripts/phase5_monitor.py
```

### Terminal 3: Launcher Log
```bash
tail -f ~/meritgiving/logs/phase5_monitor.log
```

---

## Expected Behavior

### First Hour
- Batches 1-60 processed (if system is healthy)
- Speed: 60+ orgs/min
- No errors logged (or < 2%)

### Ongoing
- Checkpoints saved every 100 orgs
- Steady speed 50-60 orgs/min
- Minimal LLM errors (< 1%)

### If Stalled
- Check LLM status: `curl http://127.0.0.1:11437/health`
- Check process: `ps aux | grep phase5`
- Check logs for errors: `tail -100 /tmp/phase5_progress.log`
- Restart if needed: `bash scripts/launch_phase5_bg.sh --resume`

---

## Stopping Phase 5

If needed to interrupt:
```bash
# Graceful stop (will resume next time)
bash ~/meritgiving/scripts/launch_phase5_bg.sh --stop

# Check what was completed
cat ~/meritgiving/logs/phase5_checkpoint.json | jq .
```

---

## Post-Launch (After Completion)

### When You See "Phase 5 Complete!" in Logs

- [ ] **Verify Results**
  ```bash
  sqlite3 ~/meritgiving/data/merit_registry.db \
    "SELECT COUNT(*), COUNT(CASE WHEN mission IS NOT NULL THEN 1 END) \
     FROM registry_enriched WHERE semantic_match = 1;"
  ```
  Expected: Second count should equal first count (all have missions now).

- [ ] **Check Sample Missions**
  ```bash
  sqlite3 ~/meritgiving/data/merit_registry.db \
    "SELECT EIN, organization_name, mission FROM registry_enriched \
     WHERE mission_source='ai_generated' LIMIT 5;"
  ```

- [ ] **Rebuild FTS Index** (optional, if search broken)
  ```bash
  python3 scripts/build_fts_index.py
  ```

- [ ] **Restart API** (to cache new data)
  ```bash
  pkill -f daanaa_api || true
  source venv/bin/activate
  ./restart_api.sh
  ```

- [ ] **Sync to Droplet** (if running)
  ```bash
  bash scripts/safe_deploy_droplet.sh
  ```

---

## Troubleshooting

### Error: "Phase 4 not complete"

Phase 4 hasn't run or is still in progress.

**Fix:**
```bash
# Check Phase 4 status
ls -lh ~/meritgiving/logs/phase4_checkpoint.json

# If missing, start Phase 4
python3 scripts/phase4_semantic_verification.py --workers 8
```

### Error: "No verified orgs found"

Phase 4 completed but found no matches.

**Fix:**
```bash
# Check Phase 4 results
sqlite3 ~/meritgiving/data/merit_registry.db \
  "SELECT COUNT(*) FROM registry_enriched WHERE semantic_match = 1;"

# If 0, Phase 4 may need more time or tuning
```

### Process Crashes Repeatedly

LLM is overloaded or crashing.

**Fix:**
```bash
# Check LLM health
curl -v http://127.0.0.1:11437/health

# Reduce batch size for testing
python3 scripts/phase5_mission_backfill.py --limit 100 --workers 4

# If that works, increase gradually
python3 scripts/phase5_mission_backfill.py --resume --workers 8
```

### "Database locked" Errors

Other scripts writing to database.

**Fix:**
```bash
# List running processes
pgrep -af "python3 scripts"

# Wait for other jobs or stop them temporarily
```

---

## Cleanup

After Phase 5 completes and you've verified results:

```bash
# Archive checkpoint (keep for reference)
cp ~/meritgiving/logs/phase5_checkpoint.json \
   ~/meritgiving/logs/phase5_checkpoint_FINAL.json

# Clear progress log if disk space needed
rm /tmp/phase5_progress.log

# Check disk usage
du -sh ~/meritgiving/data/*
du -sh ~/meritgiving/logs/*
```

---

## Timeline Estimate

| Phase | Orgs | Speed | Duration |
|-------|------|-------|----------|
| Phase 4 | 200K+ | 1-2 embeddings/sec | 2-3 days |
| **Phase 5** | **18K-25K** | **~60 orgs/min** | **30-40 hours** |
| Phase 5 FTS rebuild | All | ~1M/min | 10-15 min |
| API restart + cache warm | All | ~1K/sec | < 1 min |

---

## Success Criteria

✅ Phase 5 launch successful if:

1. All health checks pass
2. Process runs without crashing > 1 hour
3. Speed stays above 30 orgs/min (not stalled)
4. No more than 2% LLM errors
5. Checkpoints saving every 100 orgs
6. Final message: "Phase 5 Complete!"
7. Database shows all verified orgs have missions

---

## Questions?

See `docs/PHASE5.md` for full documentation.
