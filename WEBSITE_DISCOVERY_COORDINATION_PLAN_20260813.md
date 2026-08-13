# Website Discovery Coordination Plan
**Date:** 2026-08-13  
**Status:** 🔴 CRITICAL GAP IDENTIFIED — Donation Link Extraction Stalled  
**Coordination:** Claude Code + Codex Parallel Tracks

---

## The Problem

**Discovery Progress:**
- ✅ 461,682 websites discovered (22.4% of orgs)
- ✅ 87,039 active websites verified (status='ok')
- 🔴 **73,514 donation URLs extracted (16% of discovered sites)**
- 🔴 **388,168 websites with no donation URL (84% backlog)**
- 🔴 **1,983,320 total orgs with no donation link (96.4% of registry)**

**At Current Pace:**
- Daemon progress: ~46 orgs/iteration, ~6 min/iteration = ~460 orgs/day
- ETA for completion: 844 days ❌
- **Task #11 Phase 1 blocked until donation links are available**

---

## Root Cause: What's Missing?

**Key Question:** Of the 461,682 verified websites, how many actually *have* donation links on them?

| Scenario | Implication | Action |
|----------|-------------|--------|
| **A: 73K sites have donate buttons; 388K don't** | Sites lack donate links (design problem) | Document, accept, create fallback UX |
| **B: 388K+ sites have donate buttons; we're not finding them** | Algorithm incomplete (extraction problem) | Fix extraction, accelerate daemon |
| **C: Mix of both** | Some sites lack links + extraction misses some | Hybrid: accelerate + create fallback |

**We must clarify this immediately.**

---

## Coordination Strategy

### **Track 1: Codex — Donation Link Acceleration**

**Owner:** Codex  
**Duration:** 48 hours (investigate + fix)  
**Deliverable:** Diagnostic report + acceleration plan

#### Phase 1: Audit (Today — 4 hours)

1. **Sample 100 verified websites**
   - Randomly select 100 sites with `website_status='ok'`
   - Manually check: Does each site have a "Donate" button/link?
   - Record: Count with donate links + URL patterns

2. **Measure extraction**
   - Of those 100, how many have `donate_url` in DB?
   - Gap analysis: manual check vs. what's extracted

3. **Profile daemon performance**
   - Run diagnostic: workers active? GPU accelerated? Rate limits?
   - Measure: sites processed per minute (current vs. theoretical max)

4. **Report findings**
   - Donation link availability: X% of sites have extractable links
   - Extraction rate: Y sites/day at current speed
   - Bottleneck: Worker parallelization? Network? Algorithm?

#### Phase 2: Acceleration Plan (Tomorrow — 4 hours)

**If bottleneck is throughput:**
- Increase batch size (50 → 200)
- Increase workers (8 → 24)
- Enable GPU acceleration (if not active)
- Use headless browser (Puppeteer/Playwright) for JS rendering
- **Expected:** 10x throughput (460 → 4,600 orgs/day)

**If bottleneck is algorithm:**
- Improve donation link detection patterns
- Add common paths: `/donate`, `/give`, `/support`, `/fund`
- Check Charity Navigator / GiveWell for external links
- Test on sample set, re-run daemon
- **Expected:** 5x throughput (460 → 2,300 orgs/day)

**If bottleneck is missing data:**
- Accept that 388K sites lack donate buttons (15-20% of all websites)
- Focus on extracting from the extractable 73K
- Create fallback UX for sites without links
- **Expected:** Complete 73K in 160 days, halt

#### Deliverable: Diagnostic Report

Create `DONATION_LINK_EXTRACTION_DIAGNOSTIC_20260813.md` with:
```
Audit Results (100-site sample):
- Sites with donate button: X%
- Sites with extracted donate_url: Y%
- Gap: (X-Y)%

Extraction Performance:
- Current: 460 orgs/day
- Theoretical max (full parallelization): Z orgs/day
- Bottleneck: [Worker pool / Network / Algorithm]

Acceleration Plan:
- Action 1: [increase batch size / enable GPU / improve algo]
- Action 2: [...]
- Expected result: N orgs/day target
- ETA to complete 388K: D days
```

**Submit by:** Tomorrow 6 AM CDT

---

### **Track 2: Claude Code — Fallback UX for Task #11**

