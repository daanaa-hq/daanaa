# Intent Signals + Event Discovery Integration (Phase 2)

**Date:** 2026-07-23
**Status:** Ready for local testing (feature-flagged, no deployment)
**Deployment:** Blocked until event-claiming system passes QA + combined end-to-end testing

---

## Overview

This document describes the integration of:
- **intent_layer.py** — Anonymous workflow signals (volunteer, give, learn, partner, claim)
- **event_discovery_engine.py** — Rolling-window event discovery from nonprofit websites
- **Admin review queue** — Candidates pending admin approval (no auto-publish)
- **Scheduler script** — Nightly discovery run with robots.txt compliance

All changes are **additive, feature-flagged, and local**. No public promotion, email, or deployment until:
1. Event-claiming system stabilizes and passes QA
2. Combined end-to-end QA suite passes
3. Founder approval obtained

---

## Architecture

### Intent Layer (`intent_layer.py`)

Stores anonymous workflow signals only. No PII, no wallet contents, no email/phone/IP.

**Schema:**
```
intent_signals:
  id          INTEGER PRIMARY KEY
  kind        TEXT (volunteer|give|learn|partner|claim)
  ein         TEXT (optional)
  event_id    INTEGER (optional)
  source      TEXT (event_preview|event_signup|hour_log|etc)
  stage       TEXT (expressed|matched|action_started|verified|completed|withdrawn)
  evidence    TEXT (JSON, source URL + extraction date only, never identity)
  created_at  TEXT
  updated_at  TEXT
```

**API:**
- `record_intent(db, kind, source, ein=None, event_id=None, evidence=None)` → signal_id
- `transition_intent(db, signal_id, stage)` → updates stage
- `summarize_intent(db, ein=None, event_id=None)` → count-only summary (no PII exposure)

**Integration Points:**

1. **Event preview viewed:** `record_intent(kind='volunteer', source='event_preview', event_id=...)`
2. **Confirmed signup:** `transition_intent(signal_id, 'action_started')`
3. **Approved hours:** `transition_intent(signal_id, 'verified')` or `'completed'`
4. **Nonprofit dashboard:** Shows aggregate counts only (threshold: minimum 5 signals)

---

### Event Discovery Engine (`event_discovery_engine.py`)

Discovers events from nonprofit websites with:
- Rolling 14–60 day window
- Deduplication (event_date + evidence hash UNIQUE constraint)
- Source URL + extraction date tracking
- Admin review queue (no auto-publish)

**Schema:**
```
event_discovery_queue:
  id              INTEGER PRIMARY KEY
  ein             TEXT
  source_url      TEXT
  source_hash     TEXT (evidence digest for dedup)
  title           TEXT
  event_date      TEXT
  evidence        TEXT (context snippet, up to 600 chars)
  status          TEXT (pending_review|approved|rejected|expired)
  last_checked_at TEXT
  reviewed_at     TEXT
```

**API:**
- `rolling_window(today=None)` → (start_date, end_date) 14–60 days ahead
- `fetch_source(url)` → HTML (with size limit, timeout, User-Agent)
- `extract_candidates(source_url, html, today=None)` → list of candidate events
- `ensure_queue(db)` → creates schema
- `queue_candidates(db, ein, candidates)` → INSERT OR IGNORE (dedup via UNIQUE)
- `search_scope(zip_code, city, state, event_type, date_from, date_to)` → SQL WHERE + params

**Scheduler:**
- `scripts/discovery_scheduler.sh` — bash wrapper for logging/retry
- `scripts/discovery_batch.py` — nightly processor
  - Fetches nonprofit websites
  - Runs discovery engine
  - Queues candidates for review (status=pending_review)
  - Logs all discoveries + failures

---

### Admin Endpoints

Feature-flagged behind `ENABLE_EVENT_DISCOVERY` and `ENABLE_INTENT_SIGNALS`.

#### Discovery Queue Management

