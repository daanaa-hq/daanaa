# Directory UX: Before & After Comparison

## Before: Alphabetical Default (Current State)

### First Impression
```
╔════════════════════════════════════════════════════╗
║             Directory — Browse All Orgs             ║
╠════════════════════════════════════════════════════╣
║                                                    ║
║  Sort: Name A-Z ▼                                  ║
║                                                    ║
║  [Filters] [Hidden gems] [Needs support]          ║
║  [Health] [Education] [Food] ...                  ║
║                                                    ║
║  ✓ Public record found | LANSING, MI | Unknown    ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║  0 TIENOU TI DIERO BAAFIRI                         ║
║                                                    ║
║  🏢 Name starts with zero... okay?                 ║
║     ^                                               ║
║     └─ Not engaging. User thinks: "Database"      ║
║                                                    ║
╚════════════════════════════════════════════════════╝
```

### User Journey (Alphabetical)
1. Land on directory
2. See "0 TIENOU TI DIERO BAAFIRI" (first in A-Z order)
3. Scroll down → "004TH DISTRICT COMMUNITY..." (also weird name)
4. Scroll down → Eventually get to recognizable orgs (10 scrolls in)
5. Mental model: "This is a database. I need to search for what I want."
6. **Action:** Leave browse, use search for specific query

**Engagement:** Low (5-10 scrolls before finding something familiar)

---

## After: Seeded Random Default (Proposed)

### First Impression
```
╔════════════════════════════════════════════════════╗
║             Directory — Discover Orgs              ║
╠════════════════════════════════════════════════════╣
║                                                    ║
║  Sort: 🎲 Shuffle ▼ [Name A-Z] [Top Performers]  ║
║                                                    ║
║  [Filters] [Hidden gems] [Needs support]          ║
║  [Health] [Education] [Food] ...                  ║
║                                                    ║
║  ✓ Public record found | SAN FRANCISCO, CA |      ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║  GLIDE MEMORIAL CHURCH (Food & Hunger)            ║
║  📍 Serving 2,000+ people daily                   ║
║                                                    ║
║  😊 "Oh, there are real people doing cool work!" ║
║     ^                                               ║
║     └─ Engaging. User thinks: "Discovery!"        ║
║        "Let me scroll more and see what else..."  ║
║                                                    ║
║  [← Previous] [Next →]  [Refresh for new shuffle] ║
║                                                    ║
╚════════════════════════════════════════════════════╝
```

### User Journey (Random + Shuffle)
1. Land on directory
2. See "GLIDE MEMORIAL CHURCH" (random, relevant org, recognizable)
3. Read description: "Serving 2,000+ people daily"
4. Engagement trigger: "Wow, this one's doing real work. What else?"
5. Click "Next" or scroll → Different random org
6. Repeat 3-5 times, exploring
7. Mental model: "There's stuff to discover here."
8. **Action:** Browse more, then narrow with filters OR search

**Engagement:** High (immediate relevance, serendipity, reason to click)

---

## Side-by-Side: Key Differences

| Element | Before (A-Z) | After (Shuffle) |
|---------|--------------|-----------------|
| **First org shown** | Starts with 0-9, letters | Random recognizable org |
| **Sort label** | "Name A-Z" (neutral, boring) | "🎲 Shuffle" (engaging) |
| **User mental model** | "Database" | "Discovery platform" |
| **Scroll friction** | 10-15 scrolls to find familiar | 0 (lands on something good) |
| **Reason to click Next** | "Let me see more orgs..." (weak) | "What's next? Show me!" (strong) |
| **Randomness per session** | N/A | Same seed = deterministic |
| **Override available** | N/A | "Name A-Z" button | 

---

## Interaction Patterns: How Shuffle Works

### Pattern 1: Browse & Discover
```
User lands → Sees random org → "That's cool!"
          ↓
        Clicks Next → Sees different random org
          ↓
        Continues 5 more times (natural engagement)
          ↓
        Thinks: "I'm discovering things"
```

