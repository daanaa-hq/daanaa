# Overnight Automation Schedule (8 Hours: ~04:45 UTC → 12:45 UTC)

**Date:** 2026-07-24 → 2026-07-25  
**Duration:** 8 hours  
**Mode:** Full autonomous operation (no user input needed)  
**Server Utilization:** 70-80% CPU, 60-70% RAM (all productive work)  

---

## Task Timeline

### HOUR 1 (04:45 - 05:45 UTC): Phase 3 Discovery Completion
**Status:** Already running (launched 04:50 UTC)

**Worker Activity:**
- 8 workers processing 400-650 nonprofit websites
- Strategies: Google, Charity Navigator, state registries
- Target: 70%+ success rate
- Audit logging every attempt (no PII)

**Output:**
- ~280-450 websites recovered (estimated)
- ~50-100 events extracted
- Audit log: 500+ discovery events logged

**Expected Completion:** 05:30 UTC (500+ websites target)

---

### HOUR 2 (05:45 - 06:45 UTC): Phase 3 Learning Extraction

**Script:** `scripts/phase3_learning_analysis.py` (NEW)

**Analysis:**
1. Aggregate discovery statistics
   - Success rate by NTEE (which categories easiest?)
   - Success rate by state (geographic patterns)
   - Success rate by org size (small vs. large)
   - Success rate by strategy (which method worked best?)

2. Error pattern analysis
   - Top 10 failure reasons (timeout, 404, parse error, etc.)
   - Retry opportunities (which should be retried?)
   - Rate limit patterns (did we get blocked?)

3. Algorithm improvement recommendations
   - Boost confidence for successful strategies
   - Adjust timeout for slow discovery methods
   - Identify next batch targets (by NTEE/state gap)

4. Generate lessons learned doc
   - What worked: 3-5 specific findings
   - What failed: root causes
   - What's next: recommendations for Phase 3-B

**Output:**
- `docs/PHASE_3_LEARNING_RESULTS_2026_07_25.md` (written to disk)
- Audit log summary: `discovery_batch_analysis_complete`
- Recommendations for next 500 orgs

**Duration:** ~30 min
**Expected Completion:** 06:15 UTC

---

### HOUR 3 (06:45 - 07:45 UTC): Database Import + Maintenance

**Script:** `scripts/phase3_import_results.py` (NEW)

**Import Phase 3 Results:**
```sql
UPDATE registry_enriched
  SET website = ?, website_status = 'valid', website_discovery_strategy = ?
  WHERE ein IN (recovered 400-450 EINs)
  
INSERT INTO volunteer_hours_events_impact
  (org_ein, event_name, event_date, event_type, source)
  VALUES (...) -- 50-100 new events
```

**Database Maintenance:**
1. **VACUUM** (15 min)
   - Reclaim deleted space from audit_log, old records
   - Defragment indexes
   - Update statistics

2. **Index Rebuild** (10 min)
   - Rebuild FTS5 search index (if needed)
   - Rebuild org_embeddings indexes
   - Refresh query plans

3. **Integrity Check** (5 min)
   - PRAGMA integrity_check
   - Verify no corruption
   - Log result to audit trail

**Output:**
- 400-450 websites updated in registry_enriched
- 50-100 events added to volunteer_hours_events_impact
- Database optimized, indexes rebuilt
- Disk space reclaimed (~100-200MB)

**Duration:** ~45 min
**Expected Completion:** 07:30 UTC

---

### HOUR 4-5 (07:45 - 09:45 UTC): Nightly Data Pipeline

**Script:** `scripts/overnight_pipeline.py` (EXISTING, run nightly)

**Purpose:** Score orgs, rebuild search, generate reports

**Stage 1: Scoring** (30 min)
- Run `scripts/merit_scorer_v4_0.py`
- v5 peer financial context scores
- Recompute for recovered websites (higher accuracy with URLs)
- Update ntee1_percentile, peer_rank

**Stage 2: Search Index** (15 min)
- Run `scripts/build_fts_index.py`
- Rebuild FTS5 index with new orgs
- Include discovered websites in search
- Update `org_fts` virtual table

**Stage 3: Embeddings** (20 min)
- Run `scripts/build_org_embeddings.py`
- Generate mxbai vectors for new/updated orgs
- Update `org_embeddings` table
- Preload into memory for fast inference