**GET /api/admin/discovery/queue**
```
?status=pending_review&limit=50&offset=0

Response:
{
  "status": "pending_review",
  "candidates": [
    {
      "id": 1,
      "ein": "123456789",
      "source_url": "https://example.org/events",
      "title": "Community Clean-Up",
      "event_date": "2026-08-15",
      "evidence": "...",
      "status": "pending_review",
      "last_checked_at": "2026-07-23T13:00:00",
      "reviewed_at": null
    }
  ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

**POST /api/admin/discovery/queue/{id}/review**
```
{
  "decision": "approved",  // or "rejected", "deferred"
  "notes": "Verified with nonprofit"
}

Response:
{
  "success": true,
  "candidate_id": 1,
  "decision": "approved",
  "notes": "..."
}
```

When decision=`approved`:
- Candidate promoted to `volunteer_events` (status=`unconfirmed`, claim_status=`unconfirmed`)
- Event remains in preview mode (no signup, no hour logging)
- Nonprofit must claim/confirm to enable volunteer signup

#### Intent Signals Summary

**GET /api/admin/intent/summary**
```
?ein=123456789&event_id=2

Response:
{
  "ein": "123456789",
  "event_id": null,
  "signals": {
    "volunteer:expressed": 10,
    "volunteer:action_started": 7,
    "volunteer:verified": 3
  }
}
```

Aggregate counts only. No individual user data. Threshold enforcement in API layer: never expose counts < 5.

---

## Feature Flags

Both disabled by default. Enable only after event-claiming system stabilizes.

```bash
ENABLE_INTENT_SIGNALS=true    # Record workflow signals
ENABLE_EVENT_DISCOVERY=true   # Run discovery + populate review queue
```

**Set via environment:**
```bash
ENABLE_INTENT_SIGNALS=true python3 daanaa_api.py
```

---

## QA Results

All 15 integration tests pass ✓

### Test Coverage

1. ✓ **Source page to discovery queue** — HTML extraction + candidate queueing
2. ✓ **Date window: 14–60 days** — Correct rolling window calculation
3. ✓ **Search filters** — ZIP, city, state, event_type, date_from, date_to
4. ✓ **Deduplication** — UNIQUE(ein, source_url, event_date, source_hash)
5. ✓ **Preview creation** — Candidates stay unconfirmed until admin approves
6. ✓ **Anonymous intent signal** — No PII stored in intent_signals table
7. ✓ **Confirmed signup transition** — stage: expressed → action_started
8. ✓ **Approved hours transition** — stage: → verified or completed
9. ✓ **Aggregate counts (threshold 5)** — Counts only, no individual exposure
10. ✓ **Privacy checks** — No identity fields, no IP, no wallet data
11. ✓ **Source changes** — Handled via review queue (no silent rewrites)

**Privacy Check:** ✓ PASS
```
== privacy_check ==
GATE 8: Tier 2 Entity Firewall
  OK — all machine-checkable privacy invariants hold.
```

**Python Compilation:** ✓ PASS
- intent_layer.py
- event_discovery_engine.py
- daanaa_api.py (modified)
- scripts/discovery_batch.py

---

## Deployment Checklist

**Before local testing:**
```bash
python3 -m py_compile intent_layer.py event_discovery_engine.py daanaa_api.py scripts/discovery_batch.py
bash scripts/privacy_check.sh
source venv/bin/activate && python3 -m pytest tests/test_intent_discovery_integration.py -v
```

**Before production deployment** (BLOCKED until claiming system stable):
1. Event-claiming system passes its own QA
2. Combined end-to-end testing:
   - Event discovery → preview creation
   - Nonprofit claims event
   - Volunteer signs up → intent transition
   - Hours approved → intent verified
   - Dashboard shows aggregate counts (no PII)
   - Privacy check passes
   - No SQL injection in admin endpoints
3. Founder approval of QA report
4. No database migrations (additive only)
5. No email or public outreach enabled

**Production deployment steps** (after approval):
```bash
# Set feature flags to OFF initially
export ENABLE_INTENT_SIGNALS=false
export ENABLE_EVENT_DISCOVERY=false

# Deploy to droplet
bash scripts/ops/sync_droplet_api.sh

# Verify smoke test
curl https://daanaa.org/health

# Monitor logs
tail -f logs/discovery_$(date +%Y%m%d).log

