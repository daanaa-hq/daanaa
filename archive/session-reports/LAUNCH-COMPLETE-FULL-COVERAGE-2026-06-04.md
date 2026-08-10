# DAANAA v4.0 — FULL COVERAGE DEPLOYED ✅

**Date:** 2026-06-04  
**Status:** Production-ready with complete fair coverage  
**Total Organizations Scored:** 538,233  
**Coverage:** 29.7% of all 501(c)(3)s with financial data available  

---

## Three-Tier Scoring System

### ✅ Tier A: Complete Financial Fingerprint
- **71,473 organizations**
- All 4 metrics: revenue, expenses, reserves, program spend
- Donor-deductible (IRS deductibility='1')
- Original visibility tiers: Blazing/Burning Bright/Growing/Steady Flame/Just Starting

### ✅ Tier B: Partial Data (Revenue + Expenses)
- **308,517 organizations**
- Derived program expense from NTEE defaults or org data
- Donor-deductible (IRS deductibility='1')
- Marked as: visibility_tier='Tier_B'

### ✅ Tier C: Non-Deductible with Financial Data
- **158,243 organizations**
- Revenue + expenses available (same data as Tier B)
- NOT donor-deductible (IRS deductibility != '1')
- Marked as: visibility_tier='Tier_C'
- **Previously excluded due to deductibility filter—now fairly scored**

---

## The Stewardship Fix

**What We Found:** 158,243 legitimate nonprofits with complete financial data were being excluded solely because their deductibility status wasn't '1'. Examples:
- Amalgamated Transit Union (deductibility=2, revenue=$101K)
- Countless trade unions, professional associations, mutual benefit orgs
- Health plans, pension funds, other specialized nonprofits

**The Problem:** Excluding orgs from fair ranking based on tax deductibility violates our principle of treating all organizations with equal dignity.

**The Solution:** Tier C applies the same peer-based methodology (8 operating models, revenue bands, percentile ranking) to non-deductible orgs with financial data.

**The Result:** 158,243 additional orgs now get fair peer-based scoring instead of no visibility at all.

---

## Coverage Breakdown

| Tier | Orgs | Deductible | Data | Visibility Marker |
|------|------|---|---|---|
| A | 71,473 | ✅ Yes | Complete | Original (Blazing/etc) |
| B | 308,517 | ✅ Yes | Partial (rev+exp) | "Tier_B" |
| C | 158,243 | ❌ No | Partial (rev+exp) | "Tier_C" |
| **Total Scored** | **538,233** | Mixed | Mixed | Various |
| Unscored | ~1.2M | Any | None | N/A |

**Unscored Orgs:** Those with NO financial data cannot be scored fairly without inventing metrics.

---

## Financial Health Distribution

### Tier A (Complete Data)
- Blazing: 1,149 orgs (100% Strong)
- Burning Bright: 8,327 orgs (100% Strong)
- Growing: 28,779 orgs (100% Stable)
- Steady Flame/Just Starting: Variable

### Tier B (Deductible, Partial Data)
- Strong: 110,790 (35.9%)
- Stable: 154,752 (50.2%)
- Inspiring: 42,975 (13.9%)

### Tier C (Non-Deductible, Partial Data)
- Strong: 43,971 (27.8%)
- Stable: 80,688 (51.0%)
- Inspiring: 33,584 (21.2%)

*Note:* Tier C has more Stable/Inspiring ratio vs Tier B, possibly due to different organizational profiles (unions, professional associations, health plans).

---

## API Integration

All three tiers seamlessly integrated:
- `visibility_tier` field distinguishes tiers
- Same peer-based scoring methodology across all tiers
- Tier A preserves original visibility markers
- Tier B and C clearly marked for transparency
- All 4 v4 fields present: financial_health, operating_model, peer_cell_size, revenue_band

**Sample:**
```json
{
  "EIN": "010018605",
  "organization_name": "AMALGAMATED TRANSIT UNION",
  "financial_health": "Inspiring",
  "operating_model": "Direct_Service",
  "visibility_tier": "Tier_C",
  "peer_cell_size": 14910
}
```

---

## Stewardship Alignment

✅ **Principle 1: Fairness** — All orgs with financial data get peer-based scoring (no exclusion by deductibility)  
✅ **Principle 2: Transparency** — visibility_tier clearly marks which tier each org belongs to  
✅ **Principle 3: Dignity** — Non-deductible orgs treated with equal methodological rigor  
✅ **Principle 4: Accuracy** — Peer groups maintain ≥75 org minimum across all tiers  
✅ **Principle 5-11:** All verified ✅

---

## Launch Readiness

- [x] All three tiers loaded and indexed
- [x] API serving all tiers with visibility_tier distinguishing
- [x] Health distributions verified and fair
- [x] Sample orgs tested across all tiers
- [x] Stewardship gap fixed (Tier C now included)
- [x] Repository clean
- [x] Documentation complete
- [x] Zero-downtime deployment (additive changes only)

**Status:** PRODUCTION READY ✅

---

## What This Means for Users

When searching for nonprofits, users will now see:

1. **Tier A orgs** with complete financial profiles → Original visibility tier + Financial Health
2. **Tier B orgs** (deductible, partial data) → marked "Tier_B" + Financial Health  
3. **Tier C orgs** (non-deductible, partial data) → marked "Tier_C" + Financial Health

Example: 
- A food bank (Tier B): "Stable among Direct Service nonprofits"
- A health plan (Tier C): "Inspiring among Direct Service nonprofits"

Both get fair peer-based scoring. No org is invisible just because of tax status.

---

## Next Phase

1. **Public Announcement:** Ready to send
2. **Monitor 24h:** Latency, error rate, engagement
3. **Gather Feedback:** User experience with three-tier system
4. **Future Features:** Weekly category tiles, intelligent tooltips, hidden gems mechanic

---

**System Complete. Stewardship Gap Fixed. Ready for Launch.** 🚀

Signed: Claude Haiku 4.5 | Date: 2026-06-04 | Status: LIVE ✅
