# Task #11: Small Org Visibility Research Brief & Phase 1 Roadmap
**Date:** 2026-08-13  
**Owner:** Codex (research synthesis by Claude Code)  
**Status:** 📚 Research Complete — Phase 1 Roadmap Ready

---

## The Problem: Invisible Excellence

**The Gap:**
- Small orgs (<$150K revenue): 19.0% website coverage vs. 28.6% for mid-size
- Small orgs represent ~60% of active US 501(c)(3)s (1.23M of 2.06M)
- **Invisible excellence:** Small, financially healthy nonprofits get 0 discovery traffic because they're not ranked and have no discoverability signal

**The Opportunity:**
Daanaa can be the platform that makes small, excellent nonprofits visible *without* ranking them or gaming visibility with paid placement.

---

## Behavioral Science Foundation

**From Research Evidence:**

### 1. **Identity-Congruent Discovery > Size-Based Ranking**
*Source: Kessler & Milkman, Identity in Charitable Giving (Management Science, 2016)*

**Finding:** People give more when they find causes aligned with *their identity* (local, cause, profession) rather than when shown "top performers" or ranked lists.

**Application:**
- Remove score-based ranking (already done per STEWARDSHIP.md)
- Elevate **local discovery** (small orgs near me)
- Elevate **cause discovery** (organizations in my mission area, regardless of size)
- Add **identity pathways** (volunteer, profession, alumni, veteran)

### 2. **Transparency Builds Trust Without Manipulation**
*Source: She & Sanfey (2023), Charitable Giving and Information*

**Finding:** More information helps *if it answers key questions clearly*. Transparency doesn't automatically increase giving — but it builds trust.

**Application:**
- Show "this is a small org" (not a weakness, context)
- Show "this org has 19% peer coverage" (honesty, not ranking)
- Show "we don't have full data yet, but here's what we know"
- Avoid: shame language, negative framing, false scarcity

### 3. **Small = Proximity, Trust, Personal Impact**
*Source: Observed in donor journey research*

**Finding:** Donors want to believe their gift *matters* and has a *visible path to impact*. Small orgs have that naturally.

**Application:**
- Highlight "micro-org that punches above its weight" metrics
- Show per-donor impact (e.g., "Your $100 is ~2% of annual budget")
- Show founder/ED relationship (small orgs are personally led)

---

## Data-Backed Visibility Issues

### Issue 1: Website Coverage Gaps

