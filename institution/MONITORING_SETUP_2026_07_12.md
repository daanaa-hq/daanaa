# External Uptime Monitoring Setup (T4)

**Authority:** EXECUTION_HANDOFF_2026_07_12.md  
**Purpose:** Close the INC-001 gap — watchdog that checks real pages, not health pings.  
**Status:** Configuration documented; manual setup required (UptimeRobot free tier).

## The INC-001 lesson

On 2026-07-05, /health returned 200 while every actual page returned 500 for 11 hours. The internal watchdog only checked /health. The lesson: **external monitoring must verify real user-facing content, not synthetic health checks.**

## Three monitors to set up (UptimeRobot free tier)

Login to uptimerobot.com with the founder email (akbar.khowaja@gmail.com).

### Monitor 1: Homepage renders

- **URL:** `https://daanaa.org/`
- **Check type:** Keyword (HTTP)
- **Expected keyword:** `doctype html` (only present when the SPA shell is intact; missing = page 500)
- **Interval:** 5 minutes
- **Alert on down:** Yes → email founder

**Why this closes INC-001:** A 500 error won't render the doctype. An SPA fallback crash won't either. This catches the exact failure mode.

### Monitor 2: Core API availability

- **URL:** `https://daanaa.org/api/organizations?limit=1`
- **Check type:** HTTP status
- **Expected:** 200 OK
- **Interval:** 5 minutes
- **Alert:** Yes → email

**Why:** Confirms the droplet's query API is reachable.

### Monitor 3: Search working

- **URL:** `https://daanaa.org/api/search?q=food`
- **Check type:** Keyword (HTTP)
- **Expected keyword:** `"mode"` (search response always includes a mode field)
- **Interval:** 5 minutes
- **Alert:** Yes → email

**Why:** Confirms the search index is live and responding.

## Verification

1. Create all three monitors in UptimeRobot
2. Use the "Test Notification" button on each to verify email delivery to the founder
3. Wait for one check cycle (~5 minutes) and confirm status shows "Up"
4. Document the UptimeRobot monitor IDs and dashboard link in DECISION_LOG.md

## What gets logged

When T4 is complete, add to DECISION_LOG.md:
```
- Identifier: T4-2026-07-12
- Date: [today]
- Monitors created: 3 (homepage/doctype, API 200, search keyword)
- Alert channel: email to founder
- Detection latency: 5-minute interval
- Why: Closes INC-001 gap (health ping ≠ real-page check)
```

## Next: T7 & T8 (research experiments)

Once T4 is verified, the research work begins:
- T7: sqlite-vec benchmark (semantic search on droplet)
- T8: Litestream continuous replication (backup to R2)

Both run on home server, no droplet dependency. Both log hypotheses + decision rules to REGISTRY.md.
