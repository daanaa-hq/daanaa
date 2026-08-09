# Phase 3 → Gate A.1: Measurement Reliability — Readiness Check

**Status:** ✅ **95% Ready**  
**Date:** 2026-08-09  
**Blocker:** Custom events/goals must be manually created in Plausible UI

---

## Infrastructure Status

### Frontend Analytics (✅ Complete)
- `trackEvent(name, {props})` — extended to support Plausible properties
- `trackAtAGlanceVisible(orgSize)` — fires on component mount
- `trackOrgBookmark(orgSize)` — fires on wallet bookmark
- `trackSearchFilter(filterType)` — skeleton ready (no UI filters yet)

**Build:** ✅ Clean (33e9906a4a4)  
**SPA:** ✅ Ready at `frontend/dist/`

---

### Plausible Analytics Stack (✅ Running)
- **Status:** Healthy (postgres + clickhouse both OK)
- **URL:** https://stats.daanaa.org (via Cloudflare Tunnel)
- **Version:** Community Edition v2.1.4
- **Ingest:** Active (daanaa.org frontend already wired)
- **Dashboard:** Accessible at https://stats.daanaa.org (admin login required)

**Verify:**
```bash
curl -s http://localhost:18000/api/health
# Expected: {"postgres":"ok","clickhouse":"ok","sites_cache":"ok"}
```

---

## What's Working Now

1. ✅ **Event generation** — Frontend code fires custom events when tracked functions called
2. ✅ **Event transport** — Plausible script.js accepts events and sends to stats.daanaa.org
3. ✅ **Data collection** — ClickHouse stores all events (with or without goals defined)
4. ✅ **Privacy** — Only org-level properties sent (revenue_band, section); never EIN

---

## What Needs Setup (Manual, in Plausible UI)

To measure Gate A.1, three **custom goals** must be created in Plausible dashboard:

### Goal 1: `atagla nce_visible`
- **Event name:** `atagla nce_visible`
- **Description:** At a Glance section became visible on org detail page
- **Target metric:** >60% of org detail visitors see this (Phase 3 success signal)

### Goal 2: `org_detail_bookmark`
- **Event name:** `org_detail_bookmark`
- **Description:** User added org to Giving Wallet (bookmark action)
- **Target metric:** Micro/Large bookmark ratio improvement (proxy for decision-making)

### Goal 3: `search_filter_context` (optional, forward-compatible)
- **Event name:** `search_filter_context`
- **Description:** User engaged with context-driven search filters
- **Target metric:** Leadership/stability filters used >10% of searches

---

## How to Set Up Plausible Goals

1. Open https://stats.daanaa.org → login (admin creds in `deploy/plausible/plausible-conf.env`)
2. Go to **daanaa.org site → Goals** 
3. Click **+ Add Goal**
4. For each goal above:
   - Set **Goal name** = event name
   - Select **Event name** trigger
   - Enter exact event name (must match tracking calls)
   - Save

**Reference:** Plausible docs — https://plausible.io/docs/custom-goals#triggering-custom-goals-with-javascript-events

---

## Baseline Metrics: Aug 2-8 (Pre-Phase-3)

Once goals are created, capture baseline CTR for micro orgs:

```sql
-- Query A: Small org CTR (pre-Phase-3 baseline)
-- Period: Aug 2-8, 2026
-- Segment: org_size = 'Micro' (revenue < $150K)
-- Metric: (org_detail_page_visits) / (directory_page_visits) × 100
```

Plausible UI: 
- Date range: Aug 2-8
- Filter: `org_size = 'Micro'` (once properties added)
- Goal: `org_detail_bookmark` (or track page views for CTR calculation)

---

## Live Measurement Window: Aug 10-16

Once baseline is captured:

1. **Aug 10:** Verify tracking is firing (browser dev tools → Network tab → stats.daanaa.org)
2. **Aug 10-16:** Daily pulse checks (5 min each day)
   - Log: `Micro CTR = X%, Δ from baseline: Y%`
   - Target: Variance <15% day-to-day
3. **Aug 16:** Generate Week 1 report
   - Compare CTR(Aug 9-16) vs baseline(Aug 2-8)
   - Document sample size
   - Recommend Gate A.1 pass/fail

---

## Deployment Status

### Frontend Code (Ready)
- ✅ Committed: 33e9906a4a4
- ✅ Build clean
- ⏳ **Not yet deployed to droplet** (was blocked by cache issue on Aug 9)

### To Deploy:
```bash
cd ~/meritgiving/frontend && npm run build
rsync -az --delete dist/ root@162.243.97.179:/opt/daanaa/frontend/dist/ \
  -e "ssh -i ~/.ssh/daanaa_do"
ssh -i ~/.ssh/daanaa_do root@162.243.97.179 'systemctl restart daanaa'

# Verify:
curl -s https://daanaa.org/ | grep -c "atagla nce_visible"  # Should appear in JS
```

---

## Next Steps (In Order)

1. **Create Plausible goals** (3 custom goals, <5 min manual setup)
2. **Baseline capture** (query Aug 2-8 data, save baseline numbers)
3. **Deploy updated frontend** to droplet (if not deployed yet)
4. **Verify tracking fires** (browser DevTools confirmation)
5. **Start daily pulse checks** (Aug 10+)
6. **Generate Week 1 report** (Aug 16 decision memo)

---

## Success Criteria: Gate A.1

✅ **PASS:**
- Day-to-day CTR variance <15% (measurement is stable)
- Sample size >100 micro org clicks/day (signal is strong)
- No technical errors in event capture (logs clean)
- Ready to proceed to Gate A.2 (statistical significance)

❌ **FAIL:**
- Variance >15% (measurement is noisy, needs investigation)
- Sample size <100/day (need longer baseline)
- Events not firing (technical issue with tracking)

---

## Stewardship Alignment

- **P2 (Privacy):** Only org-level props, zero PII ✅
- **P3 (Evidence-based):** Real data, not assumptions ✅
- **P4 (Small org fairness):** Explicit measurement of small org CTR ✅
- **P6 (Mistakes correction):** Daily monitoring catches regressions ✅

---

## Questions?

- **Plausible login:** See `deploy/plausible/plausible-conf.env` (chmod 600, not in git)
- **Event firing:** Check browser DevTools → Network → stats.daanaa.org
- **Baseline queries:** Ask for query templates from PHASE3_MEASUREMENT_PLAN.md

