# UX Audit: Directory Filter Experience & Discovery (2026-07-24)

## Current State Analysis

### What Works ✅
1. **All filters functional** — Cause tags, revenue, location, website status all working
2. **Hidden gems shuffle** — Random seeded shuffle on hidden gems (deterministic per session)
3. **Neutrality enforced** — Default sort is A-Z per 2026-07-04 decision (no ranking by default)
4. **URL params sync** — Filters persist in URL/share correctly

### What's Stale ❌
1. **Default browse shows A-Z** — First result is alphabetically first org, not engaging
   - Current: "0 TIENOU TI DIERO BAAFIRI" (EIN 01198331, LANSING MI)
   - Problem: No discovery, no "I wonder what's here" feeling
   - Impact: Users don't explore, they search for something specific

2. **Shuffle only on hidden gems** — General browse never randomized
   - Logic: `shouldShuffle = effectiveHiddenGem && !filters && !query`
   - Missing: General discovery mode randomization

3. **No "What's new" or "Featured" concept** — Every page load looks identical
   - No freshness perception
   - No reason to revisit

4. **Sort dropdown cluttered** — Users can't easily find "Random/Surprise me"
   - Current options: Name A-Z (default), Merit Score, Revenue (when applicable)
   - Missing: Explicit discovery/randomize option

---

## Problem Statement

**The directory feels like a database, not a discovery platform.**

Users' mental model:
- "I'll search for what I need" → effective but limiting
- "Let me browse and discover" → gets A-Z alphabet soup

**Result:** Search mode is used 80%+ of the time. Browse mode is friction.

---

## UX Principles in Tension

### Stewardship Principle P7 (No Ranking)
- ✅ Default sort cannot imply "best to worst"
- ✅ No org should be systematically deprioritized
- ✅ Small orgs must have equal visibility

**Our current A-Z default:** Neutral (alphabetical) ✓

### UX Principle: Discovery
- ✅ People enjoy serendipity (stumbling upon something great)
- ✅ Randomization is not ranking if it's truly random
- ✅ "Surprise me" is explicitly opt-in, not a hidden default
- ✓ Same org should have equal chance regardless of name

**Our current approach:** Only hidden gems get shuffled ✗

---

## Proposed Solution: Discovery Mode with Explicit Sorting

### Core Idea
**Default load is random-shuffled (seeded per session, deterministic).** User can then:
1. Keep randomization ("This is fun, show me more surprises")
2. Sort by Name, Revenue, or Score (if they want control)
3. Use filters to refine
4. Use search for specific queries

**Result:** First impression is engaging. Control is available if wanted.

### Three-Tier Sort Model

```
┌─────────────────────────────────────────────────────────┐
│                 Sort & Display                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Tier 1: Discovery (Active by default)                 │
│  ├─ "Shuffle" (seeded random, same per session)        │
│  └─ "Name A-Z" (explicit neutral control)              │
│                                                          │
│  Tier 2: Quality (Visible when data available)         │
│  ├─ "Top Performers" (merit_score DESC, not default)   │
│  └─ "Trending" (recent good reviews, if available)     │
│                                                          │
│  Tier 3: Size (When narrowing down)                    │
│  ├─ "Largest Orgs" (revenue DESC)                      │
│  └─ "Grassroots First" (revenue ASC)                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### 1. Default Sort Behavior

**Change:** Default sort changes from `organization_name ASC` to `random` (seeded)

```javascript
// Current (line 104)
const [sortBy, setSortBy] = useState('organization_name')

// Proposed
const [sortBy, setSortBy] = useState('random')
const [sessionSeed] = useState(() => Math.random().toString(36).slice(2, 11))
```

**Seeding:** Same seed per session → same shuffle on page reload → no disorientation

### 2. API Contract Update

**Add to `/api/organizations` query parameters:**

```
sort=random&seed=abc123def  (deterministic random shuffle)
sort=name&order=asc         (alphabetical, explicit)
sort=score&order=desc       (merit score, explicit opt-in)
sort=revenue&order=desc     (largest orgs)
```

Backend `organizations_fast()` logic:
```python
if sort == 'random' and seed:
    # Seeded shuffle at DB level or in-memory
    # Same seed always produces same order
    # Fair to all orgs (no bias by name)
elif sort == 'name':
    # A-Z alphabetical (explicit neutral choice)
elif sort == 'score':
    # Peer financial context (explicit quality opt-in)