**Owner:** Claude Code  
**Duration:** Parallel to Track 1 (doesn't wait)  
**Deliverable:** Fallback UX design + implementation plan

#### Phase 1: Design Fallback (Today — 2 hours)

**Scenario A: Site has no donate button (likely for 15-20% of sites)**

UI Component: "Give Now" section on org detail page

```
Case 1: donate_url EXISTS
┌─────────────────────────────────┐
│ ✅ GIVE NOW                      │
│ ┌─────────────────────────────┐ │
│ │ Visit [org website] to give │ │
│ │ [Donate button/link]        │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘

Case 2: donate_url NOT FOUND (website exists but no link found)
┌─────────────────────────────────┐
│ 📍 GIVE DIRECTLY                 │
│ ┌─────────────────────────────┐ │
│ │ Visit their website:        │ │
│ │ [org.website]               │ │
│ │                             │ │
│ │ Look for "Donate" or        │ │
│ │ "Give" button (usually      │ │
│ │ top-right or footer)        │ │
│ └─────────────────────────────┘ │
│                                  │
│ 🔗 Other giving options:        │
│ • Charity Navigator profile     │
│ • GiveWell (if rated)           │
│ • Donor-Advised Fund (DAF)      │
└─────────────────────────────────┘

Case 3: No website at all (19% of micro-orgs)
┌─────────────────────────────────┐
│ 📞 CONTACT DIRECTLY             │
│ ┌─────────────────────────────┐ │
│ │ Phone: [if available]       │ │
│ │ Email: [if available]       │ │
│ │                             │ │
│ │ Ask them how to support     │ │
│ │ their work.                 │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

**Stewardship Alignment:**
- ✅ Honest ("we don't have a direct link yet")
- ✅ Helpful ("here's how to find it yourself")
- ✅ Enabling (gives agency, not blocking)

#### Phase 2: Implementation Plan (Today — 2 hours)

**Changes needed:**

1. **Frontend (`OrganizationDetail.tsx`)**
   - Add conditional logic for donate_url
   - Case 1: donate_url exists → Button with link
   - Case 2: website exists, donate_url missing → "Visit website" UI
   - Case 3: no website → "Contact directly" UI
   - Add copy: "Help us improve: [report missing donate link]"

2. **Backend API (`/api/organizations/{ein}`)**
   - Return: `donate_url`, `donate_confidence`, `donate_url_status`
   - Add: `website_final_domain`, `website_status` (already exists)
   - Add: `contact_email`, `contact_phone` (if available)

3. **Analytics**
   - Track: Which UI case is shown most? (feedback on donation link coverage)
   - Track: Click-through to website vs. direct donate button

**File Structure:**
```
frontend/src/components/
  ├── DonateOptions.tsx (new component)
  │   ├── Case 1: DirectDonateLink
  │   ├── Case 2: VisitWebsiteToDonate
  │   └── Case 3: ContactDirectly
  └── (integrate into OrganizationDetail.tsx)
```

#### Deliverable: Design Doc + Wireframes

Create `DONATION_FALLBACK_UX_DESIGN_20260813.md` with:
```
Problem: 84% of discovered websites lack donation URLs (extracted)

Solution: Three-tier fallback UX
- Tier 1 (16% of sites): Direct donate link available → Button
- Tier 2 (68% of sites): Website exists, link unknown → "Visit website"
- Tier 3 (16% of sites): No website → "Contact org directly"

Implementation:
- Component: DonateOptions.tsx
- Logic: Conditional on donate_url presence
- Copy: Affirming, not apologetic
- Analytics: Track which tier users see

Supports Task #11 Phase 1 launch even if donation links are incomplete.
```

**Submit by:** Today 4 PM CDT

---

## Synchronization Points

### **Day 1 (Today) — Parallel Execution**

| Track | Owner | Output | Time |
|-------|-------|--------|------|
| **Track 1 Phase 1** | Codex | Diagnostic report (100-site audit) | 4 hrs |
| **Track 2 Phase 1** | Claude | Fallback UX design | 2 hrs |
| **Sync Point 1** | Both | Review findings + decide next steps | 30 min |

**Decision Point After Sync 1:**
- If donation links ARE extractable: Codex accelerates daemon (Track 1 Phase 2)
- If donation links DON'T EXIST on sites: Proceed with fallback UX (Track 2 Phase 2)
- If mixed: Do both (parallel)

### **Day 2 (Tomorrow) — Execution**

| Track | Owner | Output | Time |
|-------|-------|--------|------|
| **Track 1 Phase 2** | Codex | Acceleration implementation (if needed) | 4 hrs |
| **Track 2 Phase 2** | Claude | Fallback UX implementation | 4 hrs |
| **Sync Point 2** | Both | Verify daemon running + UI on staging | 30 min |

### **By EOW — Integration**

| Task | Owner | Status |
|------|-------|--------|
| Donation link extraction | Codex | Accelerated + diagnostic committed |
| Fallback UX | Claude | Live on staging (ready for Task #11 Phase 1) |
| Task #11 Phase 1 Start | Both | Unblocked (no longer waiting for 100% donate URLs) |

---

## Success Criteria

### **Codex Track Success:**
- [ ] Diagnostic report submitted (100-site audit complete)
- [ ] Extraction bottleneck identified (worker pool / algorithm / data)
- [ ] Acceleration plan documented with realistic ETA
- [ ] Daemon re-configured (if bottleneck is throughput)
- [ ] Target: 2,000–4,600 orgs/day (5–10x current)

### **Claude Track Success:**
- [ ] Fallback UX design approved (three-tier model)
- [ ] Implementation plan written (DonateOptions component)
- [ ] Staging deployment ready
- [ ] Analytics instrumented (track which tier users see)
- [ ] Task #11 Phase 1 unblocked (donate links no longer a blocker)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Donation links don't exist on 70%+ of sites | Accept this, accelerate extraction for available links, deploy fallback UI |
| Daemon acceleration adds cost/complexity | Profile first; only accelerate if algorithm allows it; keep rollback plan |
| Fallback UI feels like cop-out to users | Design affirming messaging ("Help us improve") + analytics to measure impact |
| Codex diagnostic takes >4 hours | Focus audit on 100 sites; defer full implementation; provide daily standup updates |

---

## Communication Plan

### **To Codex:**

> "Website discovery audit needed. Of 461K sites discovered, only 73K have donate URLs extracted (84% gap). Need diagnostic:
> 
> 1. **100-site manual audit** — How many sites actually have donate buttons?
> 2. **Performance profile** — Current 460 orgs/day; what's the bottleneck?
> 3. **Acceleration plan** — How to achieve 2K–4.6K orgs/day?
> 
> Report by tomorrow 6 AM. This unblocks Task #11 Phase 1."

### **To Yourself (When You Return):**

Review Track 1 (Codex diagnostic) + Track 2 (Claude fallback UX):
- Is donation link availability the issue, or extraction?
- Approve Codex acceleration plan (if needed)
- Approve Claude fallback UX design
- Kick off parallel execution

### **To Team (After Both Tracks Complete):**

> "Website discovery coordination complete:
> - Donation link extraction: [X orgs/day → Y orgs/day] via [acceleration strategy]
> - Fallback UX: Ready for sites without donate URLs
> - Task #11 Phase 1: Unblocked, ready to launch
> - ETA for 388K remaining: [N] days"

---

## Appendix: Donation Link Extraction Patterns

**Common patterns to search for:**

```
Paths:
/donate, /giving, /support, /fund, /contribution, /join, /pledge

Button text (case-insensitive):
"donate", "give", "support us", "fund us", "contribute", "join us"

Elements:
<a> tags with href containing above
<button> with text above
Meta tags (og:url for donate page)

External signals:
GiveWell rating (=> has donate link)
Charity Navigator profile (=> likely has donate link)
```

**Testing approach:**
1. Fetch homepage HTML
2. Search for patterns (quick regex)
3. Parse buttons + links (BeautifulSoup/Puppeteer for JS)
4. Validate link (HEAD request → 200 OK)
5. Store: `donate_url`, `donate_confidence`, `donate_url_status`

---

## Files to Create

1. **Track 1:** `DONATION_LINK_EXTRACTION_DIAGNOSTIC_20260813.md` (Codex)
2. **Track 2:** `DONATION_FALLBACK_UX_DESIGN_20260813.md` (Claude)
3. **Sync:** `WEBSITE_DISCOVERY_COORDINATION_SYNC_20260813.md` (after sync point 1)

---

## Estimated Timeline

| Milestone | Date | Owner | Status |
|-----------|------|-------|--------|
| **Codex Diagnostic** | Aug 13 6 AM | Codex | ⏳ In progress |
| **Claude Fallback Design** | Aug 13 4 PM | Claude | ⏳ In progress |
| **Sync Point 1** | Aug 13 5 PM | Both | ⏳ Pending |
| **Track 2 Implementation** | Aug 14 EOD | Claude | ⏳ Ready to start |
| **Track 1 Acceleration** | Aug 14 EOD | Codex | ⏳ Ready to start |
| **Task #11 Phase 1 Unblocked** | Aug 14 EOW | Both | ⏳ On track |

---

## Current Blockers

🔴 **Task #11 Phase 1 is blocked on:**
- Donation link availability for fallback UX design
- Extraction throughput for data completeness

**This plan unblocks both within 48 hours.**

---

**Status: COORDINATION PLAN READY**

Codex: Start diagnostic audit (100-site sample).  
Claude: Design fallback UX (three-tier model).  
Sync tomorrow at 5 PM CDT.