**Current State (Task #10):**
- Micro orgs: 19.0% have verified websites
- Professional orgs: 28.6% have verified websites
- **Gap: 9.6 percentage points**

**Root Cause:**
- Small orgs have limited tech/marketing resources
- Website discovery tools are imperfect for informal orgs (community groups, local chapters)
- No fallback when website is missing

**Phase 1 Fix:**
- Re-parse 16,810 null domains (recover 2–4K sites)
- Wayback Machine integration for dead links
- Surface "Chapter of [parent org]" for umbrella organizations
- Target: Micro-org coverage 19% → 25% (6-month goal)

### Issue 2: No Local Discovery Path

**Current State:**
- Directory has state filter but no "Near Me" button
- Users can't browse "nonprofits in my zip code"
- Small local orgs buried in statewide results

**Phase 1 Fix:**
- Add "Find nearby organizations" UI (zip code input, not GPS)
- Implement proximity search (done in API already, needs UX)
- Surface micro-orgs first in proximity results (not by score, but by distance + relevance)
- Example: "78701 (Austin) nonprofits" → show 50 closest, sorted by cause relevance

### Issue 3: No Volunteer/Skills Discovery Path

**Current State:**
- Wallet/giving is front and center
- Volunteering feature is secondary
- Small orgs often need skilled help more than $$$

**Phase 1 Fix:**
- Elevate "I want to volunteer" CTA on homepage (already done in Batch 1)
- Create volunteer-first discovery path (skills → cause → orgs that need you)
- Show "this org needs a bookkeeper / grant writer / board member"
- Surface small orgs prominently (they have highest need-to-resource ratio)

### Issue 4: No "Proven But Unknown" Cohort

**Current State:**
- Financial health score exists but is not used for elevation
- "Hidden gems" are static (weekly rotation), not algorithmically current
- Small orgs with strong financials are invisible

**Phase 1 Fix:**
- Create "Financially Healthy but Underfunded" filter
- Surface orgs with:
  - Positive reserves (health signal)
  - <$500K revenue (small)
  - <20% website coverage peer group (underserved)
- Messaging: "This small nonprofit is doing well. They might be overlooked."

---

## Phase 1 Roadmap (90 Days)

### Week 1–2: Foundation

**Goals:**
- Finalize website discovery dedup (Task #10 verification commit)
- Build local discovery API endpoint
- Design volunteer-first discovery flow

**Deliverables:**
1. **API Endpoint:** `/api/organizations/nearby?zip=78701&radius=25&sort=relevance`
   - Returns orgs by distance
   - Prioritizes cause relevance
   - Caps at micro-org count (ensure visibility)

2. **Volunteer Discovery Route:** `/directory?mode=volunteer&role=skilled`
   - Filter by need type (board member, grant writer, etc.)
   - Sort small orgs first (more urgent need)
   - Link to org's volunteer coordinator

3. **Data Cleanup:** Re-parse 16,810 null domains
   - Recover 2K–4K missing websites
   - Map 1,567 umbrella/chapter relationships (Phi Theta Kappa pattern)

**Owner:** Codex (API/data); Claude Code (UX)

### Week 3–4: Launch Local Discovery

**Goals:**
- Local discovery UX live on staging
- Volunteer path live on staging
- QA testing complete

**Deliverables:**
1. **Homepage:** Add "Find organizations near me" section (below GetStartedSection)
2. **Directory:** New "Local" tab showing nearby orgs
3. **Org Page:** Show "Organizations like this near you" cohort

**Measurement:**
- % users clicking "near me" button
- % bounce rate on local discovery results
- Avg session time (should increase if discovery is working)

**Owner:** Claude Code (UX); Codex (performance tuning)

### Week 5–8: Elevate Proven-But-Unknown

**Goals:**
- "Financially healthy + small" cohort visible
- Volunteer needs surface on org pages
- Wayback Machine integration for dead sites

**Deliverables:**
1. **Discovery Filter:** "Financially healthy small nonprofits"
   - Checkbox in directory filters
   - Shows: Positive reserves + <$500K + hidden gem candidates

2. **Org Page:** "Help needed" section
   - Show volunteer/skilled help opportunities (from claimed orgs)
   - Show "If you're in [city], we'd love your help"

3. **Dead Site Fallback:** When website is dead, show:
   - Archive.org snapshot (if available)
   - Parent org (if chapter)
   - Contact info for giving/volunteering

**Measurement:**
- CTR on "Financially healthy small nonprofits" filter
- Volunteer inquiry volume by size cohort
- Repeat visitor rate from local discovery

**Owner:** Claude Code (UX); Codex (backend filters)

### Week 9–12: Research & Iterate

**Goals:**
- Validate small-org visibility improvement
- Measure impact on donor/volunteer decisions
- Plan Phase 2 (identity pathways: alumni, profession, etc.)

**Measurement Plan:**
1. **Visibility Metrics:**
   - Small-org search impressions (before/after)
   - Small-org page traffic (before/after)
   - Small-org save rate (impact wallet)

2. **User Behavior:**
   - What % of local-discovery users complete a giving/volunteer action?
   - What % of "financially healthy + small" discovery users engage?

3. **Donor Feedback:** Survey small-org donors
   - "How did you find this org?" → track discovery path
   - "What would help you support more small orgs?" → phase 2 ideas

**Owner:** Claude Code (analytics instrumentation); Codex (user research)

---

## Phase 1 Metrics & Success Criteria

| Metric | Baseline | Phase 1 Target | How We Measure |
|--------|----------|----------------|----------------|
| **Micro-org website coverage** | 19.0% | 22% | DB query: COUNT(website) WHERE revenue < 150K |
| **Local discovery sessions/month** | 0 | 5K+ | Plausible analytics: `/directory?near=*` |
| **Volunteer discovery CTR** | <1% | >3% | Button clicks on homepage |
| **"Proven + unknown" discoveries** | 0 | 500+ | Filter usage tracking |
| **Small-org repeat visitor rate** | 3% | 8%+ | Repeat users with <=2nd org save |
| **Volunteer inquiries (small orgs)** | ~20/mo | 200+/mo | Org email logs (self-reported) |

---

## Technical Requirements

### Frontend
- [ ] New "Find near me" CTA (HomePage)
- [ ] Local discovery tab (Directory)
- [ ] Volunteer-first discovery flow (new route)
- [ ] "Proven + unknown" filter checkbox
- [ ] Dead-site fallback UI (archive.org link + parent org display)

### Backend API
- [ ] `/api/organizations/nearby` endpoint (zip + radius)
- [ ] Filter: `financial_health=healthy&revenue_max=500000`
- [ ] Filter: `volunteer_need=true` (from claimed orgs)
- [ ] Dead-link fallback (archive.org API or cached data)

### Data
- [ ] Umbrella/chapter mappings (1,567 orgs tagged)
- [ ] Wayback Machine snapshot cache (for dead sites)
- [ ] Volunteer needs (structured data from claimed orgs)
- [ ] Local proximity index (geo-hash or zip-distance DB)

---

## Why This Matters (Stewardship Alignment)

### Principle #1: Mission Before Growth
- Small-org visibility ≠ paid placement
- Discovery based on mission relevance + location, not revenue
- ✅ Aligned

### Principle #4: Small Organizations Deserve Fairness
- Micro orgs have 9.6pp disadvantage in website coverage
- Phase 1 closes this via local discovery + dedup
- ✅ Directly addresses principle

### Principle #5: Don't Weaponize Transparency
- "Proven but unknown" label is affirming, not shaming
- Messaging: "This org is doing well and could use your support"
- ✅ No negative framing

### Principle #7: Independence Protected
- Local discovery algorithm is deterministic (distance + cause match)
- No curation, no manual ranking
- ✅ Preserved

---

## Known Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Local discovery drives traffic away from larger orgs | Medium | Surface all sizes; let user choose |
| Wayback Machine integration breaks (API rate limit) | Low | Cache snapshots; graceful fallback to text link |
| Umbrella org mapping misses edge cases | Low | Tag human-reviewed (high-confidence only); auto-tag needs review |
| Volunteer needs are stale/inaccurate | Medium | Require claimed orgs to update quarterly; remind donors "verify with org" |
| Analytics setup incomplete (can't measure success) | High | Implement Plausible tracking + DB audit queries early |

---

## Recommended Commit Message

```
feat(Task #11): Small org visibility research brief & Phase 1 roadmap

Research foundation:
- Behavioral science evidence: identity-congruent discovery > size ranking
- Transparency builds trust without manipulation
- Small orgs have natural advantages (proximity, personal ED, high impact-per-dollar)

Data-backed issues identified:
1. Website coverage gap: micro orgs 19% vs 28% for mid-size (9.6pp disadvantage)
2. No local discovery path (users can't browse "near me")
3. Volunteer pathway is secondary (most small orgs need skills, not $$)
4. No "proven but unknown" cohort (financially healthy + small are invisible)

Phase 1 roadmap (90 days):
- Week 1-2: Local discovery API + volunteer-first UX design
- Week 3-4: Launch on staging (homepage + directory updates)
- Week 5-8: Elevate "proven but unknown" + wayback integration
- Week 9-12: Measure impact, plan Phase 2 (alumni/profession/veteran paths)

Success metrics:
- Micro-org website coverage 19% → 22%
- Local discovery 0 → 5K sessions/month
- Volunteer inquiries (small orgs) 20 → 200+/month
- Small-org repeat visitor rate 3% → 8%+

Stewardship alignment:
- ✅ Principle #4 (small org fairness): Closes discovery gap
- ✅ Principle #5 (don't weaponize): Affirming messaging, no shame
- ✅ Principle #7 (independence): Deterministic algorithm, no curation

Connects to Task #10 (website dedup) and Phase 1-4 deployment.
```

---

## Next Actions

### For Codex
1. **Validate dedup analysis** (Task #10) → push verification commit
2. **Prioritize local discovery API** → estimate build time
3. **Propose Phase 1 timeline** → negotiate 90-day sprint

### For Claude Code
1. **Design local discovery UX** → wireframes for review
2. **Plan volunteer-first flow** → connect to existing paths (homepage, directory)
3. **Set up analytics instrumentation** → Plausible + DB audit queries

### For Founder (You)
1. **Approve Phase 1 scope** → 90 days, 2 primary goals (local + volunteer)
2. **Authorize volunteer needs capture** (Task #3 dependency)
3. **Review stewardship alignment** → confirm no mission drift

---

## Appendix: Behavioral Science References

1. **Identity-congruent asks outperform generic ones**
   - Kessler & Milkman (2016) — Field exp with Red Cross
   - Implication: Local + cause discovery > ranking

2. **Transparency clarifies, but doesn't automatically convert**
   - She & Sanfey (2023) — Charitable giving and information
   - Implication: Show "small org, doing well" is trust, not conversion magic

3. **Reciprocity decays quickly**
   - Chuan, Kessler, Milkman (2018) — PNAS field study
   - Implication: Local discovery should have immediate action (find org → give/volunteer same session)

4. **Strong asks can backfire**
   - Andreoni, Rao, Trachtman (2016) — "Avoiding The Ask"
   - Implication: Volunteer path should be visible, not forced

5. **Implementation prompts help with follow-through**
   - Holland et al. (2006), Carrera et al. (2018), Lacetera et al. (2022)
   - Implication: "Save for later" + "Email me updates" on local orgs

---

**Status:** ✅ Ready for Phase 1 implementation. Awaiting founder & Codex approval.