# After 1 week (claiming system stable), enable features:
# ENABLE_INTENT_SIGNALS=true
# ENABLE_EVENT_DISCOVERY=true
# Then run combined QA again
```

---

## Integration Points (Remaining Work)

These hooks need to be added AFTER the claiming system is stable:

1. **Event preview viewed** (frontend)
   ```python
   from intent_layer import record_intent
   record_intent(db, kind='volunteer', source='event_preview', event_id=event_id)
   ```

2. **Volunteer signup confirmed**
   ```python
   intent_layer.transition_intent(db, signal_id, 'action_started')
   ```

3. **Hours approved by nonprofit**
   ```python
   intent_layer.transition_intent(db, signal_id, 'verified')
   ```

4. **Nonprofit dashboard aggregate display**
   ```python
   from intent_layer import summarize_intent
   summary = summarize_intent(db, ein=org_ein)
   # Show counts only if >= 5 (threshold enforcement)
   ```

5. **Scheduler setup (optional)**
   ```bash
   # Cron: nightly at 8pm
   0 20 * * * bash /home/akbar/meritgiving/scripts/discovery_scheduler.sh
   ```

---

## Files Changed

**New Files:**
- `intent_layer.py` (99 lines)
- `event_discovery_engine.py` (135 lines)
- `scripts/discovery_scheduler.sh` (executable)
- `scripts/discovery_batch.py` (executable)
- `tests/test_intent_discovery_integration.py` (380+ lines, 15 tests)
- `docs/INTENT_DISCOVERY_INTEGRATION_2026-07-23.md` (this file)

**Modified:**
- `daanaa_api.py` — Added:
  - Feature flags (ENABLE_INTENT_SIGNALS, ENABLE_EVENT_DISCOVERY)
  - Schema init functions (_init_intent_signals_table, _init_event_discovery_queue_table)
  - Admin endpoints (/api/admin/discovery/queue, /api/admin/intent/summary)
  - Imports (intent_layer, event_discovery_engine)

---

## Stewardship Alignment

✓ **P1 (Mission before growth):** Event discovery + intent signals inform better giving decisions without external pressure
✓ **P2 (Privacy is structural):** No PII, no wallet exposure, no tracking, no email until nonprofit confirms
✓ **P3 (Trust signals evidence-based):** All candidates include source URL + extraction date; admin reviews before promotion
✓ **P4 (Small orgs fairness):** Discovery treats all organizations equally (no size bias); small events discoverable
✓ **P5 (No weaponized transparency):** Counts only shown to nonprofits (no shame framing, no negative exposure)
✓ **P7 (Independence protected):** Candidates promote algorithmically; no curation, no partner influence
✓ **P8 (No fund control):** Daanaa records intent in wallet; donations flow direct to org
✓ **P10 (AI is a tool):** Discovery is AI-assisted but human-reviewed before promotion

---

## Known Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Silent data corruption on discovery | Write dedup via UNIQUE constraint; admin approval required for promotion |
| Performance: scanning 400K websites | Batch limits (1000/run); nightly schedule; skip recently checked |
| Privacy leak: email in evidence | Code review enforces: evidence = source URL + context only, never identity |
| Nonprofit complaint: "I never gave permission" | Admin review queue: nonprofit must claim/confirm to enable signup |
| Unconfirmed events showing in search | Frontend filters: only confirmed events (status='active') appear in public search |
| Mass discovery spam | Dedup by source URL + event date; admin review queue acts as gate |

---

## Success Criteria

✓ **Additive:** No changes to existing scoring, wallet, nonprofit ranking
✓ **Feature-flagged:** Both disabled by default, can be toggled independently
✓ **Local:** All code in repo, ready to deploy when claiming system stable
✓ **Tested:** 15/15 integration tests pass, privacy check passes
✓ **Documented:** This file + handoff doc + code comments explain design
✓ **Safe to ship:** No database migrations, no breaking changes, fail closed on error

---

## Next Steps (After Claiming System Stable)

1. Run combined end-to-end QA suite
2. Integrate hooks (event_preview, signup, hour_approval)
3. Get founder approval of QA report
4. Deploy with feature flags ON
5. Monitor logs + metrics for 1 week
6. Proceed to next phase (wallet "Add to My Impact" button, etc.)

---

**Prepared by:** Claude Code
**Reviewed by:** User (pending)
**Status:** Ready for review and local testing
