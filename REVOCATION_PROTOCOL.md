# Revocation Protocol — Critical Data Freshness

**Principle**: No org with stale revocation status can be shown to users.

---

## The Problem

- IRS automatically revokes 501(c)(3) status when orgs don't file for 3+ years
- Daanaa indexes ~1.8M orgs; revocation status changes monthly
- If we show a user a revoked org, we've broken trust (they might donate to a defunct org)
- **Stale data = legal risk + user harm**

---

## The Solution: 3-Layer Protocol

### Layer 1: Automatic Sync (Daily)
```
2:00 AM (cron)  → overnight_sync.py       (merge IRS 990s)
  ↓
2:30 AM (cron)  → overnight_pipeline.py   (ProPublica enrichment)
  ↓
[Optional]      → sync_irs_revocations.py (check revocation list)
```

**Status**: overnight_sync + overnight_pipeline now scheduled  
**Gap**: sync_irs_revocations needs daily schedule too

### Layer 2: Immediate Verification (On Backfill Complete)
```
Phase 2 backfill complete
  ↓
revocation_check_on_backfill_complete.py runs automatically
  ↓
1. sync_irs_revocations.py (full download + compare)
  ↓
2. check_newly_revoked() (flag any revoked orgs in batch)
  ↓
3. invalidate_api_cache() (mark cache stale)
```

**Status**: Script created, integrated into backfill monitor  
**Action**: Monitoring loop now checks + triggers on completion

### Layer 3: API Safeguards
```python
GET /api/organizations/<EIN>
  ↓
if EIN in revoked_eins table:
    → HTTP 410 Gone (Org no longer exists)
    → Don't serve details, never serve as recommendation
```

**Status**: revoked_eins table exists (1.2M rows)  
**Gap**: API doesn't check this — would serve revoked orgs

---

## Data Freshness Targets

| Metric | Target | Current | Action |
|--------|--------|---------|--------|
| Revocation list age | ≤ 30 days | ~7 days | ✅ OK |
| Sync frequency | Daily | [Will be 2 AM] | ⏳ Scheduled |
| New org revocation check | Immediately | [Automated] | ⏳ Monitoring |
| API cache age | ≤ 24h | In-memory, no TTL | ⚠️ Manual restart |

---

## Automated Workflow (Starting 2026-06-10)

```
2026-06-09 04:07 UTC
  ↓ Phase 2 enrichment starts (26.5K new BMF orgs)
  ↓
2026-06-[XX] ~HH:MM UTC
  ↓ Phase 2 complete
  ↓
  → revocation_check_on_backfill_complete.py triggers
  → sync_irs_revocations.py runs
  → Checks for newly-revoked orgs
  → Invalidates API cache marker
  ↓
[If revoked orgs found]
  → Log alert: "N orgs are revoked"
  → Require: API restart to clear cache
  ↓
[Post-restart]
  → API returns HTTP 410 for revoked EINs
  → Frontend removes them from results
```

---

## Monitoring Commands

```bash
# Watch for backfill completion + revocation checks
tail -f logs/backfill_new_bmf.log
tail -f logs/revocation_check_monitor.log

# Check revocation list freshness
ls -lh data/irs_revocation_cache.csv

# See which orgs are revoked
sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM revoked_eins;"

# Manual sync (if needed)
python3 scripts/sync_irs_revocations.py

# Check for revoked orgs in new batch
sqlite3 data/merit_registry.db "
  SELECT COUNT(*) FROM registry_enriched re
  WHERE re.EIN IN (SELECT EIN FROM revoked_eins)
  AND re.source = 'IRS_BMF'
  AND re.updated_at > datetime('now', '-2 days');
"
```

---

## Alert Scenarios

### 🟢 Green (All Good)
- Revocation list age: < 30 days
- Zero revoked orgs in new batch
- API cache shows current data
- No stale orgs being served

### 🟡 Yellow (Action Recommended)
- Revocation list age: 30-45 days
- Revocation sync scheduled but not yet run
- **Action**: Run `sync_irs_revocations.py` manually
- **Impact**: Low; only affects newly-added orgs from last sync window

### 🔴 Red (Critical)
- Revoked orgs found in new batch
- API still serving old cache (stale org data)
- **Action**: Restart API immediately
- **Impact**: High; users could see defunct orgs as searchable

---

## Post-Launch Checklist

- [ ] `sync_irs_revocations.py` added to daily cron (e.g., 3:00 AM)
- [ ] `revocation_check_on_backfill_complete.py` integrated into monitoring
- [ ] API endpoint checks revoked_eins table and returns 410 Gone
- [ ] Frontend gracefully handles 410 errors (don't show, don't recommend)
- [ ] Monitoring dashboard shows revocation list age
- [ ] Alert webhook fires if revocation list age > 45 days
- [ ] Weekly spot-check: Query revoked_eins count (should be growing, ~1K/month)

---

## Legal/Compliance Notes

**Charitable Solicitation Law**:
- Showing a donor a revoked org could violate state registration laws
- Daanaa must not facilitate donation to revoked orgs
- Best practice: Don't show them at all (410 Gone)

**Privacy**:
- Revocation list is public (IRS)
- No private data exposed by flagging revoked orgs

**Fiduciary Duty**:
- Daanaa promises donors go to real, active nonprofits
- Stale revocation data breaks that promise

---

## Owned By

- **Data freshness**: Claude (automated monitoring + alert)
- **API safeguards**: Backend team (410 handler)
- **Frontend UX**: Frontend team (graceful degradation)
- **Manual backups**: Daanaa founder (weekly check)

