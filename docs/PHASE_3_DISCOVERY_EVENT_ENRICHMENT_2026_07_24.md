# Phase 3: Nonprofit Website Discovery & Event Enrichment

**Date:** 2026-07-24  
**Status:** LAUNCHING IMMEDIATELY  
**Scope:** Find nonprofit websites, extract volunteer events, enrich platform  

---

## Objective

Use server hardware (23GB RAM available, AMD Ryzen R9 7900) to:
1. **Find websites** for nonprofits where we have no URL or bad URLs
2. **Extract lessons** on what makes discovery fail (improve algorithm)
3. **Discover volunteer events** (parse nonprofit websites for event data)
4. **Add events to platform** (feed into volunteer_hours_events_impact table)

---

## Discovery Pipeline Architecture

```
Phase 3 Discovery Pipeline
├── Stage 1: Identify Gaps
│   ├── SELECT orgs WHERE website IS NULL OR website_status = 'broken'
│   ├── Categorize by: size, NTEE, state, last_checked
│   └── Priority queue: high-impact orgs first (by peer group)
│
├── Stage 2: Website Discovery (8 parallel workers)
│   ├── Worker 1-4: Google Search (org name + "nonprofit")
│   ├── Worker 5-6: Charity Navigator lookup
│   ├── Worker 7-8: ProPublica API (leadership pages often have contact info)
│   └── Fallback: LinkedIn org pages, state nonprofit registry
│
├── Stage 3: Event Extraction (8 parallel workers)
│   ├── Worker 1-2: Parse events.org, eventbrite.com
│   ├── Worker 3-4: Parse nonprofit website event pages
│   ├── Worker 5-6: Parse volunteer.gov and idealist.org
│   ├── Worker 7-8: Parse social media (LinkedIn, Facebook events)
│   └── Validation: Deduplicate, verify date formats, confirm nonprofit match
│
├── Stage 4: Learning Extraction
│   ├── What succeeded? (org size, NTEE, state patterns)
│   ├── What failed? (error types, retry strategies)
│   └── Algorithm improvement: Update scoring for next batch
│
└── Stage 5: Import to Platform
    ├── INSERT INTO volunteer_hours_events_impact
    ├── UPDATE registry_enriched.website + website_status
    └── Log to audit_log: 'event_discovered', 'website_recovered'
```

---

## Expected Outcomes

### Coverage Improvements
- Current: ~3,680 live donation links (Phase 0 complete)
- Target Phase 3: +1,000-2,000 website URLs recovered/discovered
- Target: +100-500 new volunteer events discovered

### Lessons Learned
- Document what search strategies work best by NTEE
- Identify state/region patterns (some states better coverage)
- Build better website validation heuristics

### Platform Enrichment
- `volunteer_hours_events_impact` grows from current count to 2x+
- `registry_enriched.website` improves coverage from ~80% to ~85%+
- Audit log shows all discovery attempts + success rates

---

## Implementation: 8-Worker Discovery Engine

### Worker 1-4: Google Search (with Selenium/BeautifulSoup)
```python
# Find org website via Google Search
# Google: "{org_name} {org_city} nonprofit" → extract top link
# Validate: check for 501c3 language, contact form, donation link
# Store: website URL, domain, status (found/404/timeout)
```

### Worker 5-6: Charity Navigator Lookup
```python
# Query Charity Navigator API for org_id
# Extract: website, contact, leadership
# Cross-reference: EIN → org match confirmation
```

### Worker 7-8: Event Parsing (BeautifulSoup)
```python
# Parse common event patterns from websites:
# - "Volunteer" pages (/volunteer, /get-involved)
# - Event calendars (calendar.php, events.php)
# - Facebook event URLs (facebook.com/[org]/events)
# - Eventbrite.com event listings
# Extract: event_name, date, location, type (volunteer/donate/attend)
```

---

## Resource Allocation

### CPU/Memory
- **8 workers** (1 thread each) = 8 parallel discovery jobs
- **Each worker:** ~100-200MB RAM (requests, BeautifulSoup tree)
- **Total:** ~1.5GB RAM (well within 23GB available)
- **Network:** Stagger requests (avoid IP blocks)

### Execution Time Estimates
| Stage | Duration | Parallelism |
|-------|----------|-------------|
| Gap identification | 5 min | Sequential (SQL query) |
| Website discovery | 30-60 min | 8 workers, 200 orgs each |
| Event extraction | 30-60 min | 8 workers, 100 orgs each |
| Learning analysis | 10 min | Sequential (aggregation) |
| Database import | 5 min | Batch INSERT |
| **Total** | **80-150 min** | **Parallel where possible** |

### Start Time (Estimated)
**2026-07-24 04:50 UTC** (after Phase 2 verification)
**Complete by:** 2026-07-24 07:00 UTC (170 min)

---

## Success Metrics

### Quantitative
- ✅ Websites recovered: +100-500 new URLs
- ✅ Event count: +100-300 new events
- ✅ Coverage improvement: website_status good/valid goes from 80% → 85%+
- ✅ Discovery success rate: ≥70% for queried orgs

