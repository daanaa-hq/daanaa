# Daanaa NCCS Data Partnership: Status & Ask

**For:** Dr. Lecy, NCCS  
**Date:** 2026-07-23

---

## Current Coverage

**Tax-deductible nonprofits (501c3s with active donation status):**

| Metric | Number |
|--------|--------|
| Total deductible orgs | 1,946,935 |
| With NCCS financial data | 476,757 |
| **Coverage** | **24.5%** |
| **Gap** | **1,470,178 orgs (75.5%)** |

---

## What We're Using NCCS Data For

- **Peer financial context scores** (0–100 percentile rank)
- **Financial health signals:** HEALTHY / STABLE / NEED_SUPPORT
- **Solvency metrics:** Net assets ratio, months of runway, debt burden

---

## Our Resources

✓ SQLite database infrastructure (2.06M orgs + 15GB of financial data)  
✓ Data ingestion pipeline (proven for NCCS Part X/IX imports)  
✓ Automated scoring engine (peer-group computation at scale)  
✓ Public API serving data to nonprofit discovery platform  
✓ Donor-facing transparency (all scores attributed to NCCS, IRS data)  

---

## The Gaps (Priority Order)

| Gap | Scale | Impact |
|-----|-------|--------|
| **1. Microdonor orgs** (<$50K revenue) | 618K orgs | Only 8.2% have NCCS data |
| **2. Faith/Fraternal** (X, Y, Z NTEE) | 145K orgs | Only 15.1% coverage |
| **3. Liabilities/Debt data** | 1.47M orgs | Can't measure solvency |
| **4. Intermediate/Other** (U, Z NTEE) | 21K orgs | Only 8% coverage |

---

## Our Ask

**We need to understand:**

1. **Why is small-org coverage (8.2%) so low?**
   - Are <$50K organizations using Form 990-N (simplified)?
   - Does 990-N include Part X (balance sheet)?
   - What % of <$50K filers use simplified form?

2. **Why do faith communities (15.1%) lag other sectors?**
   - Lower Form 990 filing rates?
   - Different accounting practices?
   - Excluded from NCCS extraction?

3. **Where is liabilities data?**
   - Only 24% have liabilities data despite 24.5% having net assets
   - Is this a parsing issue or filing rate issue?

**Bottom line:** Can NCCS help us identify which of these gaps are:
- **Fixable** (outreach, extraction improvements)
- **Structural** (certain orgs/types don't report these fields)
- **Partnerships** (joint outreach to increase filing rates in underserved categories)

---

## What We Commit To

✓ Transparent attribution (all scores linked to NCCS data + IRS Form 990)  
✓ No resale of data (scores are internal; raw data stays private)  
✓ Annual refresh as new 990s are filed  
✓ Share aggregate findings with NCCS for research  

---

## Next Steps

- Review this gap analysis with your team
- Discuss which gaps are highest priority for NCCS to investigate
- Identify joint research opportunities (e.g., small-org filing patterns)
- Explore targeted outreach to missing categories

**Contact:** [Daanaa team]
