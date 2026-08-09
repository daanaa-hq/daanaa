# Data Coverage Gaps & Transparency Framework (2026-07-26)

## 📋 Pages Affected (Showing Financial Data/Coverage)

**Core pages displaying org scores/financial data (9 pages):**
- `frontend/src/pages/OrganizationDetail.tsx` — org detail pages (2.06M orgs) — PRIMARY
- `frontend/src/pages/Directory.tsx` — search results with scores
- `frontend/src/pages/CategoryPage.tsx` — category filtering + scores
- `frontend/src/pages/Methodology2.tsx` — methodology & explanation — PRIMARY
- `frontend/src/pages/ResearchDashboard.tsx` — research/stats overview
- `frontend/src/pages/WalletPage.tsx` — donor wallet (shows bookmarked org data)
- `frontend/src/components/V5Context.tsx` — financial context component
- `frontend/src/components/FinancialContext.tsx` — score display
- `frontend/src/components/OrgInfoHierarchy.tsx` — org info display (recently added)

**Secondary pages displaying org data/stats (11 pages — added per sitemap audit):**
- `frontend/src/pages/ComparePage.tsx` — side-by-side comparison of multiple orgs + scores
- `frontend/src/pages/CauseSpotlight.tsx` — featured org rotation + scores
- `frontend/src/pages/OpenData.tsx` — data exports, org counts, aggregated statistics
- `frontend/src/pages/SectorHealth.tsx` — sector-level analytics, org distribution by tier
- `frontend/src/pages/TiersPage.tsx` — tier system explanation + tier distribution charts
- `frontend/src/pages/NonprofitDashboard.tsx` — org admin dashboard showing their own data + peer context
- `frontend/src/pages/OrgClaimEditor.tsx` — org claim editing, displays org financial data for verification
- `frontend/src/pages/PartnerDetail.tsx` — partner profile, may display org counts/stats
- `frontend/src/pages/GuildPage.tsx` — guild/community page, may display org counts
- `frontend/src/pages/VolunteerDiscoveryPage.tsx` — volunteer search, may show org/event data
- `frontend/src/pages/VolunteerSearch.tsx` — volunteer search results, org/event display
- `frontend/src/pages/DonationReceipt.tsx` — post-donation confirmation, shows confirmed org

**Will need new components:**
- `CoverageVisualization.tsx` (5 new charts for Methodology page)
- `ConfidenceBadge.tsx` (show confidence level on every score)

---

**Principle:** Stewardship #3 (Evidence-based) + #6 (Mistakes corrected quickly) require honest accounting of what we can and cannot confidently say about orgs.

---

## Coverage Summary (2.06M orgs)

| Data Layer | Available | % | Gap | Gap % |
|------------|-----------|---|-----|-------|
| **Mission statement** | 2.05M | 99.8% | 3.6K | 0.2% |
| **Archetype (funding model)** | 1.72M | 83.5% | 340K | 16.5% |
| **Revenue band** | 372K | 18.1% | 1.68M | **81.9%** |
| **Financial health signal** | 372K | 18.1% | 1.68M | **81.9%** |
| **Financial ranking** (direct) | 368K | 17.9% | 1.69M | 82.1% |
| **NTEE-only ranking** | 270K | 13.1% | — | — |
| **No ranking at all** | 1.42M | 68.9% | — | — |
| **Website verified** | 89K | 4.3% | 1.97M | **95.7%** |
| **Donate link verified** | 59K | 2.9% | 1.99M | **97.1%** |

---

## Critical Gaps (P3: Evidence-Based Honesty)

### 1. **Revenue Band Data (81.9% Missing)**
**What we can say:** Only 372K orgs have confirmed revenue band data
- Micro (<$150K): 148K confirmed
- Professional ($150K–$700K): 111K confirmed
- Established (>$700K): 114K confirmed

**What we CANNOT say:** "This org is a micro nonprofit" unless we have actual 990 data
- For 1.68M orgs, revenue is unknown, making fair peer comparison impossible

**Impact:** Small orgs (likely the 1.68M without data) cannot be compared fairly against peer group
- **Fairness risk (P4):** We may penalize small orgs for "missing data" when in reality they simply lack filed 990s

**Fix:** Display band data only when available; offer "We don't yet know their revenue" message (not shame)

---

### 2. **Financial Health Signals (81.9% Missing)**
**What we can say:** 183K orgs are HEALTHY, 168K CAUTION, 22K STABLE (based on 990 data)

**What we CANNOT say:** "This org is unstable" for the 1.68M without 990s
- Our silence is correct; assuming they're unstable would be evidence-free

**Impact:** Scoring pages must show confidence level, not just a number
- Confidence pyramid: High (18.1%) → Medium (13.1% NTEE-only) → Low/None (68.9%)

