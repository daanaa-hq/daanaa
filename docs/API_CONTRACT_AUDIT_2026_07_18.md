# API Contract & Performance Audit — 2026-07-18

**Trigger:** The 2026-07-05 outage was caused by droplet_api.py serving stale SPA while daanaa_api.py had moved on. Contract drift between the two "canonical" backends is the highest-risk failure mode.

**Goal:** Audit both APIs for route/response consistency, validate SLO compliance, identify performance bottlenecks before they hit users.

---

## Part 1: API Contract Audit

### Endpoints to Validate (Live Site: daanaa.org)

**Search/Organizations:**
- `GET /api/organizations` — query, filters, pagination, sort
- `GET /api/organizations/<ein>` — org detail endpoint
- `GET /api/organizations/<ein>/similar` — similar orgs

**Peer/Financial Context:**
- `GET /api/peer-group/<ein>` — peer context + benchmarking
- `GET /api/health` — health check
- `GET /api/stats` — aggregate stats

**Nonprofit (Claimed):**
- `POST /api/claim/start` — initiate claim
- `PATCH /api/claim/profile` — update profile (we just fixed the response here)
- `GET /api/nonprofit/dashboard/<claim_token>` — claimed org dashboard (legacy route check)

**Validation checks:**

| Route | Droplet Response | Home Response | Match? | Field Variance OK? |
|-------|---|---|---|---|
| GET /api/organizations?q=health | Check status code, pagination envelope, field names | Should be identical | TBD | TBD |
| GET /api/organizations/<ein> | Should include: EIN, organization_name, STATE, mission, donate_url, merit_score_v5, etc. | Should be identical | TBD | Cached values drift OK; live changes require precompute |
| POST /api/claim/profile | Response: {status: "updated", message: "Saved..."} | Home is canonical; should match | TBD | Just updated; must match exactly |

### Contract Test Strategy

**Approach:** Call the same route on both droplet (live.daanaa.org) and home (localhost:5000), compare responses.

**Setup:**
```python
import requests

# Routes to test (read-only, safe)
ROUTES = [
    '/api/organizations?q=food&per_page=5',
    '/api/organizations?q=health&state=CA&per_page=5',
    '/api/organizations/261234567',  # Red Cross
    '/api/organizations/251000090',   # Another random org
    '/api/health',
    '/api/stats',
]

DROPLET = 'https://daanaa.org'
HOME = 'http://localhost:5000'

for route in ROUTES:
    droplet_resp = requests.get(DROPLET + route, timeout=10).json()
    home_resp = requests.get(HOME + route, timeout=10).json()
    
    # Compare structure, field names, types
    check_contract(droplet_resp, home_resp, route)
```

**What to check:**
1. **Status codes:** both 200? both same?
2. **Response envelope:** both have `{organizations: [...]}` or `{data: ...}`?
3. **Field names:** does droplet have fields home doesn't? vice versa?
4. **Data types:** is EIN a string in both? is merit_score a number in both?
5. **Content freshness:** is data stale on droplet (>24h old)? acceptable?

**Red flags:**
- ❌ Droplet missing a field that home has (user sees incomplete data)
- ❌ Droplet has a field home doesn't (undocumented feature, risk)
- ❌ Field is different type (string vs int; breaks client parsing)
- ❌ Status codes differ (one 200, one 500)
- ⚠️ Droplet data is >7 days stale (acceptable but flag for awareness)

---

## Part 2: Search Performance Audit

### SLO Status

**Target:** <3s for 95th percentile (from SLO alert 2026-07-18)  
**Current:** ~2.6-4.6s observed at deployment (post memory-leak fix)

**Test plan:**
1. Run 50 queries from the golden set (both common words and specific searches)
2. Measure latency for each (wall-clock time, not server-reported)
3. Record p50, p95, p99 latencies
4. Identify slow queries (>3s) and their patterns

**Queries to test:**
```
- Common words: "health", "food", "children", "education"
- Org names: "Red Cross", "Salvation Army", "YMCA"
- Locations: "CA", "New York, NY", "90210", "Los Angeles, CA"
- Filters: state + cause, state + revenue band, archetype + band
- Sorting: name ASC/DESC, revenue DESC/ASC
- Pagination: page 1, page 5, page 10
```

**Expected results:**
- p50: 0.8-1.5s (hot cache, no network jitter)
- p95: <3s (SLO target; some cache misses, network variance)
- p99: <5s (worst case: cold cache on high-cardinality join)

**If >3s observed:**
- Check if it's a single slow query type (e.g., all location queries)
- Measure droplet vs home response time separately (to isolate network vs compute)
- Profile database query plan (does FTS use the right index? Does join cardinality explode?)

---

## Part 3: Data Quality Spot-Check

### Sample 20 random orgs, verify:

1. **Website/donate URL reachability** — do they exist and return 2xx?
2. **Mission statement** — is it reasonable (not garbage, not suspiciously AI-generated)?
3. **Peer context consistency** — is the financial health signal reasonable for the org's size/revenue?
4. **Claim status accuracy** — if org is marked "claimed", does org_claims table confirm?

**Red flags:**
- ❌ Website URL returns 404/403 (broken link)
- ❌ Mission is obviously AI-generated gibberish
- ❌ Org with $0 revenue marked "HEALTHY" (data integrity issue)
- ⚠️ Org hasn't been scored in >30 days (stale data)

---

## Part 4: Ops Reliability Checklist

**Daemon health:**
- [ ] SLO alert watchdog is running? (daanaa_watchdog.py)
- [ ] Archive recovery daemon is running? (archive_recovery_daemon.sh)
- [ ] Link verification daemon running? (link verification cron)
- [ ] Precompute deploy cron scheduled for tonight? (02:30 UTC / 20:30 CDT)

**Backups:**
- [ ] Latest backup exists? (daanaa_backup.sh)
- [ ] Backup size is reasonable (>5GB, <15GB)?
- [ ] Last restore drill: 2026-07-18 (recent)

**Monitoring:**
- [ ] Plausible analytics active on daanaa.org?
- [ ] Search latency probe running on SLO alert?
- [ ] Droplet disk space <80% used?

---

## Execution Plan

**Phase 1 (now):**
1. Run API contract test against live droplet + home (10 min)
2. Log any mismatches to a report

**Phase 2 (now):**
3. Run 50-query performance test, record latencies (15 min)
4. Compare p95 to 3s SLO target

**Phase 3 (now):**
5. Spot-check 20 random orgs from API response (10 min)

**Phase 4 (now):**
6. Verify daemon health via ps/logs (5 min)

**Reporting:** Summary of findings + action items if any SLO breach or data integrity issue found.

---

## Success Criteria

- ✅ **Contract:** No unexpected field mismatches; all routes respond 200 on both backends
- ✅ **Performance:** p95 latency <3s on golden set queries
- ✅ **Data quality:** Spot-checked orgs are reasonable (websites reachable, missions sensible, financial signals coherent)
- ✅ **Ops:** All daemons running; backups recent; monitoring active

---

## Risk Assessment

**This audit is read-only:** No changes to production data or code. Safe to run anytime.  
**Expected outcome:** Either "all green" (builds confidence) or "found X issues" (actionable fixes).  
**Blockers:** None. Can run in parallel with other work.

---