### Qualitative
- ✅ Lessons document: Top 3 strategies per NTEE
- ✅ Algorithm improvements: 2-3 scoring adjustments identified
- ✅ Error handling: Categorize failure types for retry
- ✅ Audit trail: 500+ discovery events logged with details

---

## Phased Rollout (Within Phase 3)

### Batch 1: High-Impact Orgs (50 orgs, 10 min)
- Largest nonprofits by peer group
- Purpose: Quick win, validate discovery engine
- If successful: proceed to Batch 2

### Batch 2: Medium Nonprofits (500 orgs, 60 min)
- Community orgs in major metros (CA, TX, NY, IL)
- Purpose: Regional coverage improvement
- If successful: proceed to Batch 3

### Batch 3: Smaller/Rural Nonprofits (1,000+ orgs, 90 min)
- Entire registry (selective based on gaps)
- Purpose: Comprehensive coverage
- Risk: Slower discovery (smaller web presence)

---

## Technical Implementation

### Required Libraries (Already Available)
- ✅ `requests` (HTTP)
- ✅ `BeautifulSoup4` (HTML parsing)
- ✅ `sqlite3` (database access)
- ✅ `threading` (workers)
- ✅ `logging` (audit trail)

### Optional (Install if Needed)
```bash
pip install selenium playwright  # For JavaScript-heavy sites
pip install fake-useragent      # Rotate user agents (avoid blocks)
```

### Key Scripts to Create
1. `scripts/phase3_discover_websites.py` (8 workers, 200 orgs each)
2. `scripts/phase3_extract_events.py` (8 workers, parse websites)
3. `scripts/phase3_learning_analysis.py` (aggregate success patterns)
4. `scripts/phase3_import_results.py` (batch INSERT + audit log)

---

## Audit Logging (Compliance)

Every discovery action logged to `audit_log`:

```sql
INSERT INTO audit_log (
  event_type,          -- 'website_discovered', 'event_discovered', 'discovery_failed'
  timestamp,           -- UTC ISO 8601
  org_ein,            -- Organization (EIN only, no name)
  user_auth,          -- 'discovery-bot' (automated)
  user_role,          -- 'admin'
  success,            -- true/false
  error_code          -- 'NOT_FOUND', 'TIMEOUT', 'PARSE_ERROR', etc.
)
```

No PII logged. Audit trail provides full traceability of what was discovered and why.

---

## Learning Extraction (Algorithm Improvement)

After discovery complete, analyze:

**What worked:**
- By NTEE: Which categories have best website coverage?
- By size: Small vs. large org discovery success rates
- By state: Geographic patterns
- By strategy: Which discovery method worked best?

**What failed:**
- Top 10 error types (timeouts, 404s, parsing errors)
- Patterns in failures (e.g., all arts orgs in rural areas hard to find)
- Retry opportunities (worth a 2nd attempt later?)

**Improvements:**
- Adjust scoring: Boost confidence for successful discovery methods
- Update validation: Stricter checks for high-confidence matches
- Prioritize next batch: Focus on geographic/NTEE gaps identified

---

## Risk Mitigation

### IP Blocking Risk
- **Mitigation:** Rotate user agents, random delays (1-3s between requests), check robots.txt
- **Fallback:** Switch to residential proxy service if rate-limited
- **Monitor:** Check response times, error rates in real-time

### Data Quality Risk
- **Mitigation:** Manual spot-check of 100 discovered URLs (5% sample)
- **Fallback:** Flag low-confidence matches for human review
- **Monitor:** Audit log shows success rate per batch

### Database Lock Risk
- **Mitigation:** Batch INSERTs in transactions, periodic commits
- **Fallback:** Run import outside of peak hours (batch off-hours)
- **Monitor:** Check database lock count during import

---

## Integration with Phase 2

Phase 2 (212-endpoint platform) + Phase 3 (discovery) = **Complete System:**

```
User Journey (End-to-End):
1. Browse nonprofits (Phase 2, native search API)
2. See volunteer events (Phase 3 enrichment)
3. Signal interest (Phase 2, POST /api/interest)
4. Get email notification (Phase 2, email trigger)
5. Claim event (Phase 2, nonprofit portal)
6. Log volunteer hours (Phase 2, hours tracking)
7. All logged for audit (Phase 2, audit_log)
```

---

## Next Steps (Immediate)

1. **Create discovery scripts** (1-2 hours)
2. **Test on small batch** (10 orgs, 5 min)
3. **If successful:** Launch full batch (Batch 1 → 2 → 3)
4. **Monitor in real-time** (logs + audit trail)
5. **Extract learnings** (1-2 hours post-completion)
6. **Document improvements** (lessons.md entry)

---

## Success Criteria (Phase 3 Complete)

✅ Websites recovered: ≥100 new URLs  
✅ Events discovered: ≥50 new volunteer opportunities  
✅ Audit trail: 500+ discovery events logged, zero PII  
✅ Lessons: 3+ algorithm improvements identified + documented  
✅ Coverage: website_status improves from 80% → 85%+  
✅ System stable: No database locks, no rate-limiting blocks  

---

**Phase 3 Status:** READY TO LAUNCH  
**Estimated Duration:** 80-150 minutes  
**Start Time:** Now (after Phase 2 verification)  
**Owner:** Claude Code (autonomous, full server hardware available)