**Stage 4: Missions** (15 min)
- Run `scripts/generate_missions.py`
- Use Qwen3-30B-A3B (local inference)
- Generate/refresh missions for 50+ new events
- Store in registry_enriched.mission

**Stage 5: Stats Export** (10 min)
- Generate `docs/statistics_snapshot_YYYYMMDD.json`
- Sector health, peer group counts, coverage metrics
- Upload to S3 for dashboard

**Output:**
- 400-450 orgs re-scored (v5 context)
- Search index refreshed (FTS5 + embeddings)
- 50+ volunteer event missions generated
- Statistics snapshot exported

**Duration:** ~90 min
**Expected Completion:** 09:15 UTC

---

### HOUR 6 (09:45 - 10:45 UTC): Enrichment Pipeline

**Script:** `scripts/enrich_discovered_websites.py` (NEW)

**Purpose:** Extract data from newly discovered websites

**Processing:**
1. **Website Content Scraping** (30 min, 8 workers)
   - Fetch & parse organization pages
   - Extract: mission, contact, leadership, programs
   - Store rich text in `registry_enriched.org_content`

2. **Cause Tag Extraction** (15 min)
   - Use mxbai + clustering to categorize new orgs
   - Compare website content + IRS NTEE
   - Update `registry_enriched.cause_tags`

3. **Media Asset Discovery** (10 min)
   - Find logo, hero image from website
   - Store asset URLs for frontend display
   - Cache metadata

**Output:**
- 400+ orgs enriched with website content
- Cause tags updated (AI-extracted from websites)
- Asset URLs cached for 48h

**Duration:** ~60 min
**Expected Completion:** 10:45 UTC

---

### HOUR 7-8 (10:45 - 12:45 UTC): Backup, Monitoring, Reports

**Stage 1: Backup** (15 min)
- Snapshot database: `daanaa_backup_$(date +%s).db`
- Compress to S3: `s3://daanaa-backups/db/`
- Verify integrity: read back from S3
- Clean old backups (keep last 7 days)

**Stage 2: Health Check** (10 min)
- Verify all APIs responding
- Check database size + growth rate
- Confirm inference servers healthy
- Test droplet connectivity

**Stage 3: Reporting** (30 min)

Generate overnight reports:

1. **Discovery Report** (`docs/DISCOVERY_REPORT_2026_07_25.md`)
   - 500+ websites recovered
   - Success rate by NTEE/state
   - Top strategies used
   - Recommendations

2. **Pipeline Report** (`docs/PIPELINE_REPORT_2026_07_25.md`)
   - Scoring results (400+ orgs)
   - Search index stats
   - Embeddings loaded
   - Missions generated

3. **System Health** (`docs/HEALTH_REPORT_2026_07_25.md`)
   - Database size, growth rate
   - API latency (P50/P95/P99)
   - Inference server loads
   - Memory/CPU utilization

4. **Audit Summary** (`docs/AUDIT_SUMMARY_2026_07_25.md`)
   - Total events logged: ~1,000+
   - Event breakdown by type
   - Error patterns
   - Compliance: zero PII

**Stage 4: Slack Notification** (5 min)
- Send summary to #ops channel (if configured)
- Include: websites recovered, events found, success metrics
- Flag any alerts or anomalies

**Output:**
- Database backed up to S3
- 4 comprehensive reports generated
- Team notified of results
- System health confirmed

**Duration:** ~60 min
**Expected Completion:** 12:45 UTC

---

## Resource Allocation (Overnight)

```
CPU Allocation (8 cores):
├── Workers 1-4: Discovery (04:45 - 05:30)    → Phase 3 completion
├── Workers 5-6: Enrichment (09:45 - 10:45)   → Website scraping
├── Workers 7-8: Backup (10:45 - 11:00)       → Database ops
└── Background: Scoring pipeline (07:45 - 09:45) → FTS5, embeddings

RAM Allocation (30GB):
├── Qwen3-30B-A3B: 14GB (fixed)
├── mxbai-embed-large: 1GB (fixed)
├── DeepSeek-R1-8B: 8.2GB (new)
├── Discovery workers: 0.5GB
├── Scoring/pipeline: 2GB
├── Database cache: 2GB
└── System + headroom: 1.3GB

GPU (AMD Radeon ROCm):
├── Qwen3 inference: 40-50% (scoring, missions)
├── mxbai inference: 30-40% (embeddings)
└── Peak: 70-80% during parallel stages
```

