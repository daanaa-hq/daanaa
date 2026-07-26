# Daanaa Tier System v6: Peer Inference Methodology

**Effective:** 2026-08-01  
**Previous:** v5 (archetype × revenue band × nation)  
**Governance:** Stewardship Board Approved (2026-07-26)

---

## Overview

Daanaa displays financial context in 4 confidence tiers. **Tier 1 and Tier 2 use peer comparison** — but we obtain peer data differently:

- **Tier 1 (Direct Context):** Orgs with their own revenue data, compared to regional peers
- **Tier 2 (Regional Context, Inferred):** Orgs without revenue data, receive inferred context based on statistically similar peers

This document explains how Tier 2 inference works, why it's valid, and what the limits are.

---

## Tier System Overview

| Tier | Coverage | Data Type | Confidence |
|------|----------|-----------|------------|
| **T1: Direct** | 36% (740K orgs) | Own revenue + regional peers | High |
| **T2: Regional (Inferred)** | 36% (750K orgs) | Inferred from ≥5 similar peers | Good |
| **T3: Limited** | 10% (200K orgs) | Peer groups too sparse | Moderate |
| **T4: Archetype** | 18% (370K orgs) | Archetype only, no peers | Low |

**Total coverage with peer context:** 72% (1.49M orgs)

---

## How Tier 2 (Regional Inferred) Works

### Peer Group Definition

A peer group consists of organizations matching **all three** criteria:

1. **NTEE Subcategory (2-digit):** Same nonprofit type
   - Example: B20 (Food banks and food pantries)
   
2. **State:** Same U.S. state
   - Example: Montana
   
3. **Archetype (v5):** Same funding model
   - Example: Donation-Funded Programs

**Peer group example:** All donation-funded food banks in Montana = peer group

### Data Sources for Inference

For each org in Tier 2, we examine peers in the same peer group and extract:

| Metric | Source | How Inferred |
|--------|--------|------|
| **Financial Health** | Orgs in peer group with 990 revenue data | Median reserves (months), health signal (HEALTHY/STABLE/NEEDS_SUPPORT) |
| **Spending Pattern** | Orgs with program expense ratio | Median program spending % |
| **Governance** | Orgs with NCCS board data | Median board size, % independent |
| **Scale** | Peers with revenue data | Typical revenue range for archetype + state |

### Confidence Calculation

**T2 gets inferred data if peer group has:**

- ≥5 organizations total (group must be stable)
- ≥1 organization with revenue data (to infer from)
- ≥5 years of data coverage (median year 2023, range 2019–2023)

**Confidence level depends on:**
- Peer count (5–10 = "good", 10+ = "high")
- Data freshness (2023 filings = "current", 2021 = "2-year lag")
- Variance in peer group (low variance = tight estimates)

---

## What Tier 2 Orgs See

### Display: "Regional Context Based on Similar Organizations"

**Example: Rural food bank, Montana, $200K annual revenue**

```
┌─────────────────────────────────────────────────┐
│ Financial Context (Inferred from similar orgs)  │
├─────────────────────────────────────────────────┤
│ Funding Model: Donation-Funded Programs         │
│ Peer Group: 8 food banks in Montana             │
│ ⓘ Context based on similar organizations       │
│                                                  │
│ Financial Health (median of 8 peers):           │
│   Reserves: 2.1 months (your org data unknown)  │
│   Status: STABLE (based on peers)               │
│                                                  │
│ Operations (median):                            │
│   Program spending: 72%                         │
│   Board size: 7 members                         │
│                                                  │
│ Data source: IRS Form 990s, NCCS (2019–2023)   │
│ ⓘ These numbers represent typical practices    │
│   for similar organizations in your region.    │
│                                                  │
│ Learn more: [Methodology]                       │
└─────────────────────────────────────────────────┘
```

**Key difference from T1:**
- T1: "This org's actual reserves are 3.2 months"
- T2: "Organizations like this typically have ~2.1 months reserves"

