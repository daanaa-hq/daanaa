# Methodology Page Updates for Data Coverage Transparency

## 📋 Pages Affected

**Primary update location:**
- `frontend/src/pages/Methodology2.tsx` — Main methodology page (all users visit this)
  - New section: "Coverage & Confidence" with 5 visualizations
  - Updated FAQ: why 69% of orgs lack financial scores
  - Copy changes: "Data limits" section expanded
  - Copy changes: "Lamp tiers" section clarified for small orgs

**Secondary pages needing copy alignment (8 pages — expanded per sitemap audit):**
- `frontend/src/pages/About.tsx` — Add link to methodology coverage section
- `frontend/src/pages/Approach.tsx` — Emphasize "honest about data gaps"
- `frontend/src/pages/OrganizationDetail.tsx` — Show confidence badge next to every score
- `frontend/src/pages/OpenData.tsx` — Add data freshness date + confidence notes on exports
- `frontend/src/pages/SectorHealth.tsx` — Add "Data coverage by tier" section + link to methodology
- `frontend/src/pages/TiersPage.tsx` — Explain why 69% of orgs lack tier data + link to methodology
- `frontend/src/pages/ResearchDashboard.tsx` — Add "Data confidence" legend to all visualizations
- `frontend/src/pages/ComparePage.tsx` — Show confidence level for each org being compared

**Components needing creation/update:**
- `frontend/src/components/CoverageVisualization.tsx` (NEW) — 5 charts
- `frontend/src/components/ConfidenceBadge.tsx` (NEW) — Visual confidence indicator
- `frontend/src/components/V5Context.tsx` (UPDATE) — Add confidence level display

---

**Goal:** Add Stewardship #3 (Evidence-based) and #6 (Mistakes corrected) transparency to Methodology2.tsx by visualizing actual data coverage gaps.

---

## New Section: "Coverage & Confidence"

**Location:** After "Data limits" section, before "Lamp tiers"

**Narrative:**
"Every data point on Daanaa rests on what's publicly available. Here's exactly what we have, and what we don't."

---

## Visual 1: Coverage Pyramid (Confidence Levels)

**Component:** Stacked bar chart (vertical pyramid shape)

```
High Confidence (17.9%)
├─ Direct financial data: 368K orgs
│  └─ These have recent IRS Form 990 filings
│
Good Confidence (13.1%)
├─ NTEE-only ranking: 270K orgs
│  └─ No recent 990, but we can estimate from peer category
│
Low Confidence (68.9%)
└─ No ranking data: 1.4M orgs
   └─ No recent filing or below IRS reporting threshold
```

**Copy:**
"When we show a financial score or signal, we're drawing from one of three confidence levels. The pyramid shows the distribution across our 2.06M orgs."

**Implementation:** React component with three colored blocks:
- Top (17.9%, green): "High: Direct 990 data"
- Middle (13.1%, yellow): "Good: Peer-group estimate"
- Bottom (68.9%, gray): "Limited: No ranking available"

---

## Visual 2: Archetype Coverage

**Component:** Horizontal bar chart

```
Donation-Funded Programs:        ████████████████░  73.7% (1.52M)
Fee-for-Service Operators:       ██░               8.4% (172K)
Endowment-Funded Grantmakers:    █░                1.3% (28K)
Unknown Archetype:               ████░            16.5% (340K)
```

**Copy:**
"We classify 83.5% of organizations by funding model. The remaining 16.5% haven't provided enough public information yet."

**Insight callout:** "Small nonprofits often don't file complete forms, so the 16.5% unknown group is likely where many grassroots organizations live. Their silence is not weakness — it's data availability."

---

## Visual 3: Revenue Band Coverage

**Component:** Donut/pie chart split by coverage

```
Has Revenue Data (18.1%)
├─ Micro <$150K: 7.2% (148K)
├─ Professional $150K–$700K: 5.4% (111K)
└─ Established >$700K: 5.5% (114K)

Missing Revenue Data (81.9%)
└─ 1.68M orgs without recent 990
```