---

## Expected Results (By Morning)

**Quantitative:**
- ✅ 400-450 nonprofit websites recovered
- ✅ 50-100 new volunteer events extracted
- ✅ 400+ orgs re-scored (v5 peer context)
- ✅ 1,000+ audit log entries created
- ✅ Search index updated (FTS5 + embeddings)
- ✅ Database backed up (S3)

**Qualitative:**
- ✅ Website discovery success metrics documented
- ✅ Algorithm improvements identified
- ✅ Enrichment pipeline complete
- ✅ System health verified
- ✅ All reports ready for morning review

**File Outputs:**
```
docs/
├── PHASE_3_LEARNING_RESULTS_2026_07_25.md
├── DISCOVERY_REPORT_2026_07_25.md
├── PIPELINE_REPORT_2026_07_25.md
├── HEALTH_REPORT_2026_07_25.md
└── AUDIT_SUMMARY_2026_07_25.md

backups/
└── daanaa_backup_[timestamp].db.gz (S3)
```

---

## Monitoring While You Sleep

**Automated Checks (Every 15 min):**
```bash
# Database size + growth
du -sh ~/meritgiving/data/merit_registry.db

# CPU/Memory utilization
top -b -n 1 | grep -E "Cpu|Mem"

# Audit log entries (count grows)
sqlite3 ~/meritgiving/data/merit_registry.db "SELECT COUNT(*) FROM audit_log"

# API health (if droplet monitoring enabled)
curl http://127.0.0.1:5000/health
```

**Alert Triggers (Automatic halt if any occur):**
- ❌ CPU sustained >95% (thermal throttling risk)
- ❌ RAM >95% (swap thrashing, slowdown)
- ❌ Database corrupt (PRAGMA integrity_check fails)
- ❌ API non-responsive (health check timeout)

---

## Timeline Summary

| Time | Duration | Task | Expected Output |
|------|----------|------|-----------------|
| 04:45 - 05:30 | 45 min | Phase 3 Discovery | 400-450 websites |
| 05:45 - 06:15 | 30 min | Learning Analysis | Improvement recommendations |
| 06:45 - 07:30 | 45 min | Import + Maintenance | Database updated, optimized |
| 07:45 - 09:15 | 90 min | Nightly Pipeline | Scoring, search, embeddings |
| 09:45 - 10:45 | 60 min | Enrichment | Website content extracted |
| 10:45 - 12:45 | 120 min | Backup + Reports | All reports ready |
| **Total** | **390 min** | **All tasks** | **System updated, optimized** |

---

## What You'll See in the Morning

**By 08:00 UTC (user wakes up):**
- Phase 3 discovery complete (✅ ~500 websites)
- Learning analysis document ready (✅ recommendations)
- Nightly pipeline running (FTS5 + embeddings updating live)

**By 12:00 UTC (user checks in):**
- All 8 hours complete
- 5 comprehensive reports generated
- Database backed up to S3
- System optimized and ready for pilot

---

## Cost of Overnight Work

**Electricity (8 hours, 8 cores @ 250W avg):**
- 8 hours × 250W = 2 kWh
- At $0.12/kWh = ~$0.24 (negligible)

**Inference Cost (local, not cloud):**
- Qwen3: 0 (local GPU, ROCm)
- mxbai: 0 (local GPU, preloaded)
- DeepSeek: 0 (local GPU, ROCm)
- Total: $0 (all local inference)

**Data Storage (S3 backup):**
- 1 database backup (~10GB compressed) = ~$0.23/month

**ROI:**
- 500 websites recovered (20+ volunteers likely find new orgs)
- 100 events extracted (platform richness improved)
- 4 reports generated (morning decision-making data)
- Cost: ~$0.25 electricity

---

**Overnight Automation Status:** READY  
**Start Time:** ~04:45 UTC (when Phase 3 launches)  
**Completion Time:** ~12:45 UTC (8 hours)  
**Reports Ready:** By morning for review  

Sleep well — the system will optimize itself overnight.