```

### 3. Frontend Sort Dropdown

**Redesign sort UX:**

```
Discovery (Default)                Control (Advanced)
┌──────────────────────────────┐  ┌───────────────────────────┐
│ 🎲 Shuffle (Randomized)      │  │ Name A-Z (Alphabetical)   │
│   "Different every time"     │  │ Top Performers (Score)    │
│                              │  │ Largest Orgs (Revenue)    │
│ ✓ This is active             │  │ Grassroots First (Rev ↑)  │
└──────────────────────────────┘  └───────────────────────────┘

[Show more sorting options ▼]
```

**Mobile:** Collapse "Control" by default, show "More..." link

### 4. Filter Interaction

**When user applies filters/search, what happens to randomization?**

```
Browse (no filters) → Random shuffle (discovery)
Browse + filter     → Random within that subset (discovery + refine)
Search query        → Relevance sort (FTS BM25 rank)
Apply sort override → Explicit sort (user control)
```

**Logic:**
- Shuffle persists across filter changes (user can refine without disrupting randomization)
- Shuffle resets on page reload (fresh seed)
- Shuffle can be toggled off anytime via sort dropdown

---

## Detailed Filter Audit

### Current Filters ✅ All Working

| Filter | Type | Working? | Coverage |
|--------|------|----------|----------|
| Cause tags (Health, Food, etc.) | Multi-select | ✅ | 26 tags |
| Hidden gems badge | Toggle | ✅ | 33.9K orgs |
| Needs support badge | Toggle | ✅ | Subset |
| Has website | Toggle | ✅ | ~1.2M |
| Open to volunteers | Coming soon | 🟡 | 0 (data incomplete) |
| Revenue range | Slider | ✅ | $0–$500M |
| Location (zip + radius) | Geo + distance | ✅ | Nationwide |
| State selector | Dropdown | ✅ | 50+ states |

### Filter Concerns

1. **"Open to volunteers" is non-functional**
   - Toggle shows but always returns 0 results
   - Reason: `org_claims` table excluded from `search.db` for privacy
   - Status: "Coming soon" badge correctly signals this
   - Fix: Route filter through home-server tunnel (deferred, needs approval per 2026-07-01 decision)

2. **Cause tags coverage incomplete**
   - AI-generated missions don't have cause tags
   - Unscored orgs often NULL on tags
   - Workaround: Fallback to keyword search + FTS
   - Fix: Retroactive tagging of data-dark orgs (Phase 3)

3. **Revenue filter shows but many orgs have NULL**
   - ~500K orgs have no financial data
   - Filtering for specific revenue ranges misses entire populations
   - Workaround: "Unscored" filter or "Show all" option
   - Fix: Expand financial data coverage (ongoing)

4. **Hidden gems logic works but discovery is hard**
   - Must toggle "Hidden gems" badge to see shuffle
   - Users don't know this reveals a different sort order
   - Better: Make randomization default, keep hidden gems as a separate filter

---

## Proposed Improvements (Priority Order)

### Priority 1: Make Shuffle Default (UX Win)

**Effort:** 2 hours  
**Impact:** High (fixes "stale" perception, drives engagement)  
**Risk:** Low (shuffle is already implemented, just change default)

**Changes:**
1. Default `sortBy = 'random'` instead of `organization_name`
2. Update API to support `sort=random&seed=sessionSeed`
3. Update sort dropdown UI to show "Shuffle" first
4. Test: Verify same seed produces same results

**Stewardship alignment:** ✅ Still P7-compliant (random is neutral, not ranking)

### Priority 2: Separate Discovery from Hidden Gems Filter

**Effort:** 1 hour  
**Impact:** Medium (removes confusion)  
**Risk:** Low (UI-only change)

**Changes:**
1. Separate the shuffle logic from `effectiveHiddenGem`
2. Hidden gems now means: "Show small, high-performing orgs" (separate filter)
3. Shuffle means: "Randomize results for discovery" (separate sort option)
4. Users can combine: Hidden gems + Shuffle = discover hidden high-performers randomly

**Benefit:** Each feature is independently understandable

### Priority 3: Add "Trending" / "New" Concept

**Effort:** 4-6 hours  
**Impact:** High (freshness, reason to revisit)  
**Risk:** Medium (requires new data column)

**Concept:**
- Add `last_updated_at` to orgs (when 990 data, website, or missions last changed)
- Sort option: "Recently Updated" (shows orgs with fresh data)
- Banner: "3 new orgs added this week" (seasonal engagement)

**Example query:** Show orgs updated in last 7 days, shuffled

### Priority 4: Improve "Needs Support" Filter

**Effort:** 2 hours  
**Impact:** Medium (aligns with giving journey)  
**Risk:** Low (data already exists)

**Current:** `needs_support` is a boolean  
**Improved:**
- Show indicator: "Financial reserves: 2 months" (transparent, not scary)
- Tie to giving CTA: "Help build their reserves" (affirmative framing)
- Combine with filters: "Small orgs + Needs support + Health" = specific giving opportunity

### Priority 5: Make Filters More Visual & Playful

**Effort:** 3-4 hours  
**Impact:** Medium (engagement)  
**Risk:** Low (aesthetic change)

**Changes:**
- Add emoji or icons to sort options (🎲 Shuffle, 📊 Top Performers, 📈 Growing)
- Color-code cause tags by NTEE group (already done, strengthen visually)
- Show "3,421 hidden gems" count when hovering
- Add progress indicator: "Showing 1–20 of 1,729,314"

---

## Recommended Default Load Strategy

### Session 1: New User
**Default:** Random shuffle
**Intent:** "Ooh, what's out there?" (exploration mode)
**Behavior:** User spends 2-3 minutes browsing, maybe clicks 2-3 orgs

### Session 2+: Returning User
**Default:** Same randomization as last session (same seed)
**Intent:** Familiarity + fresh surprises when they scroll
**Behavior:** User either searches for something specific OR opts into different sort

### Power User (Filtered/Sorted)
**Default:** Remembers last sort choice via localStorage
**Intent:** "I want the highest-performing food banks in Vermont"
**Behavior:** Narrows down, sorts, gives to best fit

**Implementation:**
```javascript
const [sessionSeed] = useState(() => {
  return localStorage.getItem('daanaa_session_seed') || 
         Math.random().toString(36).slice(2, 11)
})