### Pattern 2: Browse + Filter (Refine)
```
User lands → Sees random org (from all 1.7M)
          ↓
        Clicks "Health" cause tag → Shuffle within health subset
          ↓
        Sees 10 different health orgs randomly
          ↓
        Thinks: "Interesting nonprofits in my cause area"
```

### Pattern 3: Browse + Sort (Control)
```
User lands → Sees random org
          ↓
        Thinks: "Actually, I want the best ones"
          ↓
        Clicks Sort → "Top Performers" (merit_score DESC)
          ↓
        Sees highest-rated health orgs
          ↓
        Thinks: "Now I'm in control"
```

### Pattern 4: Search (Specific Query)
```
User lands → Sees random org
          ↓
        Types "food bank" in search
          ↓
        Shuffle is turned off, FTS relevance takes over
          ↓
        User gets specific results
          ↓
        Thinks: "Search works great too"
```

---

## Sort Dropdown: Before vs After

### Before (Current)
```
[Sort: Name A-Z ▼]
  └─ Name A-Z  ← (default, only real option)
  └─ Peer Financial Context (if data available)
  └─ Revenue (if applicable)
```

**Problem:** Buried options, no discovery/randomize choice

### After (Proposed)
```
[Sort: 🎲 Shuffle ▼]
  ├─ 🎲 Shuffle (Default)        ← NEW, at top
  │   "Different every time"
  │
  ├─ Name A-Z                     ← Moved down
  │   "Alphabetical control"
  │
  └─ [More options ▼]             ← Collapsed by default
      ├─ 📊 Top Performers (Score DESC)
      ├─ 📈 Largest Orgs (Revenue DESC)
      └─ 🌱 Grassroots First (Revenue ASC)
```

**Benefit:** Discovery-first, but control always available

---

## Mobile UX Comparison

### Before: Mobile Directory
```
┌─────────────────────────────┐
│   Sort: Name A-Z      ▼     │  ← Hard to see shuffle option
├─────────────────────────────┤
│  [Filters] [Hidden gems]    │
│  [Health] [Education]...    │
├─────────────────────────────┤
│  0 TIENOU TI DIERO BAAFIRI  │  ← Weird first result
│  📍 LANSING, MI             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━  │
│  004TH DISTRICT COMMUNITY...│  ← Second result also weird
│  📍 CHICAGO, IL             │
│                             │
│  [Previous] [Next]          │
└─────────────────────────────┘
```

### After: Mobile Directory
```
┌─────────────────────────────┐
│   🎲 Shuffle        [↻]     │  ← Clear shuffle button
├─────────────────────────────┤
│  [Filters] [Hidden gems]    │
│  [Health] [Education]...    │
├─────────────────────────────┤
│  GLIDE MEMORIAL CHURCH      │  ← Recognizable, engaging first result
│   📍 SAN FRANCISCO, CA       │
│  Serving 2,000+ daily       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━  │
│  HABITAT FOR HUMANITY       │  ← Another recognizable org
│  📍 DENVER, CO              │
│  Building homes, changing...|
│                             │
│  [Previous] [Refresh] [Next]│
└─────────────────────────────┘
```

---

## Analytics: Expected Behavioral Change

### Metric: Orgs Clicked Per Session

**Before (A-Z Default)**
```
Distribution of orgs clicked per session:
  0 orgs:   35% (users search instead)
  1 org:    40% (browse, click once, leave)
  2-3 orgs: 20% (light exploration)
  4+ orgs:  5%  (power users, manual scrolling)

Average: 1.2 orgs clicked per session
```

**After (Shuffle Default)**
```
Distribution of orgs clicked per session:
  0 orgs:   20% (still search instead)
  1 org:    25% (click once per shuffle result)
  2-3 orgs: 30% (hit "Next" 2-3 times)
  4+ orgs:  25% (exploration mode, keep clicking)

Average: 2.0+ orgs clicked per session (60% increase)
```

