# Monthly Reports: Tied to Data Pipeline, Not Calendar

**Concept:** Monthly reports document what actually happened in the data, not arbitrary "state of sector" pieces.

**Trigger:** After `overnight_pipeline.py` completes (IRS ingest → scoring → benchmarking → FTS rebuild)

**Frequency:** 1x per month (ideally first Monday, but triggered by pipeline completion)

---

## What Gets Reported

After each pipeline run, we publish a report showing:

### 1. **New Organizations Added**
- Count: "842 new nonprofits added this month"
- Source: IRS Form 990 filings, BMF updates
- Sectors: Which causes are growing
- Geography: Which regions added most new orgs
- CTA: "Explore this month's newly discovered organizations"

### 2. **Score Updates & Implications**
- Financial health changes: How many orgs improved reserves? How many declined?
- Peer rank shifts: Which orgs moved up their peer group?
- Sector trends: "Food banking reserves down 5% month-over-month"
- Geographic patterns: "Rural nonprofits stabilizing; urban growing"
- CTA: "See how your nonprofit ranks vs. peers"

### 3. **What We Learned**
- Surprising findings from the data
- "30% of food banks now below 2-month reserves" (trend, not judgment)
- "Education nonprofits growing faster than overall sector" (context)
- Honest gaps: "We lost contact info for 234 orgs; can you help?"

### 4. **Data Quality & Transparency**
- Coverage: "Now tracking 1.7M active nonprofits (up from 1.698M last month)"
- Freshness: "Latest IRS 990 data is from April 2026 filings (2-month lag)"
- What changed: New columns added, better address coverage, improved mission data
- Limitations: "We don't yet have outcome data for 15% of sector"

### 5. **How to Use This**
- If you lead a nonprofit: "Claim your profile to see your updated ranking"
- If you're a funder: "See which sectors are growing fastest"
- If you're a supporter: "Discover newly listed organizations in your area"
- If you're a researcher: "Download this month's snapshot"

---

## Example: July 2026 Pipeline Report

**Title:** What Changed in the Nonprofit Sector This Month (June–July 2026)

**Publish date:** First Monday after pipeline completes

