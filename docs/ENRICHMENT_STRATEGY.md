# Enrichment Pipeline Strategy

## Current Schedule: 8pm-9am Nightly (GPU-Bound)

The consolidated enrichment pipeline runs exclusively during overnight hours to maximize GPU utilization while keeping heat/power reasonable.

### Nightly Job (22:00-09:00)
```
cron_enrich_nightly.sh @ 22:00 (10pm)
├── GPU: mission generation (Qwen3-30B via llama-server)
├── GPU: embedding re-sync (mxbai-embed-large via llama-server)
└── CPU: cause tag consolidation + website validation (triggered by GPU tasks)
```

**Why 10pm start (not 9pm)?**
- 21:00: gpu_night.sh start — boots llama-server (startup cost ~30s)
- 22:00: enrichment batch begins — GPU servers warm and ready
- 09:00: gpu_night.sh stop — end of window, GPU shutdown begins

---

## 24/7 Candidates: CPU-Only Tasks

These tasks can run continuously without GPU contention or heat/power concerns:

### ✅ Safe for 24/7
1. **Cause tag consolidation (batch)** — runs in 4-worker pool, finishes <5min per batch
   - CPU: ~40-60% on batches
   - Network: minimal (reads DB, no external APIs)
   - Schedule: `enrich_batch.py --cause-tags-only --continuous` with 30-60s batch interval

2. **Database cleanup & optimization** — SQLite VACUUM, index maintenance
   - CPU: <10% (I/O bound)
   - Schedule: `sqlite3 merit_registry.db VACUUM` after large batches

3. **FTS index incremental updates** — rebuild search index for new records
   - CPU: ~50% (batch process, completes <30s per 1K rows)
   - Prerequisites: new missions must be ready (use 8pm-9am missions from GPU)
   - Schedule: `build_fts_index.py --incremental` every 6 hours (3am, 9am, 3pm, 9pm)

### ⚠️ NOT Safe for 24/7
1. **Website crawling/validation** — external network, puts load on remote hosts
   - Schedule: Keep to 8pm-9am only
   
2. **Mission generation (Qwen GPU)** — thermal load, power budget
   - Schedule: 8pm-9am nightly only

3. **Semantic re-embedding (mxbai GPU)** — GPU memory, cooling
   - Schedule: 8pm-9am nightly only

---

## Implementation Roadmap

### Phase 1: Current (Deployed)
- ✅ GPU enrichment pipeline: 8pm-9am nightly
- ✅ Monitoring loop: `scripts/monitor_enrichment_window.sh`
- Monitor via: `/loop monitor_enrichment_window.sh`

### Phase 2: Expand CPU Capacity (Optional)
If cause-tag consolidation backlog grows:
```bash
# Add to crontab (safe for 24/7):
*/30 * * * * cd /home/akbar/meritgiving && ./venv/bin/python3 scripts/enrich_batch.py --cause-tags-only --batch 500 >> logs/continuous_enrich.log 2>&1
```

### Phase 3: Incremental FTS Updates (Future)
```bash
# Every 6 hours, rebuild search index for new orgs
0 3,9,15,21 * * * cd /home/akbar/meritgiving && ./venv/bin/python3 scripts/build_fts_index.py --incremental >> logs/fts_incremental.log 2>&1
```

---

## Monitoring

Live monitoring during active hours (8pm-9am):
```bash
./loop "bash scripts/monitor_enrichment_window.sh"
```

Check logs:
```bash
tail -f logs/enrich_nightly.log       # enrichment batch
tail -f logs/gpu_night.log            # GPU pipeline
tail -f logs/generate_missions_32b.log # mission generation
tail -f logs/reembed_watchdog.log     # re-embedding
```

---

## Performance Targets

- **Mission generation**: 50-100 orgs/min (GPU-bound, ~8-10h for 1.7M backlog)
- **Cause tags**: 200-500 orgs/min (CPU, batches per 5-10 min)
- **Embeddings**: 1000-2000 vectors/min (GPU, real-time via mxbai)
- **FTS rebuild**: <30s per 1K new orgs (CPU, once daily post-GPU-window)

---

## Heat & Power Notes

**Ryzen 9700X + R9700 GPU (Vulkan1):**
- Idle: ~30W total
- GPU 24/7: ~150-200W sustained (not advised; thermal throttling risk)
- Nightly 8h burst: ~200-250W (sustainable, 8h cooling window during day)
- CPU-only tasks: ~40-80W (safe 24/7, headroom for other ops)

Current strategy: GPU off during day, full power during night = best compromise for equipment lifespan and energy.
