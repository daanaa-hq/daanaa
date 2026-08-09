# Small Org Clarity Strategy — Enrichment ≠ Extraction

**Discovery (2026-08-09):** We don't need NEW data sources to improve small org representation. We need to **surface existing data more clearly**.

## Problem Definition

**Status quo:** Small nonprofits on Daanaa are "invisible" not because we lack data, but because:
1. Leadership/stability signals are buried (ED tenure, board size hidden in 990 columns)
2. Service area is vague (NTEE + state, but not "I serve these 3 specific populations")
3. Org size/scope is unclear (revenue alone doesn't convey reach)
4. Mission statements are generic (AI-extracted, not org voice)

**Root cause:** We have the data. We're just not displaying it in a way that makes small orgs **obviously credible**.

## Exploration Results

### Path A: ProPublica Schedule O (Program narratives)
- **Coverage:** ~22% of active 501(c)(3)s (only established orgs file)
- **Result:** Not viable for small org enrichment by definition
- **Lesson:** Rich data exists, but only for orgs that are already visible

### Path B: Website Program Extraction
- **Scope:** Scrape /programs pages + LLM extraction
- **Result:** Most small org websites don't have clean /programs pages (JS-heavy, redirects, embedded)
- **Lesson:** Extraction adds complexity for minimal coverage gain

## The Real Strategy

**Visibility improves via display + context, not data collection.**

### Phase 3.5: Data Display Enhancement (High ROI, Low Effort)

**1. Leadership Clarity (already have data)**
- Extract + surface: ED name, ED tenure, board size, board composition
- Why: Shows organizational stability and continuity
- Source: Form 990 Part VII (compensation), Part VIII (governance)
- Display: Org detail page "Leadership" section

**2. Service Area Clarity (improve what we have)**
- Extract + surface: Primary service geography, population served, program count
- Why: Shows focus and reach without full program extraction
- Source: NTEE classification + extracted metadata (service_area_states) + 990 Schedule O if available
- Display: Org detail page "Scope" section

**3. Mission Voice (use existing extraction, improve presentation)**
- Current: AI-extracted mission statements (generic)
- Better: Surface org's own mission language (from website /about page)
- Why: Donor connection to org intent, not algorithm output
- Source: We already extract from /about; just need better UI display

**4. Org Type/Size Signals (crystallize existing scoring)**
- Current: v6 scoring (tier + confidence), but not prominently displayed
- Better: Show "Small but mighty" signal for high-performing small orgs (Stewardship P4)
- Why: Donors see at a glance: "This org is small + stable + effective"
- Source: Existing v6 context, peer group rank

### Phase 3.5 Implementation (2-3 days)

**Backend changes (API):**
- Add to org response: `leadership` (ED info), `service_scope` (area + population), `org_health_signal` (v6 scoring translated to language)
- Update existing: `mission` display to prefer extracted org voice over AI summary

**Frontend changes (org detail page):**
- New sections: "Leadership", "Scope", "Stability"
- Restructure: mission first (with source attribution), then "The org at a glance" (size + type + health)
- Visual treatment: Small org = bold, trusted

### Measurement (Post-Deploy)

- **Week 1:** CTR on small org cards vs. large org cards (should flatten)
- **Week 2:** Org detail page time-on-page for small vs. large orgs
- **Week 3:** Donation likelihood via wallet bookmarks (proxy: more bookmarks = better discovery)

---

## Why This Works (Stewardship Aligned)

- **P1 (Mission before growth):** We're not adding features to drive engagement; we're clarifying what small orgs actually do
- **P3 (Evidence-based):** All displayed data comes from official 990 filings or org websites — no interpretation
- **P4 (Small org fairness):** Explicitly surfaces small org strengths (stability, focus) that scoring alone doesn't convey
- **P5 (No weaponized transparency):** We're building UP small orgs, not comparing them down
- **P6 (Honest mistakes):** Each field is attributed to source (990 filing year, extracted date, confidence)

---

## Deferred (out of scope for this cycle)

- Complex program extraction (Scrapy + JS + LLM = high complexity, low small-org coverage)
- Volunteer event feeds (too newsy, Stewardship P5 concern)
- Social proof aggregation (violates P2 privacy principle)

**Focus:** Representation via clarity, not novelty.
