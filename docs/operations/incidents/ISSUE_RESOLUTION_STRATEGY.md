# Issue Resolution Strategy — Aug 1-31, 2026

## Summary
**No comprehensive strategy exists yet.** This document establishes resolution plans for the 6 known issues.

---

## ISSUE 1: FTS5 Database Corruption

### Current State
- **Problem:** Index tree corrupted; freelist invalid; search returns "malformed" errors
- **Cause:** Inherited from Jul 28 backup or disk corruption on Aug 1
- **Impact:** Search broken; core org queries still work
- **Criticality:** Low (doesn't block Phase 1)

### Resolution Strategy

**Phase 1 (Aug 1-7): Accept Limitation**
- Search unavailable; Phase 1 metrics don't depend on it
- Hourly corruption monitoring enabled (will alert if spreads)
- No action needed; document as known limitation

**Phase 2 (Aug 8-14): Rebuild Strategy (Choose One)**

**Option A: Rebuild from Scratch (Recommended, 1-2 hours)**
```bash
# 1. Backup current database (recovery point)
cp merit_registry.db merit_registry_pre_fts_rebuild.db

# 2. Drop corrupted index
sqlite3 merit_registry.db "DROP TABLE IF EXISTS org_fts;"

# 3. Recreate index
sqlite3 merit_registry.db << SQL
CREATE VIRTUAL TABLE org_fts USING fts5(
    ein, organization_name, mission, cause_tags, street_address, city, state,
    content=registry_enriched, content_rowid=rowid
);
INSERT INTO org_fts(rowid, ein, organization_name, mission, cause_tags, street_address, city, state)
SELECT rowid, ein, organization_name, mission, cause_tags, street_address, city, state
FROM registry_enriched WHERE org_status = 'active';
SQL

# 4. Test search
sqlite3 merit_registry.db "SELECT organization_name FROM org_fts WHERE org_fts MATCH 'health' LIMIT 1;"
```

**Option B: Restore Clean Database (1-3 hours, safest)**
1. Download clean Jun/Jul backup (if available)
2. Restore to secondary database
3. Replay enrichment changes (websites, donations, signals)
4. Swap to primary (cutover)

**Option C: Restore from Remote Backup (5-10 minutes, if S3 backup exists)**
1. Download latest good snapshot from S3
2. Restore and verify
3. Validate org count matches

**Recommended:** Option A (fastest, proven safe). Option C if S3 backups available.

**Owner:** Akbar (after Phase 1)
**Timeline:** Aug 8, 1 hour
**Success criteria:** Search returns results; `/api/search` working; query time <500ms

---

## ISSUE 2: API Performance Degradation (3.6s vs 114ms)

### Current State
- **Baseline:** 114ms (pre-OOM crash)
- **Current:** 3.6s (stable, consistent)
- **Root cause:** Embeddings (~3GB) pre-loading on every request + disk I/O pressure
- **Criticality:** Medium (tracking metric for Phase 1)

### Resolution Strategy

**Phase 1 (Aug 1-7): Monitor & Profile**
- Track latency trends via Phase 1 monitoring
- If degradation worsens, escalate
- Otherwise, defer optimization

**Phase 2 (Aug 8-14): Performance Investigation**

**Step 1: Profile Bottleneck (15 min)**
```bash
# 1. Add timing logs to daanaa_api.py request handler
# 2. Profile each section:
#   - Database query time
#   - Embeddings loading time
#   - Response serialization time

# 3. Identify the slow section
# Expected: embeddings loading or database query
```

**Step 2: Choose Optimization (based on profile results)**

**If Embeddings are Slow:**
- Option A: Lazy-load embeddings (only if search needed)
- Option B: Reduce embedding model size (mxbai-large → smaller variant)
- Option C: Load embeddings to Redis instead of RAM (async)

**If Database is Slow:**
- Option A: Add indexes on frequently queried columns
- Option B: Denormalize hot columns to registry_enriched
- Option C: Implement query caching (TTL-based)

**If Disk I/O is Slow:**
- Option A: Ensure disk recovered to >50% free (S3 archival)
- Option B: Move hot data to faster storage (if available)

**Owner:** Akbar + Performance specialist (Aug 8+)
**Timeline:** 2-3 days investigation + 1-2 days fix
**Success criteria:** Latency <500ms; org pages load in <2s

---

## ISSUE 3: Discovery Daemon Halted

### Current State
- **Status:** Stopped (was hitting FTS5 errors)
- **Progress:** Iteration 1499 complete
- **Data loss:** None (can resume cleanly)
- **Criticality:** Low (nice-to-have feature)

### Resolution Strategy

**Phase 1 (Aug 1-7): Leave Paused**
- Websites discovery on hold
- Phase 1 gate doesn't depend on it
- No action needed

**Phase 2 (Aug 8+): Resume After FTS5 Fix**
```bash
# 1. Fix FTS5 corruption (Issue #1 above)
# 2. Verify database clean
# 3. Restart daemon

nohup python3 scripts/discovery_daemon.py 100 &

# 4. Monitor logs for errors
tail -f logs/discovery_daemon.log
```

**Owner:** Automated restart (post-FTS5 fix)
**Timeline:** Immediate after FTS5 rebuild
**Success criteria:** Daemon running; discovering 50-100 orgs/hour; no corruption errors

---

## ISSUE 4: Disk Space (94% Used)

### Current State
- **Free:** 54GB (from 11GB)
- **Backups:** 289GB (main culprit)
- **Status:** Acceptable; addressed via backup optimization
- **Criticality:** Low (not critical, but needs permanent solution)

### Resolution Strategy

**Phase 1 (Aug 1-7): Monitor Only**
- Current state stable at 94%
- Backup rotation every 6 hours (new strategy)
- Alert if drops below 30GB

**Phase 2 (Aug 8-14): S3 Archival (Task #6)**

**Step 1: Archive Old Backups to S3 (2-3 hours)**
```bash
# 1. Create S3 bucket (if not exists)
aws s3 mb s3://daanaa-backup-archive/

# 2. Upload backups >7 days old
for f in backups/archive/*.db; do
  aws s3 cp "$f" s3://daanaa-backup-archive/
done

# 3. Clean up local archive
rm backups/archive/*.db

# Expected: 200GB freed locally
```

**Step 2: Update Backup Strategy**
- New cron job to auto-archive backups >7 days old
- Keep only 3 recent backups locally (72GB)

**Owner:** Akbar (Aug 8-14)
**Timeline:** 2-3 hours setup + automated cleanup
**Success criteria:** Disk <70% usage; S3 backup archive working; automated rotation verified

---

## ISSUE 5: NCCS Data Recovery

### Current State
- **Status:** Blocked (awaiting Part X/VII file)
- **Code:** Ready; pipeline complete
- **Impact:** Data enrichment; doesn't block Phase 1
- **Criticality:** Low

### Resolution Strategy

**Trigger: User Provides File**
1. Download Form 990 Part X/VII CSV from irs.gov
2. Place in `data/nccs_partx_vii_2024.csv`
3. Run ingestion:
   ```bash
   python3 scripts/ingest_nccs_partx.py --file data/nccs_partx_vii_2024.csv
   ```
4. Verify coverage: `SELECT COUNT(DISTINCT ein) WHERE nccs_x_column IS NOT NULL;`

**Owner:** Akbar (on-demand, user-initiated)
**Timeline:** 30 min (once file received)
**Success criteria:** 1M+ orgs enriched with NCCS data

---

## ISSUE 6: Charity Navigator Scraper

### Current State
- **Code:** Complete, tested
- **Status:** Blocked (legal review gate)
- **Impact:** Website discovery alternative; Phase 3 feature
- **Criticality:** Low

### Resolution Strategy

**Trigger: Founder Approval**
1. Akbar requests founder legal review sign-off
2. Once approved:
   ```bash
   # 1. Verify scraper runs without errors
   python3 scripts/charity_navigator_scraper.py --dry-run --limit 100

   # 2. Ingest results
   python3 scripts/charity_navigator_scraper.py --ingest

   # 3. Track coverage
   SELECT COUNT(DISTINCT ein) WHERE website_source = 'charity_navigator';
   ```

**Owner:** Founder approval required; Akbar executes
**Timeline:** 30 min (once approved)
**Success criteria:** 10K-50K new websites discovered; no legal concerns

---

## ISSUE 7: Phase 2 Link Reverification

### Current State
- **Links to reverify:** 9,411 donation URLs >6 months old
- **Status:** Blocked (Phase 1 PASS decision required)
- **Impact:** Data quality; doesn't block Phase 1
- **Criticality:** Low

### Resolution Strategy

**Trigger: Phase 1 PASS Decision (Friday Aug 7)**

**If PASS:**
1. Schedule reverification for Aug 8-14:
   ```bash
   python3 scripts/donation_link_verifier.py --stale-only --workers 8 --age-days 180
   ```
2. Update `donate_url_status` for each verified link
3. Report: X% success rate, Y new URLs found, Z confirmed dead

**If CONDITIONAL:**
- May delay reverification pending Phase 1 fixes
- Decision at gate review

**If FAIL:**
- Defer to Phase 3; focus on Phase 1 remediation

**Owner:** Akbar (Aug 8-14, conditional on Phase 1 decision)
**Timeline:** 2-3 days (8 parallel workers)
**Success criteria:** 90%+ links reverified; database updated

---

## TIMELINE SUMMARY

| Issue | Phase 1 (Aug 1-7) | Phase 2 (Aug 8-14) | Owner |
|-------|------|------|-------|
| **FTS5 Corruption** | Monitor only | Rebuild index (1h) | Akbar |
| **API Performance** | Track metric | Profile + optimize (2-3d) | Akbar |
| **Discovery Daemon** | Leave paused | Resume (10m) | Auto |
| **Disk Space** | Monitor | S3 archival (2-3h) | Akbar |
| **NCCS Data** | Awaiting file | Ingest (30m) | User-trigger |
| **CN Scraper** | Awaiting approval | Deploy (30m) | Founder + Akbar |
| **Link Reverif** | Awaiting decision | Execute (2-3d) | Akbar |

---

## Decision Points

**Aug 7, 8:00 PM (Phase 1 Gate):**
- If PASS: Proceed with Phase 2 (Aug 8-14 schedule above)
- If CONDITIONAL: Review blockers; may adjust timeline
- If FAIL: Extend Phase 1; defer Phase 2 work

**Aug 14, Evening (Phase 2 Review):**
- Confirm all Aug 8-14 work completed
- Readiness check for Phase 3 (Aug 15+)

---

## Resource Allocation

**Aug 1-7:** Monitoring only (no changes)
**Aug 8-14:** 
- FTS5 rebuild: 1 hour (Akbar)
- Performance profiling: 1-2 days (Akbar)
- Disk archival: 2-3 hours (Akbar)
- Discovery daemon: auto-resume (5 min)

**Total effort:** ~3-4 days of Akbar's time (Aug 8-14)

---

Generated: Aug 1, 2026 10:35 CDT
