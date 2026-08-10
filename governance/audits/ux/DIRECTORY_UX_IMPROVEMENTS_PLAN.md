# Directory UX Improvements — Action Plan (2026-07-24)

**Objective:** Transform directory from "database browser" to "discovery platform"  
**Key Change:** Default load is seeded-random (engagement), not alphabetical (stale)  
**Founder Approval Status:** ⏳ Awaiting decision on P7 implications

---

## Quick Summary for Approval

### What's the Problem?
User lands on directory → sees "0 TIENOU TI DIERO BAAFIRI" (alphabetically first) → leaves  
**Mental model:** "This is a database, not a discovery tool"

### What's the Fix?
Default sort = seeded random shuffle (fair to all orgs, different every session)  
User can then sort by Name/Score/Revenue/Trending if they want control

### Does This Break P7 (No Ranking)?
**No.** Randomization is fair (equal probability). It's not "best to worst."  
Same decision we made for hidden gems shuffle in 2026-07-04 session.

### How Long?
- Core feature: 2 hours
- Tests: 1 hour
- Polish: 1 hour
- **Total: 4 hours** (1 dev-day)

---

## Sprint Plan (If Approved)

### Phase 1: Core Implementation (2 hours)

#### Change 1: Default Sort Logic
**File:** `frontend/src/pages/Directory.tsx` (line 104)

```javascript
// BEFORE
const [sortBy, setSortBy] = useState('organization_name')

// AFTER
const [sortBy, setSortBy] = useState('random')
const [sessionSeed] = useState(() => {
  return localStorage.getItem('daanaa_session_seed') || 
         Math.random().toString(36).slice(2, 11)
})
useEffect(() => {
  localStorage.setItem('daanaa_session_seed', sessionSeed)
}, [sessionSeed])
```

#### Change 2: API Contract
**File:** `daanaa_api.py` function `organizations_fast()`

```python
sort = request.args.get('sort', 'random')  # Changed from 'name'
seed = request.args.get('seed', '')

if sort == 'random' and seed:
    # Seeded shuffle (same seed = same order)
    results = _seeded_shuffle(organizations, seed)
elif sort == 'name':
    results = sorted(organizations, key=lambda o: o['organization_name'])
elif sort == 'score':
    results = sorted(organizations, key=lambda o: o.get('merit_score', 0), reverse=True)
elif sort == 'revenue':
    results = sorted(organizations, key=lambda o: o.get('total_revenue', 0), reverse=True)
```

Helper function (add to daanaa_api.py):
```python
def _seeded_shuffle(items, seed):
    """Seeded shuffle ensures same seed = same order (deterministic)."""
    import random
    rng = random.Random(seed)
    result = items[:]
    rng.shuffle(result)
    return result
```

#### Change 3: Sort Dropdown UX
**File:** `frontend/src/components/SortDropdown.tsx` (or similar)

```jsx
// Option 1: Compact (mobile-friendly)
<select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
  <option value="random">🎲 Shuffle (Randomized)</option>
  <option value="name">A–Z (Alphabetical)</option>
  <option value="score">📊 Top Performers</option>
  <option value="revenue">📈 Largest Orgs</option>
</select>

// Option 2: Expanded (desktop)
<div className="sort-options">
  <div className="sort-group">
    <label>
      <input type="radio" value="random" checked={sortBy === 'random'} onChange={...} />
      🎲 Shuffle — "Different every time"
    </label>
  </div>
  <div className="sort-group">
    <label>
      <input type="radio" value="name" checked={sortBy === 'name'} onChange={...} />
      A–Z — "Alphabetical control"
    </label>
  </div>
  <details>
    <summary>More options...</summary>
    <label>
      <input type="radio" value="score" checked={sortBy === 'score'} onChange={...} />
      📊 Top Performers — "By financial health"
    </label>
    <label>
      <input type="radio" value="revenue" checked={sortBy === 'revenue'} onChange={...} />
      📈 Largest Orgs — "By revenue"
    </label>
  </details>
</div>
```

### Phase 2: Testing (1 hour)

