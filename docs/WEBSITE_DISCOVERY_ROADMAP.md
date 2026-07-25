# Website Discovery Roadmap — 1M Official Sites + Missions

**Goal:** Discover official websites + mission statements for 1M nonprofits (currently 86.9K verified).

**Current state:**
- 3.5M nonprofits without discovered websites
- 86.9K with verified OK websites (24% have donation links)
- 0 mission statements extracted via official sites

**Progressive milestones (incremental delivery):**

---

## Phase A: Bootstrap Discovery (Week 1-2)
**Target: 100K → 150K websites discovered**

- Deploy `website_discovery_engine.py` hourly (8 workers, 1K batch)
- Strategy: DNS lookup + common domain patterns
- Expected rate: 200-300 websites/hour = 5K-7K/day
- **ETA:** 14-21 days to 100K

**Add mission extraction:**
- Simple version: extract `<meta name="description">` tags from discovered sites
- Fallback: extract first `<h1>` or first paragraph text
- Store in `mission`, `mission_source = 'website_meta'`

**Success metric:** 100K websites, 50K+ with mission statements

---

## Phase B: Multi-source Integration (Week 3-4)
**Target: 150K → 500K websites discovered**

Deploy `continuous_website_scraper.py` as 24/7 background service:
- 8 parallel workers (I/O-bound, runs while GPU does other work)
- Targets orgs with $100K-$1M revenue first (higher likelihood)
- Scrapes for: website, mission, donation links, volunteer info

**Add external source lookups:**
- LinkedIn organization profiles (bulk API if available)
- Facebook nonprofit pages (search + link extraction)
- GuideStar/Candid.org API (if access granted)
- Charity Navigator database (bulk export or API)

**Mission extraction enhancement:**
- Extract from "About Us" page (common pattern)
- Extract from `<title>` tag + first paragraph
- Rank sources by confidence (meta > title > paragraph)
- Store source in `mission_source`

**Success metric:** 500K websites, 300K+ with verified missions

---

## Phase C: Intelligent Prioritization (Week 5-6)
**Target: 500K → 750K websites discovered**

**Smart prioritization:**
- Rank remaining 3M by: revenue, filing recency, org type (NTEE category)
- Seed discovery with similar-org lookups (if org A found, search org B in same category)
- Use discovered donation patterns to infer missing sites (federation orgs)

**Advanced mission extraction:**
- Call local Qwen3-30B model for mission generation (fallback if no extracted text)
- Prompt: "This nonprofit's website is [URL]. Generate a 1-2 sentence mission statement based on the organization name and field."
- Mark source: `mission_source = 'ai_generated'`
- Track confidence scores

**Success metric:** 750K websites, 500K+ with human-verified missions

---

## Phase D: Scale to 1M (Week 7-8)
**Target: 750K → 1M websites discovered**

**Remaining 250K are hardest targets:**
- Small orgs (<$50K revenue), limited online presence
- Dormant/inactive filers
- Organizations in non-English-speaking areas
- Defunct but not yet delisted

**Fallback strategies:**
- State nonprofit registry cross-reference (all 50 states)
- IRS Form 990 header extraction (address-only orgs can be contacted)
- Archive.org wayback machine (defunct websites)
- Email pattern inference (if we have street address, guess contact email)

**Mission completion:**
- For remaining 250K without extracted missions: generate via AI with explicit `ai_generated` flag
- Quality gate: only mark `ai_generated` if we have >90% confidence (name + field are clear)

**Success metric:** 1M official websites + 750K+ with missions (75% coverage)

---

## Success Metrics (Rolling)

| Milestone | Websites | Missions | Donation Links | Timeline |
|-----------|----------|----------|-----------------|----------|
| Phase A | 100-150K | 50K+ extracted | 30K verified | Week 2 |
| Phase B | 150-500K | 300K multi-source | 100K verified | Week 4 |
| Phase C | 500-750K | 500K verified | 250K verified | Week 6 |
| Phase D | 750-1M | 750K verified | 350K verified | Week 8 |

---

## Implementation (Active)

**Running now (auto-restart on schedule):**
```bash
# Hour :23 every hour
python3 scripts/website_discovery_engine.py
  → 1K batch, 8 workers
  → Saves website + website_status to registry_enriched
  → Extracts <meta description> for mission_source='website_meta'
```

**Parallel (link extraction, unchanged):**
```bash
# Hour :07 every hour  
python3 scripts/blitz_efficiency_tracker.py
  → Verifies donation links from known websites
```

---

## Decision Log

**2026-07-25 — Why hourly vs. continuous?**
- Hourly = predictable, non-interfering with other jobs, easy to pause/resume
- Continuous = faster but harder to coordinate with link extraction + inference jobs
- Decision: Keep hourly, can scale to 2-hourly (every other hour) if 1M becomes unblocked

**2026-07-25 — Why mission extraction on site discovery?**
- Missions are high-signal for org credibility (Stewardship P3)
- Extracting at discovery time = one pass (cheaper than separate pass)
- AI fallback ensures 1M sites get missions (even if extracted quality is mixed)

---

## Known Unknowns

1. **Discovery rate variance** — 10-30% of searches succeed (depends on org naming clarity)
2. **Mission quality tradeoff** — Extracted missions (50% coverage) vs. AI-generated (75% but lower confidence)
3. **External API availability** — LinkedIn, GuideStar, Charity Navigator access TBD
4. **Small org online presence** — May be real floor at ~750K (smallest orgs truly have no website)

---

## Rollback Plan

If discovery rate drops <5% in Phase B:
- Pause external source integration
- Revert to DNS + domain pattern only (Phase A strategy)
- Wait for further diagnosis
- Do NOT force discovery (no fabricated websites)

