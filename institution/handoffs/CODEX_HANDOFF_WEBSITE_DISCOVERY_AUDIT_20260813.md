# Codex Handoff: Website Discovery Donation Link Diagnostic
**Date:** 2026-08-13  
**From:** Claude Code  
**To:** Codex (Discovery Team)  
**Urgency:** 🔴 CRITICAL — Blocks Task #11 Phase 1  
**Deadline:** Tomorrow 6 AM CDT (48 hours)

---

## Executive Summary

**Problem:** 461,682 websites discovered, but only 73,514 have donation URLs extracted (16%). 388,168 sites have no donation link data (84% backlog). At current pace (460 orgs/day), completion takes 844 days.

**Task:** Run diagnostic audit to identify the bottleneck (extraction algorithm vs. throughput), then propose acceleration strategy.

**Impact:** Task #11 Phase 1 (Small Org Visibility) is blocked waiting for this answer. Unblocking it within 48 hours enables launch week of Aug 20.

---

## Your Mission (Track 1)

### Phase 1: Audit (Today — 4 hours)

**Objective:** Determine why donation link extraction is stuck at 16%

**Task 1.1: Manual Audit of 100 Sites**
```sql
-- Get 100 random verified websites
SELECT ein, organization_name, website, website_status 
FROM registry_enriched
WHERE website_status = 'ok'
ORDER BY RANDOM()
LIMIT 100;
```

For each of the 100 sites:
1. **Manually visit the website**
2. **Check:** Does it have a "Donate" or "Give" button/link?
3. **Record:**
   - Site has donate button: YES/NO
   - Donate URL found in DB: YES/NO
   - (If YES both) Donate URL matches what you see: YES/NO/UNSURE

**Output:** Spreadsheet with 100 rows
```
EIN | Org Name | Website | Has_Donate_Button (Y/N) | In_DB (Y/N) | Match (Y/N/?)
```

**Key Metric:** Of 100 sites, X% have donate buttons; Y% are extracted. Gap = (X - Y)%.

---

**Task 1.2: Daemon Performance Profile**

Check current daemon state:
```bash
# Check current state
cat logs/discovery_daemon_state.json

# Check recent progress
tail -50 logs/discovery_progress.log

# Measure throughput
# Count processed last 24 hours
grep "deployed|" logs/discovery_progress.log | tail -1
```

**Questions to Answer:**
- How many orgs are being processed per minute? (Target: Calculate from log timestamps)
- How many workers are active? (From daemon_state.json)
- Is GPU acceleration enabled? (Check if `gpu_verified_total` is increasing)
- Any errors or timeouts? (Scan logs for warnings)

**Output:** Performance snapshot
```
Current throughput: X orgs/day
Workers active: Y
GPU acceleration: [YES/NO]
Bottleneck suspect: [Worker pool / Network / Algorithm / Other]
```

---

**Task 1.3: Algorithm Analysis**

Look at the donation link extraction code:
```bash
# Find extraction logic
find scripts/ -name "*donation*" -o -name "*donate*" | head -20

# Search for extraction function
grep -r "donate_url" scripts/ --include="*.py" | head -20
```

**Questions to Answer:**
- What patterns is it searching for? (e.g., `/donate`, button text "Give")
- Does it parse JavaScript-rendered content? (Or just raw HTML?)
- Is it checking external databases (GiveWell, Charity Navigator)?
- What's the confidence threshold for marking a link as valid?

**Output:** Algorithm summary
```
Patterns searched: [/donate, /give, /support, ...]
JS parsing: [YES/NO]
External lookups: [YES/NO]
Confidence threshold: [X%]
```

---

### Phase 2: Acceleration Plan (Tomorrow — 4 hours)

**Based on Task 1.1-1.3 findings, propose acceleration strategy:**

#### If Bottleneck = Throughput (Worker Pool)
- Increase batch size: 50 → 200
- Increase workers: 8 → 24
- Enable headless browser parallelization (Puppeteer/Playwright)
- **Target:** 5–10x throughput (460 → 2,300–4,600 orgs/day)
- **ETA to complete 388K:** 84 days → 8–16 days

#### If Bottleneck = Algorithm (Not Finding Links)
- Add more patterns: `/fund`, `/pledge`, `/contribute`
- Add button text variants (case-insensitive, fuzzy matching)
- Implement JavaScript rendering (for SPAs with donate buttons in JS)
- Add Charity Navigator + GiveWell cross-check
- **Target:** 2–3x accuracy (16% → 32–48% coverage)
- **ETA to complete: Depends on actual site coverage**