**Test Case 1: Determinism**
```bash
# Run this 3 times with same seed
curl "http://127.0.0.1:5000/api/organizations?sort=random&seed=abc123&per_page=5"
# Expected: Same 5 orgs in same order every time
```

**Test Case 2: Randomness**
```bash
# Run this 3 times with different seeds
curl "http://127.0.0.1:5000/api/organizations?sort=random&seed=abc123&per_page=5"
curl "http://127.0.0.1:5000/api/organizations?sort=random&seed=xyz789&per_page=5"
# Expected: Different orgs/order
```

**Test Case 3: Session Persistence**
1. Open directory
2. Refresh page
3. Verify same 10 orgs visible (same seed persisted)

**Test Case 4: Filter Combination**
1. Select "Health" cause tag
2. Shuffle should still apply (random within health subset)
3. Click "Name A-Z", shuffle should stop

**Test Case 5: Mobile UX**
1. Tap sort dropdown on mobile
2. Verify options are readable
3. Verify no visual overflow

### Phase 3: Polish (1 hour)

- [ ] Refine sort dropdown copy ("Randomized" vs "Shuffled" vs "Explore")
- [ ] Add visual feedback when shuffle is active (emoji or highlight)
- [ ] Update accessibility labels (`aria-label="Sort by: Shuffle, currently active"`)
- [ ] Performance check: No rendering lag when shuffling 1.7M orgs
- [ ] Mobile test on real phone

---

## Decisions to Make (Founder)

### Decision 1: Is Random Default P7-Compliant?

**Question:** Does seeded random shuffle violate "no implicit ranking"?

**Analysis:**
- ✅ Randomization is fair (equal probability for all)
- ✅ Not hiding unfair sorting (explicitly labeled "Shuffle")
- ✅ Alphabetical option always available
- ✅ Same decision we approved for hidden gems (2026-07-04)

**Precedent:** Hidden gems use seeded shuffle → already approved this approach

**Recommendation:** ✅ YES, approve shuffle-default

---

### Decision 2: Should Shuffle Be Default or Opt-In?

**Option A: Default (Recommended)**
- Pro: High discovery engagement, fresh feeling every load
- Pro: Users can opt out to Name/Score anytime
- Con: Breaks expectation that A-Z is the neutral default
- Founder's 2026-07-04 call: A-Z is neutral → this changes it

**Option B: Opt-In (Conservative)**
- Pro: Doesn't break existing mental model
- Pro: Users explicitly choose discovery mode
- Con: Low uptake (people stick with default)
- Con: Doesn't solve "stale" perception

**Recommendation:** **Go with Option A** (default) because:
1. We're trying to make directory *feel* like a discovery platform
2. Users can override anytime ("I want control" → click Name A-Z)
3. Hidden gems already proved this works
4. Founder priority: "Make it fun, not stale"

---

### Decision 3: What About "Needs Support" and Other Quality Signals?

**Concern:** If we shuffle, how do we highlight good giving opportunities?

**Answer:** Separate filters + sort options
- `sort=score` → "Top Performers" (opt-in quality)
- `filter=needs_support` → "Financially vulnerable" (opt-in impact-focused)
- Combine: `sort=score&filter=needs_support` → "Well-managed small orgs needing support"

**This preserves P7:** Users can ask for quality, but it's not the default.

---

## Rollout Plan

### Week 1: Dev + Test
- Day 1: Implement core (2h) + tests (1h)
- Day 2: QA + polish (1-2h)
- Thursday: Code review + merge

### Week 2: Soft Launch
- 50% of users get shuffle-default
- 50% get A-Z (control group)
- Measure engagement for 48 hours

### Decision Point
- If engagement ↑ and no complaints: Keep shuffle-default for all
- If engagement flat or negative: Revert to A-Z

### Week 3: Full Rollout
- 100% shuffle-default
- Monitor for 1 week
- Collect user feedback

---

## Risks & Mitigations

