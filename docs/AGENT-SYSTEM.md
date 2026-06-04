# Daanaa Autonomous Agent System

**Date:** 2026-06-04  
**Stewardship Principles:** #3 (evidence-based), #6 (correct mistakes), #9 (explainable), #10 (AI as tool)

## Overview

Daanaa runs two autonomous agents that detect event-driven search surges (e.g., "hurricane") and intelligently boost relevant nonprofits in search results, even when the org name doesn't match the query.

**Why:** During crises (hurricanes, economic downturns), users search for "event name" but actually want nonprofits serving related causes (housing, disaster relief, food, employment). Semantic search alone struggles because nonprofit names don't include "hurricane." Event-driven boosting solves this.

**How:** Agents run on a schedule, log every action, and remain fully overrideable by humans.

---

## System Architecture

### Agent 1: Surge Monitor (`scripts/agent_surge_monitor.py`)

**Schedule:** Every 10 minutes, 8am–10pm (business hours)

**Input:** Search event logs (from `/api/log/search`)

**Process:**
1. Count queries in the past hour
2. Compare to 24-hour baseline
3. Detect spikes (3x+ baseline)
4. Classify event type (hurricane → disaster, unemployment → employment, etc.)
5. Find relevant orgs by cause_tags
6. Create boost records with 48-hour TTL

**Output:**
- Inserts into `surge_boosts` table (ein, relevance_score, event_type, expires_at)
- Logs every action to `agent_actions` table for audit trail

**Evidence-based:** Only boosts orgs that actually match the detected event type via semantic cause_tags.

### Agent 2: Outcome Analyzer (`scripts/agent_outcome_analyzer.py`)

**Schedule:** Nightly at 2am

**Input:** Click/donation logs from `search_events`

**Process:**
1. For each active or expired boost, count clicks and donations
2. Measure effectiveness (did users actually engage with boosted orgs?)
3. Update `surge_boosts` with outcome metrics
4. Generate human-readable report

**Output:**
- Updates boost records with `clicks` and `donations` fields
- Prints summary report of what worked/didn't work

**Learning:** Future improvements can weight boosts based on historical effectiveness.

---

## Data Tables

### `search_events`
```sql
id, query, timestamp, clicked_ein, donated
```
Populated by frontend calling `/api/log/search`. Tracks user intent and outcomes.

### `surge_detections`
```sql
id, query, event_type, surge_ratio, baseline_count, surge_count, 
detected_at, confidence
```
Records every detected surge: when, what event type, confidence level.

### `surge_boosts`
```sql
id, surge_id, ein, relevance_score, relevance_reason, boosted_at, 
expires_at, clicks, donations, status, overridden_at, override_reason
```
The boost action log. `status` ∈ [active, expired, overridden]. Fully auditable.

### `agent_actions`
```sql
id, action_type, action_data (JSON), reasoning, timestamp, status
```
Complete audit trail of every agent decision: surge detected, boosts created, overrides.

---

## Human Oversight (Principle #10)

### Admin Endpoints

**View active boosts:**
```bash
curl http://localhost:5000/api/admin/surge-boosts \
  -H "X-Admin-Key: $DAANAA_ADMIN_KEY"
```
Returns: boost ID, EIN, query, event type, clicks, donations, TTL.

**Override a boost** (pause it immediately):
```bash
curl -X POST http://localhost:5000/api/admin/surge-boosts/123/override \
  -H "X-Admin-Key: $DAANAA_ADMIN_KEY" \
  -d '{"reason":"Wrong event classification"}'
```
Sets `status='overridden'`, logs reason, removes from active set.

### Rules for Human Intervention

1. **Pause boosts that harm users:** If outcome report shows 0 clicks, override.
2. **Correct event misclassifications:** "hurricane" might be misclassified as "disaster"; override and re-run agents.
3. **Manual boosts during crisis:** During an actual event, you can manually insert boosts in `surge_boosts` table (create surge_id=0 entries).

---

## Principles Alignment

| Principle | How Implemented |
|-----------|-----------------|
| #3 Evidence-based | Boosts only orgs with matching cause_tags; all decisions logged |
| #6 Correct mistakes | Admin override endpoint; boosts expire (48h TTL); daily outcome analysis |
| #9 Explainable | Every action logged in `agent_actions`; reasoning stored; audit trail visible |
| #10 AI as tool | Agents have no autonomous commit power; all results in override-ready tables; human runs final decision |

---

## Testing

**Simulate a surge:**
```sql
-- Insert 50 test searches for "hurricane"
INSERT INTO search_events (query) 
SELECT 'hurricane' FROM (SELECT 1 UNION SELECT 2 ... UNION SELECT 50);

-- Run agent (will detect surge)
python3 scripts/agent_surge_monitor.py

-- Check boosts created
SELECT * FROM surge_boosts ORDER BY boosted_at DESC;

-- View admin report
curl http://localhost:5000/api/admin/surge-boosts \
  -H "X-Admin-Key: $DAANAA_ADMIN_KEY"
```

---

## Event Classification Rules

Defined in `EVENT_RULES` dict:
- `hurricane|tornado|cyclone` → disaster
- `homeless|housing crisis` → housing
- `hunger|food bank` → food
- `election|voting` → civic
- `layoff|unemployment` → employment
- `mental health|crisis` → mental_health
- `covid|pandemic` → health

Can be extended. Update `scripts/agent_surge_monitor.py` and restart.

---

## Logs

- **Agent surge log:** `logs/agent_surge.log` (every 10 min)
- **Agent outcome log:** `logs/agent_outcome.log` (nightly)
- **API error log:** `logs/daanaa_api.log` (real-time)

Example log entry:
```
[2026-06-04 13:45:22] surge_detected: query='hurricane relief' ratio=4.2x event_type='disaster'
[2026-06-04 13:45:25] boosts_created: surge_id=42 event_type='disaster' org_count=18
```

---

## Future Work

1. **Learning weights:** Adjust future boosts based on outcome metrics (clicks/donations).
2. **Regional filters:** Boost only orgs in affected geographic regions.
3. **Multi-event clusters:** Detect complex events ("hurricane + homelessness").
4. **User feedback:** Add feedback button "was this helpful?" to measure UX impact.

---

## Accountability

Human responsible for agent behavior: **Akbar Khowaja** (founder).

All agent outputs are reviewable, correctable, and logged. No decisions are final without human sign-off or explicit override capability.

Last reviewed: 2026-06-04