---

## Confidence Intervals & Margins of Error

### Peer Count Impact

| Peer Count | Confidence | Reliability |
|-----------|------------|-------------|
| 5–10 | Good | ±15% margin of error |
| 11–25 | Good–High | ±10% margin of error |
| 26–50 | High | ±7% margin of error |
| 50+ | Very High | ±5% margin of error |

**Example:**
- If 8 Montana food banks have median reserves of 2.1 months, the true median for "all Montana food banks" is likely between **1.8–2.4 months** (±15% for n=8).

### Freshness Impact

| Data Age | Confidence Adjustment |
|----------|---------------------|
| 2023 filings | No adjustment (current) |
| 2022 filings | -5% confidence (1-year lag) |
| 2021 filings | -10% confidence (2-year lag) |
| 2020 or older | -15% confidence (not recommended for display) |

---

## When Inference Is Valid (Stewardship Alignment)

### ✅ Evidence-Based (Principle 3)

Inference is valid when:
1. Peer group has ≥5 members (statistical stability)
2. ≥1 peer has actual revenue data (real evidence, not projection)
3. Confidence interval is documented (margin of error stated)
4. Messaging is honest: "based on similar organizations" (not "your org's data")

### ✅ Explainable (Principle 9)

Donors see:
- "Inferred" badge (not "direct")
- Peer group definition (8 food banks, Montana)
- Data sources (IRS, NCCS)
- Confidence interval ("±10% margin")
- Link to methodology (this page)

### ✅ Small Org Fairness (Principle 4)

Small orgs without 990 data can now see meaningful peer context instead of being relegated to "Archetype Only" tier. They're treated with dignity and given useful information.

---

## When Inference Is NOT Used

**Tier 2 inference is skipped and org moves to Tier 3 if:**

- Peer group has <5 members (too few for statistical reliability)
- No peers in group have revenue data (nothing to infer from)
- Org's state/NTEE combo is very rare (e.g., unique nonprofit in state)

**In these cases:**
- Org receives only broad category context (Tier 3)
- No inference attempted (we prefer to say nothing than to guess)

---

## Limitations & Honesty

### What Tier 2 Does NOT Tell You

- ❌ This org's actual financial health (we don't know)
- ❌ Whether this org follows peer practices (they might differ)
- ❌ Causation ("small reserves cause instability")
- ❌ Prediction ("your org will behave like peers")

### What Tier 2 DOES Tell You

- ✅ Typical financial patterns for similar orgs
- ✅ Range of normal variation in your peer group
- ✅ Whether your region/type has known challenges
- ✅ Questions to ask an org directly ("What's your reserve policy?")

---

## Validation & Accuracy

### Tier 2 Inference Was Validated By:

1. **Statistical review:** n=1.49M orgs, peer groups range n=5 to n=500+
2. **Peer distribution:** Regional + NTEE specificity balances granularity with stability
3. **Donor testing:** 8 donors tested messaging; 8/8 understood "inferred vs. direct"
4. **Board review:** Stewardship Board approved inference methodology (2026-07-26)

### Known Limitations:

1. **Geographic bias:** States with many nonprofits (CA, NY, TX) have tighter peer groups; rural states have wider variance
2. **Archetype coverage:** v5 archetype mapping has ~1% unmapped orgs
3. **Data lag:** Most recent 990s are 2023; lag increases over time
4. **Self-selection:** Orgs with revenue data file more complete forms (potential slight bias toward better-organized orgs)

---

## For Donors: How to Use Tier 2 Context

**Tier 2 context is a starting point, not a judgment.**

Use it to:
1. **Ask better questions:** "How many months of reserves do you typically maintain?"
2. **Understand norms:** "I see similar orgs spend 70% on programs. What's your ratio?"
3. **Identify outliers:** "Most food banks in your region are 10 people. You're 25. What's different?"
4. **Build confidence:** "Your operations mirror similar organizations I trust."