```
# New Discoveries: 842 Organizations Added This Month

Our database grew from 1,701,158 to 1,702,000 active nonprofits.

## Where They Are
- California: +127 new orgs
- Texas: +98
- Remote: +34
- International: +8

## What They Do
- Human Services: +234 (fastest growing)
- Education: +156
- Health: +127
- Other: +325

## Explore
[See all newly discovered nonprofits]
[Discover new orgs in your state]
[Browse by sector]

---

# What Changed in Financial Health

## Overall Trend
- **Reserves declining slightly** (avg. 3.4 → 3.2 months YoY)
- **Revenue stable** (median +1.2% YoY)
- **Small orgs growing faster** (+16% YoY for <$150K revenue)

## By Sector
| Sector | Orgs | Median Reserves | Month-over-Month |
|--------|------|-----------------|------------------|
| Food Banking | 47,382 | 2.8 mo | ↓ -0.3 mo |
| Education | 204,000 | 5.1 mo | ↔ stable |
| Health | 128,000 | 6.2 mo | ↑ +0.1 mo |
| Human Services | 289,000 | 3.1 mo | ↓ -0.2 mo |

**What it means:** Food banks face growing pressure; education stable; health improving.

## By Geography
- Urban orgs: 5.2 mo median reserves (↑ +0.1 mo)
- Suburban: 4.1 mo (↔ stable)
- Rural: 2.8 mo (↓ -0.1 mo) **needs support**

[View detailed peer rankings]
[See your organization's updated rank]

---

# Data Updates & Quality

## What's New
- ✅ 456 organizations claimed their profile and updated mission statements
- ✅ 892 new financial records absorbed (June 2026 990 filings)
- ✅ 1,200+ addresses backfilled from BMF data
- ⚠️ 34 orgs gone dark (no recent filing, likely dissolved)

## What's Better
- Address coverage: 96.8% (up from 96.2%)
- Mission clarity: 78% of orgs now have a stated mission (up from 74%)
- Website links: 84% now have verified website URLs

## What We Still Don't Know
- 15% of orgs: no recent 990 filing (data >18 months old)
- 22% of orgs: mission statement missing (small/informal orgs)
- 8% of orgs: reserve data incomplete (simplified filing)

[Help us improve the data]

---

# How This Helps You

## If you lead a nonprofit:
**Your ranking just updated.** [See where you stand vs. peers]
Want to update your info? [Claim your profile]

## If you're a funder:
**Food banking reserves are down 5% across the sector.**
[See which food banks need capital support]
[Find organizations with strong reserves]

## If you're a supporter:
**842 new nonprofits joined this month.**
[Discover new organizations in your area]
[See which sectors are growing]

## If you're a researcher:
**Download this month's snapshot (CSV, JSON)**
[Full financial database]
[Peer group benchmarks]
[Sector analysis data]

---

# What We're Watching

**Concerning trends:**
- Food banking reserves declining (watch for crisis)
- Rural org density static (nonprofit deserts persist)
- Small org growth not translating to reserves (mission over margin)

**Positive trends:**
- Health sector strengthening
- New org creation outpacing dissolutions
- Nonprofit profile claiming up 15% month-over-month

**Next month:** We expect IRS 990s from May 2026 filings. Food banking data will update.

---

# Questions & Feedback

- Found an error in your org's data? [Report it]
- Have data we're missing? [Share it]
- Ideas for this report? [Tell us]

**Data sources:** IRS Form 990 (ProPublica API, e-file), BMF, Daanaa claimed data
**Methodology:** Peer-group benchmarking (NTEE + revenue band, N≥20)
**Confidence:** 95% for financial metrics, 85% for geographic trends, 70% for outcome inference
**Last updated:** July 1, 2026 (covering June pipeline)
**Next update:** August 1, 2026 (covering July pipeline)

---

[Download full dataset] [Subscribe to updates] [Read past reports]
```

---

## Why This Format Works

1. **Tied to reality** — Reports data that actually changed, not speculation
2. **Transparency** — Shows what's improving, what's concerning, what's missing
3. **Actionable** — Different CTAs for different reader types
4. **Evergreen** — No date-specific content; can be read anytime
5. **SEO-friendly** — Targets "nonprofit statistics," "nonprofit trends," "sector health"
6. **Drives engagement** — Org updates, sector trends, peer rankings all encourage discovery

---

## Automation Potential

**Steps 1–3 (happens automatically after pipeline):**
```python
# After overnight_pipeline.py completes:
# 1. Query new orgs added (EIN not in previous month's snapshot)
# 2. Calculate financial health changes (median reserves, margin)
# 3. Generate report from template (fill in numbers, create charts)
# 4. Publish to /research/monthly/YEAR-MONTH-report.md
# 5. Email: Announce to subscribers
# 6. Social: Tweet key stats
```

**Timeline:** ~30 minutes of automation work to wire this up

**Output:** Auto-published monthly report, every month after pipeline completes

---

## Relationship to Broader Research Strategy

| Content Type | Frequency | Purpose | Automation |
|---|---|---|---|
| **Monthly pipeline report** | 1x/month (after pipeline) | What changed in the data | ✅ Fully auto |
| **Quarterly white papers** | 4x/year | Thought leadership | Manual |
| **Sector deep-dives** | 1-2x/month | Deep analysis + skills | Semi-auto |
| **Research articles** | As needed | Explain findings + methodology | Manual |

**The monthly report is the heartbeat.** Everything else hangs off it.

---

## Next Steps

1. Wire pipeline completion to trigger report generation
2. Create report template (fill-in-the-blanks from data)
3. Publish first report after next pipeline run
4. Track: engagement, CTA clicks, org profile claims
5. Iterate based on reader feedback

This makes Daanaa a **living datasource**, not a static snapshot.