**Copy:**
"Only 372K of our 2.06M organizations have recent revenue information. The 81.9% gap is mostly orgs that haven't filed a Form 990 in the last 2 years."

**Why this matters (stewardship note):**
"This is exactly where small and emerging organizations live. They're not incomplete — they're often too new or too small to file. That doesn't make them less worthy of support."

---

## Visual 4: Website & Donation Link Verification

**Component:** Dual progress bars

```
Websites Found & Verified:
████░░░░░░░░░░░░░░░░░░░░░  4.3% (89K) verified
████████░░░░░░░░░░░░░░░░  ??% (?) found but status unknown
█████████░░░░░░░░░░░░░░░  95.7% no website in our index

Donate Links Verified:
███░░░░░░░░░░░░░░░░░░░░░░  2.9% (59K) verified
█████████░░░░░░░░░░░░░░░░  97.1% no verified link
```

**Copy:**
"We've verified donation links for only 2.9% of orgs. For the other 97.1%, we provide a private, bank-based fallback: give by EIN or check (which protects donor privacy and doesn't require our infrastructure)."

---

## Visual 5: Financial Health Signals (Only Where Available)

**Component:** Horizontal stacked bar (showing only the 18.1% with data)

```
Out of 372K orgs with financial data:
HEALTHY: █████████████  49% (183K)
CAUTION: ████████████   45% (168K)
STABLE:  ████           6% (22K)

Note: This represents only the 18.1% of orgs with direct financial data.
The remaining 81.9% are not scored to avoid false confidence.
```

**Copy:**
"When we can calculate a financial health signal, about half show strong reserves and half show tighter margins. This distribution only includes the 372K organizations with recent filings."

---

## New FAQ Entry

**Q: Why don't all organizations have a financial score?**

**A:** Financial scores require recent IRS Form 990 data, which takes 1–2 years to file and publish. Small organizations and startups often don't have filed 990s yet. That's not a sign of weakness — it's how nonprofit reporting works.

**What you should do:**
- For high-confidence scores (17.9%): Use the percentile and signal as part of your research.
- For good-confidence scores (13.1%): Treat the estimate as background context, not a final word.
- For low-confidence orgs (68.9%): Skip the score entirely and focus on mission, website, and direct contact. A missing score is honest, not incomplete.

---

## Copy Updates (Existing Sections)

### "Data limits" section — add this bullet:
"**Coverage gaps:** We have financial data for only 31% of organizations. The other 69% lack recent filings, not credibility. Many are small, young, or streamlined organizations doing essential work with lean budgets."

### "Lamp tiers" section — add this note:
"Most U.S. nonprofits are small and don't have extensive public records. If an organization has a Spark (minimal data), that usually means they're small or new, not that something is wrong. The lamp shows what's publicly available today — it doesn't judge the work."

---

## Implementation Checklist

- [ ] Create `CoverageVisualization.tsx` component with all 5 charts
- [ ] Update Methodology2.tsx to include new "Coverage & Confidence" section
- [ ] Update FAQ with new Q/A
- [ ] Update copy in "Data limits" and "Lamp tiers"
- [ ] Add callouts emphasizing small-org fairness (P4)
- [ ] Add confidence level indicators to org detail pages
- [ ] Link methodology page from org detail when showing limited-confidence data

---

## Stewardship Alignment

| Principle | How This Helps |
|-----------|----------------|
| **P3 (Evidence-based)** | Shows exactly what % of data is high/good/low confidence |
| **P4 (Small org fairness)** | Explains missing data is common for small orgs, not a judgment |
| **P6 (Mistakes corrected)** | Transparent about coverage gaps; easy to update as data improves |

---

**Owner:** Data Integrity + UX  
**Status:** Proposed; ready for review + implementation  
**Priority:** High (affects every org page that displays scoring)
