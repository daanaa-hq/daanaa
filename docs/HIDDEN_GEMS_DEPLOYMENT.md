# Hidden Gems Feature — Deployment Guide

**Status:** ✓ Feature complete and ready for deployment  
**Scope:** Lands users on 33,971 small, financially healthy organizations instead of sorting by size  
**Performance:** Zero impact — served as static weekly files, not live queries  

---

## What Changed

### Backend (droplet_api.py)
- **Static gem serving** (lines 369–380): When `hidden_gem` is the *only* filter (no search, categories, state, revenue range, or other flags), serves precomputed JSON from `DATA_DIR/browse/hidden_gems/ALL_{page}.json.gz` instead of querying the database.
- **`order` parameter** (line 360): Controls sort direction (asc/desc) via `_order_clause()` helper, with defaults (name→ASC, revenue/merit_score→DESC).
- **`tier` parameter** (line 361): Filters by visibility tier (Beacon/Torch/Candle/Spark) via `_TIER_DB_VALUES` map; works with any other filter combination.

### Frontend (Directory.tsx)
- **State variables**: `hiddenGem` (on by default unless a filter is active), `needsSupport`, `visTier`, `sortOrder` — all wired to query params and the API call.
- **Discovery toggles** (lines 523–548): Hidden gems (tan color) and Needs support (purple) in the collapsed filters row.
- **UI consolidation**: 
  - Visibility tier dropdown next to Revenue and State (lines 591–617).
  - "Has a website" button integrated into the same row (lines 574–590).
  - Sort direction toggle (asc/desc icon, lines 858–869) next to the Sort dropdown.
- **Gems framing** (lines 752–759): When hidden gems are active, shows "Small, overlooked organizations · a fresh set each week" + a "See all 1.8M →" button to clear the gem filter and browse the full directory.
- **H1** (line 472): "Explore Causes & Organizations" (unchanged from current).

### Data (precompute_hidden_gems.py)
- **Weekly rotation**: Deterministic shuffle via ISO week seed (`2026-W25`, etc.) — every gem gets equal odds of a front-page slot, order resets every Monday.
- **Precomputed output**: `precompute_output/browse/hidden_gems/ALL_1.json.gz` through `ALL_1598.json.gz` (33,971 gems across ~1,600 pages).
- **Cron** (already active): Runs Monday 2 AM UTC; regenerates gems and rsyncs to droplet.

---

## Deployment Steps (Gated)

### Pre-flight Checklist
```bash
# Verify all components are in place
bash scripts/verify_hidden_gems.sh
```

Expected output:
- ✓ 33,971 gems in registry_enriched
- ✓ Precompute script exists (last run: <date>)
- ✓ ~1,600 gem pages in precompute_output
- ✓ Weekly cron configured
- ✓ droplet_api.py has gems logic
- ✓ Directory.tsx UI complete
- ✓ API params ready

### Step 1: Patch Droplet search.db

The droplet's `/data/precompute/v1/search.db` has `is_hidden_gem = 0` for all rows (stale data from before gem computation). Update it so filtering by gems with other conditions (e.g., `?hidden_gem=1&ntee=A`) works.

```bash
bash scripts/deploy_hidden_gems.sh
```

This script will:
1. Export 33,971 gem EINs from home server
2. Generate a batched SQL patch
3. Upload and apply the patch to droplet
4. Verify counts match

**Expected output:**
```
Home server gems: 33971
Droplet gems: 33971
✓ Counts match!
```

### Step 2: Rebuild Frontend & Deploy

```bash
# From project root
cd frontend
npm run build
cd ..

# Deploy to droplet
rsync -avz frontend/dist/ root@162.243.97.179:/opt/daanaa/frontend/dist/

# Restart API (if needed)
ssh root@162.243.97.179 "systemctl restart gunicorn"
```

### Step 3: Test

#### Local (dev server)
```bash
# Start the local API (if running against local DB)
cd frontend && npm run dev
# Visit http://localhost:5173/directory
# Verify:
#   - Default landing shows hidden gems
#   - "See all 1.8M" button appears below count
#   - Can toggle off and see full directory
```

#### Against Droplet
```bash
# Test API directly
curl 'https://daanaa.org/api/organizations?hidden_gem=1&page=1'
# Should return ~33,971 total, with orgs in is_hidden_gem set

# Test combined filters (exercises the live query path)
curl 'https://daanaa.org/api/organizations?hidden_gem=1&ntee=A&page=1'
# Should return gems in Arts category (from search.db)

# Test sort direction
curl 'https://daanaa.org/api/organizations?sort=organization_name&order=desc&page=1'
# Should sort Z→A (by name descending)

# Test visibility tier
curl 'https://daanaa.org/api/organizations?tier=spark&page=1'
# Should return only Spark-tier orgs
```