| Risk | Mitigation | Owner |
|------|-----------|-------|
| Users expect A-Z (breaking change) | Onboarding tooltip: "Tip: Shuffle for discovery, or choose Name A-Z for alphabetical" | Frontend |
| Random feels "unpredictable" on mobile | Persist seed, show "Refresh for new shuffle" button | Frontend |
| Performance issue with 1.7M orgs | Seeded shuffle is O(n), but happens client-side (not bottleneck) | Backend |
| Accessibility: Screen reader users confused | `aria-label="Currently showing shuffled results. Switch to alphabetical to sort A-Z"` | QA |
| P7 interpretation: Seeded random is still ranking | Document decision in DECISIONS.md with P7 rationale | Claude |

---

## Success Criteria

Launch is successful if:
- [ ] Default sort = random with session seed
- [ ] Same seed produces same results (deterministic)
- [ ] Users can opt to Name/Score/Revenue anytime
- [ ] Engagement metrics show uplift (avg orgs clicked, session duration)
- [ ] No P7 violations (random = fair)
- [ ] Mobile UX is smooth
- [ ] Accessibility score unchanged

---

## Optional Enhancements (Post-Launch)

### Quick Wins (1-2 hours each)
1. **"Trending" sort** — Show recently updated orgs (requires `last_updated_at` column)
2. **Visual polish** — Icons/emoji on sort options
3. **Favorite orgs** — Persist favorited orgs to shuffle end (serendipitous re-discovery)

### Bigger Features (4+ hours each)
1. **Personalized shuffle** — "Orgs like the ones you viewed" (ML-based)
2. **"New this week" banner** — Show recent additions
3. **Seasonal themes** — "Holiday giving", "Back to school" filters

---

## Question for Founder

**One decision needed:**

> **Should the directory default load be shuffled (random, engaging) or alphabetical (neutral, boring)?**
>
> Option A: Shuffle-default (recommended, makes directory feel fresh & fun)  
> Option B: Keep A-Z default (conservative, preserves current mental model)
>
> Both options keep P7 neutrality intact. The difference is whether randomization is the *default* or *opt-in*.

**My recommendation:** Go with Option A. Founder priority is "make it fun" + "users should discover." Shuffle accomplishes both. Users can still choose A-Z if they want control.

---

## Implementation Readiness

| Component | Status | Notes |
|-----------|--------|-------|
| Seeded shuffle logic | ✅ Exists | Already in hidden gems code |
| Session seed storage | ✅ Exists | localStorage pattern proven |
| API route support | 🟡 Needs work | Add `sort=random&seed=` support |
| Frontend dropdown | 🟡 Needs work | Redesign with new options |
| Tests | 🔴 TODO | Add determinism + combination tests |
| Documentation | 🔴 TODO | Update DECISIONS.md with choice |
| QA checklist | 🔴 TODO | 5-6 test scenarios |

**Ready to start:** Yes, approval pending

---

## Files to Touch

```
Frontend Changes:
  frontend/src/pages/Directory.tsx        # Default sort logic
  frontend/src/components/SortDropdown.tsx # UI

Backend Changes:
  daanaa_api.py                          # organizations_fast() seeded shuffle
  scripts/droplet_api.py                 # Same (parity)
  droplet_api.py (if on droplet)         # Same

Testing:
  tests/test_search_quality.py           # Add shuffle determinism tests
  QA_CHECKLIST.md                        # Add shuffle test scenarios

Documentation:
  DECISIONS.md                           # Log the decision
  UX_AUDIT_DIRECTORY_2026_07_24.md      # (reference, already created)
```

---

## TL;DR

**Current:** Directory loads alphabetically (stale, not engaging)  
**Proposed:** Default load is seeded-random (engaging, fair)  
**Time:** 4 hours  
**Risk:** Low (existing seeded shuffle code, just change default)  
**P7 Impact:** None (random is neutral)  
**Engagement Impact:** High (users explore more, feel discovery)  
**Founder Decision Needed:** Shuffle-default or keep A-Z?

**My Call:** Shuffle-default aligns with "make it fun" directive. Approval + 4-hour sprint = live by Friday EOD.