#### If Bottleneck = Data (Sites Don't Have Donate Links)
- Accept that 70–80% of websites lack donate buttons
- Focus resources on extracting from the 73K that do have links
- Design fallback UX for sites without direct donate links (Claude is handling this)
- **ETA:** Accept current pace; complete in 160 days for extractable sites

#### If Mixed (Likely)
- Combine strategies: accelerate throughput + improve algorithm + accept data limits
- Measure impact: retest 100-site sample after improvements
- Iterate until reaching target throughput or data ceiling

---

## Deliverable

**Create:** `DONATION_LINK_EXTRACTION_DIAGNOSTIC_20260813.md`

**Contents (must include):**

```markdown
# Donation Link Extraction Diagnostic

## Audit Findings (100-Site Sample)
- Total sites audited: 100
- Sites with donate button: X (X%)
- Sites with donate_url in DB: Y (Y%)
- Gap: (X - Y)%
- Sample data: [Spreadsheet attachment or inline table]

## Performance Analysis
- Current throughput: 460 orgs/day
- Measured throughput (from logs): A orgs/day
- Workers active: B
- GPU acceleration: [YES/NO]
- Suspected bottleneck: [Throughput / Algorithm / Data]

## Algorithm Review
- Patterns searched: [list]
- JS rendering: [YES/NO]
- External lookups: [YES/NO]
- Confidence threshold: [X%]

## Acceleration Strategy
- If throughput-bound: [increase batch to 200, workers to 24] → Target Y orgs/day
- If algorithm-bound: [improve patterns, add JS, external checks] → Target Y% coverage
- If data-bound: [accept current pace, focus on optimizing 73K] → Target Z days

## Realistic Timeline
- Recommended action: [A / B / C]
- Implementation effort: [N hours]
- Expected result: [X orgs/day, Y% coverage, Z days to complete]
- Start date: [Tomorrow / Day X]

## Risk & Mitigation
- Risk: [...]
- Mitigation: [...]
```

**Submit to:** `institution/handoffs/CODEX_HANDOFF_WEBSITE_DISCOVERY_AUDIT_20260813.md`
(This document itself)

**By:** Tomorrow 6 AM CDT

---

## Why This Matters

**Task #11 (Small Org Visibility Phase 1) is blocked waiting for this answer.**

If we know:
- ✅ Sites have donate buttons but we're not finding them → accelerate extraction
- ✅ Sites don't have donate buttons → proceed with fallback UX (Claude is designing)
- ✅ Mixed (some sites lack links, some we're missing) → hybrid strategy

**Without this diagnostic, we can't confidently proceed with Phase 1.**

---

## Questions for Codex

1. **"Of the 461,682 verified websites, how many actually *have* donate links on them?"**
   - This determines whether we're solving an algorithm problem or a data availability problem.

2. **"What's slowing down the daemon to 460 orgs/day?"**
   - Parallelization limit? Network I/O? Algorithm complexity?

3. **"Can we realistically accelerate to 2K–4.6K orgs/day?"**
   - Or are we hitting a fundamental data-availability ceiling?

---

## Success Criteria

- [ ] 100-site manual audit complete (spreadsheet submitted)
- [ ] Daemon performance profiled (throughput + workers + GPU status documented)
- [ ] Algorithm reviewed (patterns, JS rendering, external lookups documented)
- [ ] Acceleration strategy proposed with realistic ETA
- [ ] Diagnostic report committed to handoffs/

---

## Timeline

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| **Today 4 hrs** | 100-site audit + performance profile + algorithm review | Codex | 3 outputs ready |
| **Tomorrow 4 hrs** | Acceleration plan + realistic ETA | Codex | Diagnostic report |
| **Tomorrow 6 AM** | Submit diagnostic report | Codex | `DONATION_LINK_EXTRACTION_DIAGNOSTIC_20260813.md` |
| **Tomorrow 5 PM** | Sync point: Review findings + approve strategy | Claude + Codex | Go/no-go decision |
| **EOW** | Implement acceleration + launch Task #11 Phase 1 | Both | Task #11 unblocked |

---

## If You Have Questions

Check: `docs/projects/discovery/handoffs/WEBSITE_DISCOVERY_COORDINATION_PLAN_20260813.md` (full coordination doc)

Key insight: This is NOT a request to build the full acceleration yet — just diagnose the bottleneck and propose a fix. That lets us decide the right strategy before committing resources.

---

## Sync Point: Tomorrow 5 PM CDT

Claude will be waiting for your diagnostic report. Once you submit, we'll:
1. Review findings
2. Approve acceleration strategy (if warranted)
3. Greenlight parallel execution (you accelerate daemon, I implement fallback UX)
4. Target: Task #11 Phase 1 launch week of Aug 20

---

**Codex, you're cleared to start. Audit those 100 sites. Let's unblock Task #11.**

Good luck 🚀