#### UI
1. Visit https://daanaa.org/directory
   - ✓ Lands on hidden gems (not revenue-sorted)
   - ✓ Count shows "hidden gems" label
   - ✓ "Small, overlooked organizations · a fresh set each week" text appears
   - ✓ "See all 1.8M →" button present
2. Click "See all 1.8M"
   - ✓ Clears `hidden_gem` filter
   - ✓ Shows full directory (1.8M orgs)
   - ✓ Sort dropdown reappears
3. Toggle "Hidden gems" off and back on
   - ✓ Navigates between gems and full browse
4. Apply additional filter (e.g., "Needs support")
   - ✓ Gems + filter combination works
   - ✓ Uses live query path (droplet search.db)
5. Check mobile responsiveness
   - ✓ Toggles visible on small screens

---

## Rollback

If issues arise:

1. **Revert frontend**: `git checkout frontend/dist`
2. **Revert droplet API**: `git checkout scripts/droplet_api.py` + redeploy
3. **Restore gems flag**: Use `scripts/restore_gems_flag_backup.sql` (generated during deploy_hidden_gems.sh if needed)

---

## Weekly Monitoring

The cron job runs **every Monday at 2 AM UTC**. To verify:

```bash
# Check the cron log
tail -100 /var/log/syslog | grep "precompute_hidden_gems"

# Manually force a run
cd /home/akbar/meritgiving && \
  source venv/bin/activate && \
  python3 scripts/precompute_hidden_gems.py

# Check rsync log (cron output goes to /dev/null; add logging if needed)
ls -lah precompute_output/browse/hidden_gems/ALL_1.json.gz
# Should show "Mon HH:MM" from the latest run
```

---

## Architecture Notes

### Why Static Files?
- **Speed**: Single file read (gzipped JSON), no database query.
- **Determinism**: Weekly shuffle is reproducible (same seed per ISO week).
- **Fairness**: Every gem gets equal odds of landing on the first page (P4 — small orgs deserve fairness).

### Why Not Cache the 1.8M Directory?
- Filtering (by category, state, revenue) requires live queries; static files can't support every filter combination efficiently.
- Only the **gems default** is static because it's the default landing view (zero filters).

### Data Filter Chain
```
is_hidden_gem = 1          ← Marked in nightly scoring pipeline
AND deductibility = 1      ← Only tax-deductible giving
AND org_status = 'active'  ← Not revoked
```

Same gate as the rest of the browse cache — fail closed on deductibility.

---

## Known Limitations

1. **Search query clears gems**: Typing in the search bar switches off the gems landing (`effectiveHiddenGem = hiddenGem && !debouncedQuery`). This is intentional — users searching by name don't want gems shuffled.
2. **Mobile sort toggle hidden**: Sort direction button is hidden on small screens (responsive design).
3. **Droplet search.db rebuild needed**: The weekly cron only syncs static files; if search.db is rebuilt, the gem flags will reset (mitigated by next cron run, but temporary gap if someone filters gems + category on that day).

---

## Files Changed

| File | Change |
|------|--------|
| `scripts/droplet_api.py` | Lines 357–394: hidden_gem/order/tier params + static gem serving |
| `frontend/src/pages/Directory.tsx` | Lines 191–203: new state variables; 279–296: API params; 523–548: toggles; 574–617: dropdowns; 750–759: gems framing |
| `frontend/src/data/api.ts` | Lines 191–235: API params already included (no change needed) |
| `scripts/precompute_hidden_gems.py` | No change — already committed (commit 91b488b) |
| `scripts/deploy_hidden_gems.sh` | NEW — Patch droplet search.db |
| `scripts/verify_hidden_gems.sh` | NEW — Status check before deployment |
| `.crontab` | Weekly Monday 2 AM: regenerate gems + rsync to droplet |

---

## Questions?

- **Gem count lower than expected?** Check the filter: `is_hidden_gem=1 AND deductibility=1 AND org_status='active'`.
- **Static files missing on droplet?** Check cron job; manually run `scripts/deploy_hidden_gems.sh` to sync.
- **Sort order wrong?** Verify `order` param is passed (defaults: name→ASC, revenue→DESC).
- **Tier filter returns no results?** Check `_TIER_DB_VALUES` mapping in droplet_api.py.

---

**Prepared by:** Claude Code  
**Date:** 2026-06-20  
**Status:** Ready for approval & deployment