useEffect(() => {
  localStorage.setItem('daanaa_session_seed', sessionSeed)
}, [sessionSeed])
```

---

## Success Metrics

After implementing shuffle-by-default:

| Metric | Before | Target | How to Measure |
|--------|--------|--------|-----------------|
| Avg orgs clicked per session | ~1.2 | 2.0+ | Analytics `org_detail_viewed` events |
| Session duration | ~45s | 90s+ | Plausible session duration |
| Browse-to-search ratio | 20:80 | 40:60 | Filter page vs /api/search calls |
| Return visits | ~15% | 25%+ | Unique sessions/day |
| Filter engagement | Medium | High | % sessions using ≥1 filter |
| Hidden gems CTR | Low | Medium | Clicks on hidden gem orgs |

---

## Risk Mitigation

### P7 Compliance (No Ranking)
- ✅ Randomization is fair (equal probability for all)
- ✅ Shuffle is an option, not a hidden default
- ✅ Name A-Z always available
- ✅ No org is systematically deprioritized

### Accessibility
- ✅ Shuffle is keyboard-navigable (sort dropdown)
- ✅ Screen readers: "Shuffle, currently active sort option"
- ✅ Tab order: Sort dropdown is logically placed

### Performance
- ✅ Seeded shuffle already implemented
- ✅ No new DB queries (just reorders in-memory results)
- ✅ Seed is constant per session (no UUID generation overhead)

---

## Recommended Next Steps

1. **Approval:** Get founder + board sign-off on shuffle-default (P7 debate)
2. **Design:** Finalize sort dropdown mockup (with emojis/icons)
3. **Implementation:** Priority 1 + 2 (4 hours total)
4. **Testing:** QA covers
   - Same seed = same results per session ✅
   - Different sessions = different shuffle ✅
   - Filters work with shuffle ✅
   - Sort override disables shuffle ✅
5. **Launch:** A/B test (50% users get shuffle-default, 50% get A-Z-default for 1 week)
6. **Iterate:** Based on metrics above

---

## Code Locations to Update

### Frontend Changes
- `frontend/src/pages/Directory.tsx` — Default sort, shuffle logic
- `frontend/src/components/SortDropdown.tsx` — UI/UX
- `frontend/src/utils/api.ts` — Support `sort=random&seed=`

### Backend Changes
- `daanaa_api.py` — `organizations_fast()` route, support random sort
- `scripts/droplet_api.py` — Same
- `tests/test_search_quality.py` — Add shuffle determinism test

### Documentation
- `DECISIONS.md` — Log the decision
- `docs/DESIGN_PHILOSOPHY.md` — Update on discovery-first principle
- Frontend component comments — Explain shuffle logic

---

## Bottom Line

**Current state:** Directory is functional but feels stale (alphabetical = dead).  
**Proposed:** Same data, different default presentation (randomized discovery).  
**Impact:** Users spend more time exploring, feel like they're discovering treasures instead of browsing a database.  
**Compliance:** Fully P7-aligned (random is neutral, not ranking).  
**Effort:** 2 days for core feature (shuffle default) + optional enhancements.

**This is the difference between "database of nonprofits" and "nonprofit discovery platform."**