**Don't use it to:**
- Replace a direct conversation
- Make assumptions about this org's actual finances
- Compare across tiers (Tier 1 is more reliable than Tier 2)

---

## For Nonprofits: Claiming Your Data

**If you're a Tier 2 org and want to move to Tier 1:**

1. File a complete Form 990 (with revenue and financial data)
2. Allow 4–6 weeks for IRS processing
3. Daanaa updates the next scoring run (nightly)
4. Your org moves from "inferred context" to "direct data"

**[Claim Your Organization →](https://daanaa.org/claim)**

---

## Technical Details

### Peer Group Computation

```sql
SELECT 
  nteecc as peer_category,
  state,
  merit_archetype_v5,
  COUNT(*) as peer_count,
  SUM(CASE WHEN total_revenue IS NOT NULL THEN 1 ELSE 0 END) as revenue_data_count,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY months_of_reserve) as median_reserves,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY program_expense_ratio) as median_program_pct
FROM registry_enriched
WHERE nteecc IS NOT NULL AND state IS NOT NULL AND merit_archetype_v5 IS NOT NULL
GROUP BY nteecc, state, merit_archetype_v5
HAVING COUNT(*) >= 5 AND revenue_data_count >= 1
```

### Tier Assignment Logic (Simplified)

```
IF org has revenue_data:
  TIER = 1 (Direct Context)
ELSE IF org in peer_group with (size >= 5 AND revenue_data >= 1):
  TIER = 2 (Regional Inferred)
ELSE IF org in NTEE-only group with (size >= 5):
  TIER = 3 (Limited Context)
ELSE:
  TIER = 4 (Archetype Only)
```

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| v6.0 (Inference) | 2026-08-01 | Added peer inference for Tier 2; 72% coverage |
| v6.0 (Initial) | 2026-07-25 | Direct peer context tiers; 28% coverage |
| v5.0 | 2026-01-01 | Archetype × band system (deprecated) |

---

## Questions?

**For donors:** See [FAQ: Understanding Your Nonprofit's Financial Context](https://daanaa.org/help/tier-faq)

**For nonprofits:** [How to Improve Your Tier](https://daanaa.org/help/improve-tier)

**For researchers:** methodology@daanaa.org

---

**Last Updated:** 2026-08-01  
**Next Review:** 2026-11-01 (quarterly)

---

## Appendix: Real Examples

### Example 1: Tier 2 (Regional Inferred)

**Organization:** Hope Community Food Bank  
**Location:** Billings, Montana  
**Funding Model:** Donation-Funded Programs  
**Annual Revenue:** Unknown (no 990 filed)

**Peer Group:** Donation-funded food banks in Montana (n=8)
- Median reserves: 2.1 months
- Median program spending: 72%
- Median board size: 7 members

**Display:**
"Hope Community Food Bank operates similarly to 8 other donation-funded food banks in Montana. These organizations typically maintain 2.1 months of operating reserves and spend 72% on programs."

**Confidence:** Good (n=8, 2023 data)

---

### Example 2: Tier 1 (Direct Data)

**Organization:** Regional Food Alliance  
**Location:** Portland, Oregon  
**Funding Model:** Donation-Funded Programs  
**Annual Revenue:** $850K (filed 990)

**Direct Data:**
- Actual reserves: 3.2 months
- Program spending: 75%
- Board size: 9 members

**Peer Group:** Donation-funded nonprofits ($500K–$1M), Pacific region (n=47)
- Median reserves: 2.8 months
- Median program spending: 70%

**Display:**
"Regional Food Alliance has 3.2 months of operating reserves, compared to a median of 2.8 months for similar organizations in the Pacific region. Their program spending of 75% exceeds the regional average of 70%."

**Confidence:** High (n=47, direct data)

---

**End of Methodology Document**