**Fix:** "We have direct financial data for [X%] of similar orgs" with explicit confidence banner

---

### 3. **Direct Financial Data (68.9% Have No Ranking)**
**Breakdown of the 1.42M with no data:**
- No recent 990 filed (most common)
- No IRS registration (dormant or <$50K threshold)
- Too new to have filed
- IRS data hasn't been published yet (lag)

**Implication for Scoring:**
- We can rank 368K by direct data (peer_percentile)
- We can rank 270K by NTEE category only (weaker signal)
- 1.42M get NO algorithmic ranking (correct choice, not a bug)

**Our v6 tier system helps here:**
- v6_inference: "archetype_only" vs. "regional_inferred" vs. "direct_data"
- confidence_v6: "high", "good", "moderate", "archetype_only"

**Fix:** Always show inference type: "Based on [type], we estimate..."

---

### 4. **Website Verification (95.7% Missing)**
**Verified websites:** 89K (4.3%)
**Implications:**
- Cannot verify mission from web scraping for 1.97M orgs
- AI missions become primary source for discovery

**For Giving Paths:**
- Only 59K (2.9%) have verified donate links
- For remaining 2M, we offer DAF/EIN fallback (private, verified, bank-based)

**Fix:** Be transparent: "Link verified from their website" vs. "No website found; use DAF by EIN instead"

---

## Stewardship Alignment Plan

### P3 (Evidence-Based): What to Show
✅ **Always display:**
- Confidence level (high/good/moderate/archetype-only)
- Data source + age ("2023 990 filing" vs. "estimated from NTEE peers")
- "We don't yet know" rather than silence

❌ **Never display:**
- A number without confidence bounds
- A ranking without showing how many peers have actual data
- Missing data as a judgment on the org

### P4 (Small Org Fairness): What to Change
**Current risk:** Small orgs (likely the 1.68M without revenue band data) look "incomplete"

**Fix:** Reframe in UI:
- "Small organizations often haven't filed recent 990s yet. That doesn't mean they're not great."
- Show actual peer group size: "Compared to 47 similar education nonprofits"
- Link to methodology: "How we handle missing data"

### P6 (Mistakes Corrected): What to Monitor
- Flag orgs with confidence = "archetype_only" for manual review when they appear in top results
- Alert if inference becomes wrong after actual 990 is filed
- Surfaces corrections path (Mistake Registry)

---

## Implementation Roadmap

### Phase 1: Audit Pages (This Week)
- [ ] Methodology2.tsx — Add confidence bands to all score explanations
- [ ] V5Context.tsx — Show "based on [data source]" attribution
- [ ] OrgInfoHierarchy.tsx — Add confidence disclaimer for each field
- [ ] Org detail page — Show which tier has "high", "moderate", "low" confidence

### Phase 2: Update Copy (Next Week)
- [ ] Remove "incomplete data" language → "we're still learning"
- [ ] Add confidence icons (✓ verified, ≈ estimated, ? unknown)
- [ ] Update methodology page with coverage percentages

### Phase 3: Expose v6 Confidence (This Sprint)
- [ ] API returns confidence_v6 + confidence_margin_v6
- [ ] Frontend displays confidence slider: High ←→ Low
- [ ] Search results sorted by: Relevance + Confidence

---

## Public Transparency Statement (for charter/about page)

**From Stewardship Charter:**

> "If evidence is weak, incomplete, outdated, or uncertain, we must clearly say so."

**Our current honest state:**
- 18% of orgs: We have direct financial data (high confidence)
- 13% of orgs: We have peer-group ranking only (moderate confidence)
- 69% of orgs: We have no financial data (we show mission + contact only)

**What this means:**
- Small and young nonprofits are often in the 69% group. This is not a sign of weakness — it's because they haven't filed a 990 yet.
- When we show a score, we always tell you how confident we are.
- Missing data doesn't make an org incomplete. It makes it honest.

**Your donation path doesn't depend on our scoring:**
- All 2.06M orgs have a verified giving path (EIN-based, checked link, or both)
- Our scoring is one input; your values are the other

---

## Metrics to Track (for next audit)

1. **Coverage trend:** Is 18.1% revenue-band coverage growing? (Track monthly)
2. **IRS lag:** How old is the oldest 990 we're using? (Target: <2 years)
3. **Website crawl success:** Can we improve from 4.3% verified? (Target: 10% by Q4)
4. **Donation link verification:** Are we improving the 2.9%? (Target: 5% by Q4)
5. **User feedback:** Are people confused by confidence levels? (Monitor Mistake Registry)

---

**Owner:** Data Integrity (P3, P4, P6)  
**Status:** Documented; ready for UI implementation  
**Next:** Audit pages + update copy per Phase 1-3 roadmap