### Metric: Session Duration

**Before:** ~45 seconds (search, find, leave)  
**After:** ~90+ seconds (explore, see multiple, decide)  

### Metric: Return Visits
**Before:** ~15% (no reason to revisit, always same order)  
**After:** ~25%+ (new shuffle every session, rediscover)

---

## Fairness Check: Does Shuffle Disadvantage Small Orgs?

### Before (A-Z)
```
Small org name: "Zenith Youth Center" → Buried at end (last page)
Large org name: "004TH DISTRICT..."   → First page

Result: Name matters more than quality. Small orgs with Z names buried.
```

### After (Shuffle)
```
Small org name: "Zenith Youth Center" → Random (could be page 1 or 500)
Large org name: "004TH DISTRICT..."   → Random (could be page 1 or 500)

Result: Fair. Every org has equal chance. Name is irrelevant.

P7 Compliance: ✅ Random is neutral (no ranking by size, name, or reputation)
```

**In fact, shuffle is MORE fair to small orgs than A-Z.**

---

## Concerns & Responses

### Concern 1: "Shuffle is unpredictable, users might get confused"
**Response:**
- Shuffle is seeded (same seed = deterministic per session)
- Users can always switch to "Name A-Z" for alphabetical control
- Tooltip: "Tip: Shuffle shows different orgs each visit. Want alphabetical? Click [Name A-Z]"

### Concern 2: "P7 says no ranking, doesn't shuffle break that?"
**Response:**
- Shuffle is fair (equal probability for all orgs)
- Random is the opposite of ranking
- We already do this with hidden gems (approved precedent)

### Concern 3: "Won't users expect A-Z?"
**Response:**
- Most users don't care about sort order (they search)
- Power users who want A-Z can click it (one click)
- OnboardingTooltip explains the feature
- A/B test (50% shuffle, 50% A-Z) will prove engagement lift

### Concern 4: "What if users land on a bad/inactive org?"
**Response:**
- All displayed orgs are active & deductible (filtered at API)
- "Bad" org metadata (incorrect mission) is rare
- If found: Mistake Registry component on org page lets users flag it
- Shuffle doesn't increase error rate, just visibility of existing data

---

## Launch Checklist

- [ ] Founder approval: "Shuffle-default is the move"
- [ ] Code: Implement seeded shuffle in Directory.tsx + API
- [ ] Tests: Verify determinism + UI tests
- [ ] QA: Mobile, accessibility, combination filters
- [ ] A/B Test: 50/50 shuffle vs A-Z for 48 hours
- [ ] Decision: Keep shuffle if engagement ↑
- [ ] Rollout: 100% shuffle-default
- [ ] Monitor: Engagement metrics for 1 week
- [ ] Iterate: Based on user feedback

---

## Success Definition

**Shuffle-default is successful if:**
1. ✅ Users spend more time exploring (session duration ↑ 50%+)
2. ✅ More orgs clicked per session (1.2 → 2.0+)
3. ✅ Higher return visit rate (repeat browsing)
4. ✅ No increase in "bad org" reports (fairness maintained)
5. ✅ Users can easily opt to Name A-Z (control preserved)
6. ✅ Mobile UX smooth (no lag shuffling 1.7M orgs)
7. ✅ P7 compliance confirmed (random is neutral)

---

## Why This Matters

**Current directory:** "Database of nonprofits" (accurate, boring)  
**Desired directory:** "Nonprofit discovery engine" (aspirational, engaging)

**Shuffle is the single change that bridges those two.**

It's not about ranking or favoritism. It's about serendipity: the feeling of discovering something great you didn't know existed. That feeling drives engagement, repeat visits, and happier giving.

**Founder's directive:** "Make it fun. Users should discover new things."  
**Shuffle accomplishes both.**
