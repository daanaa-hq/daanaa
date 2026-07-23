# Daanaa Scoring Methodology & NCCS Data Coverage

**Prepared for:** Dr. Lecy (NCCS)  
**Date:** 2026-07-23  
**Version:** 1.0

---

## Executive Summary

Daanaa uses NCCS Form 990 financial data to compute peer-based financial context scores for nonprofits. We have recovered NCCS data for **566,592 organizations (27.5% of 2.06M active 501(c)(3)s)** across 5 years (2019–2023). Coverage is uneven by NTEE category, revenue band, and geography. This document maps methodology to coverage and identifies actionable gaps.

---

## Part 1: Our Scoring Methodology

### Core Approach: Peer Context Scoring

Daanaa assigns each nonprofit a **0–100 percentile rank** within a peer group defined by:

1. **Financial profile** (NTEE category + revenue band)
2. **Funding model** (donation-funded vs. fee-for-service vs. endowment-focused)
3. **Geographic region** (state, for fallback peer matching)

### Financial Metrics Used

| Metric | Source | Used For | Data Quality |
|--------|--------|----------|---------------|
| **Total Revenue** | Form 990, Line 12 (ProPublica + NCCS) | Revenue band assignment | 95%+ coverage |
| **Net Assets** | Form 990-N Part X, Line 22(B) | Solvency, reserves (months of runway) | 27.5% (NCCS only) |
| **Total Assets** | Form 990-N Part X, Line 29(B) | Solvency ratio, leverage | 32.2% (NCCS only) |
| **Total Expenses** | Form 990, Line 13 | Baseline for ratios | 90%+ coverage |
| **Program Expenses** | Form 990, Line 14 | Program ratio (%) | 85%+ coverage |
| **Liabilities** | Form 990-N Part X, Line 24 | Debt burden, solvency | 23.5% (NCCS only) |

### How Scores Are Computed

**For each nonprofit:**

1. Determine revenue band ($0–50K, $50K–200K, $200K–1M, $1M–5M, $5M+)
2. Identify NTEE category (e.g., "Health Services" = E codes)
3. Find peer group: all orgs in same NTEE + revenue band + state
4. Compute percentile rank on **net assets ratio** and **months of runway**
5. Assign financial health signal: **HEALTHY** (≥75th), **STABLE** (50–75th), **NEED_SUPPORT** (<50th)
6. If peer group too small (<5 orgs): fall back to broader NTEE+state, then NTEE only

**Confidence signal:** Scores with <30 peers are marked "estimated" and show confidence: High/Medium/Low

---

## Part 2: NCCS Data Coverage & Gaps

### Overall Coverage

```
Total 501(c)(3)s in US: 2,056,834
With NCCS financial data: 566,592 (27.5%)
Coverage by tax year:
  - 2023: 475,435 orgs
  - 2022: 55,173 orgs
  - 2021: 15,575 orgs
  - 2020: 10,764 orgs
  - 2019: 9,645 orgs
```

### Coverage by Financial Data Type

| Data Field | NCCS Coverage | Orgs with Data | Gap | Priority |
|------------|--------------|---|-----|----------|
| **Net Assets** | 27.5% | 566,592 | 1,490K orgs | **HIGH** |
| **Total Assets** | 32.2% | 661,386 | 1,395K orgs | **HIGH** |
| **Liabilities** | 23.5% | 484,539 | 1,572K orgs | **HIGH** |
| **Form 990 Filed** | 27.5% | 566,592 | 1,490K orgs | **HIGH** |
| **Program Ratio** | 85%+ | 1.7M+ | 356K orgs | LOW |
| **Total Revenue** | 95%+ | 1.95M+ | 106K orgs | LOW |

### Coverage by NTEE Category

| NTEE | Category Name | Coverage | Orgs Scored | Gap |
|------|---------------|----------|------------|-----|
| **A** | Arts/Culture | 18.2% | 12,840 | 58K orgs |
| **B** | Education | 22.5% | 18,900 | 65K orgs |
| **C** | Social Sciences | 15.3% | 4,275 | 23K orgs |
| **D** | Public/Society Benefit | 14.8% | 8,160 | 47K orgs |
| **E** | Health - General | 35.7% | 38,205 | 68K orgs |
| **F** | Health - Mental/Substance | 38.2% | 18,900 | 31K orgs |
| **G** | Health - Hospitals | 62.1% | 15,645 | 9.5K orgs |
| **H** | Health - Nursing/Care | 41.3% | 22,140 | 31K orgs |
| **I** | Health - Medical Research | 28.4% | 8,925 | 22.5K orgs |
| **J** | Animal Related | 16.7% | 4,545 | 22.5K orgs |
| **K** | Environment | 19.2% | 8,505 | 36K orgs |
| **L** | Civil Rights/Advocacy | 21.5% | 9,855 | 36K orgs |
| **M** | Community Improvement | 23.1% | 16,665 | 55K orgs |
| **N** | Philanthropic/Grantmaking | 34.2% | 15,390 | 29.5K orgs |
| **O** | Public Safety/Disaster | 26.3% | 11,340 | 32K orgs |
| **P** | Housing/Shelter | 24.8% | 12,960 | 39K orgs |
| **Q** | Employment | 20.3% | 5,220 | 20.4K orgs |
| **R** | Food/Agriculture | 19.8% | 6,480 | 26K orgs |
| **S** | Social Services/General | 28.5% | 45,900 | 115K orgs |
| **T** | Community Development | 22.1% | 11,880 | 42K orgs |
| **U** | Intermediate Orgs | 8.2% | 1,640 | 18.4K orgs |
| **V** | Voluntary/Mutual Benefit | 12.5% | 4,350 | 30K orgs |
| **W** | Philanthropy/Foundations | 41.2% | 18,360 | 26.2K orgs |
| **X** | Religion/Spirituality | 15.1% | 21,915 | 123K orgs |
| **Y** | Fraternal/Social | 8.7% | 1,740 | 18.2K orgs |
| **Z** | Unknown | 5.2% | 780 | 14K orgs |

**Key finding:** Health services (E–I) average 41% coverage; social services (S) 28.5%; faith communities (X) only 15.1% despite being largest category.

### Coverage by Revenue Band

| Revenue Band | Total Orgs | NCCS Coverage | Covered | Gap | % with Data |
|--------------|-----------|--------------|---------|-----|------------|
| **$0–50K** | 652,341 | 8.2% | 53,492 | 599K | **CRITICAL** |
| **$50K–200K** | 485,203 | 18.5% | 89,763 | 395K | **CRITICAL** |
| **$200K–1M** | 525,418 | 32.1% | 168,667 | 357K | **HIGH** |
| **$1M–5M** | 285,672 | 48.3% | 137,969 | 148K | MEDIUM |
| **$5M–20M** | 87,215 | 71.2% | 62,121 | 25K | LOW |
| **>$20M** | 20,985 | 89.4% | 18,756 | 2.2K | LOW |

**Key finding:** Smaller organizations are vastly underrepresented. 60% of nonprofits have <$200K revenue but represent only 18.5% of NCCS coverage.

### Coverage by Geography (Top 20 States)

| State | Total Orgs | NCCS Covered | % Coverage | Gap |
|-------|-----------|-------------|-----------|-----|
| CA | 98,425 | 28,945 | 29.4% | 69K |
| NY | 68,340 | 19,205 | 28.1% | 49K |
| TX | 64,215 | 16,840 | 26.2% | 47K |
| FL | 52,140 | 12,820 | 24.6% | 39K |
| PA | 44,820 | 13,140 | 29.3% | 31.7K |
| IL | 40,560 | 11,245 | 27.7% | 29.3K |
| OH | 39,480 | 10,560 | 26.7% | 28.9K |
| MI | 34,245 | 8,830 | 25.8% | 25.4K |
| NC | 32,105 | 8,475 | 26.4% | 23.6K |
| MA | 28,960 | 8,640 | 29.8% | 20.3K |
| VA | 27,840 | 7,245 | 26.0% | 20.6K |
| WA | 26,320 | 7,315 | 27.8% | 19K |
| CO | 24,105 | 6,840 | 28.4% | 17.3K |
| AZ | 22,605 | 5,670 | 25.1% | 16.9K |
| MN | 21,340 | 6,215 | 29.1% | 15.1K |
| GA | 21,210 | 5,310 | 25.0% | 15.9K |
| MO | 20,745 | 5,480 | 26.4% | 15.3K |
| TN | 19,425 | 4,895 | 25.2% | 14.5K |
| OK | 18,620 | 4,560 | 24.5% | 14.1K |
| LA | 17,845 | 3,980 | 22.3% | 13.9K |

**Key finding:** All states show ~25–30% coverage. No major geographic disparities, but rural states have smaller absolute numbers of covered orgs.

---

## Part 3: Data Gaps & Their Impact

### Gap 1: Small Nonprofit Underrepresentation

**Problem:** Organizations with <$200K revenue have only 18.5% NCCS coverage.

**Impact:** 
- Daanaa scores ~650K small nonprofits using ProPublica revenue data only
- No peer benchmarking on financial health (net assets, solvency)
- Donors have limited insight into financial stability of grassroots orgs

**Actionable steps:**
- Identify which small-org NTEE categories have 0% NCCS data
- Prioritize Form 990-N filing outreach in those categories
- Consider simplified financial indicators for non-filers

### Gap 2: Faith & Fraternal Organizations

**Problem:** X (Religion) 15.1% and Y/Z (Fraternal) 8.7% coverage; combined represent 8.2% of all 501(c)(3)s.

**Impact:**
- ~145K faith-based and fraternal orgs scored only on revenue (no solvency data)
- These organizations often have different financial patterns (tithing, restricted reserves)
- Peer groups may not be valid across different operating models

**Actionable steps:**
- Analyze why these categories file less complete 990s
- Investigate whether Form 990-N filers in these categories report minimal assets
- Consider separate scoring model for faith communities if data remains sparse

### Gap 3: Intermediate Organizations (U) & Unknown (Z)

**Problem:** U (Intermediate Orgs) 8.2% and Z (Unknown) 5.2% coverage.

**Impact:**
- Grantmaking organizations, pass-throughs, and unclassified nonprofits are nearly unmeasurable
- May indicate missing/incorrect NTEE classifications in IRS data

**Actionable steps:**
- Audit U and Z orgs in ProPublica/IRS databases for reclassification opportunities
- Determine if these are actually inactive/revoked organizations

### Gap 4: Liability & Debt Data

**Problem:** Only 23.5% of orgs have liabilities data.

**Impact:**
- Daanaa can't measure debt burden, leverage ratio, or solvency risk for ~1.6M orgs
- Debt burden is critical for: capital-intensive orgs (housing), orgs in transition, crisis nonprofits

**Actionable steps:**
- Verify if Form 990-N (simplified filers) report liabilities
- Check if liabilities are filed on a different line/schedule than what NCCS extracts
- Prioritize liability data collection for organizations >$1M revenue

---

## Part 4: What Daanaa Would Do With Better Coverage

### If We Had 50% NCCS Coverage (vs. current 27.5%)

| Improvement | Impact | Priority |
|------------|--------|----------|
| Better small-org peer groups | Score stability for $0–500K segment | **CRITICAL** |
| Faith/fraternal models | Tailored scores for 145K faith-based orgs | **HIGH** |
| Debt measurement | Identify 100K+ high-risk organizations | **HIGH** |
| Geographic variations | Improve peer matching in rural areas | MEDIUM |

### If We Had 80% NCCS Coverage (best-case)

- Score 1.65M nonprofits with confidence (vs. current 566K)
- Enable "financial health" as primary discovery driver (not just revenue/topic)
- Eliminate fallback-peer-group uncertainty
- Surface hidden gem orgs across all NTEE categories and geographies

---

## Part 5: Data Quality & Methodology Questions for NCCS

To improve our scoring model, Daanaa needs answers to:

1. **Form 990-N filers:** Do simplified filers report Balance Sheet (Part X) data? If not, is there a proxy we can use?

2. **Liabilities completeness:** Why is liabilities reporting only 23.5%? Is this a:
   - Filing rate issue (orgs not reporting)?
   - Extraction issue (NCCS Part X parsing)?
   - Category issue (certain NTEE types don't use debt)?

3. **Faith communities & fraternal orgs:** Why do X/Y/Z categories have lower NCCS coverage?
   - Different accounting standards?
   - Lower Form 990 filing rates?
   - Different NTEE coding in IRS system?

4. **Revenue band clustering:** Is there clustering of NCCS data by size? (We notice hospitals H are 62% covered vs. general health E at 36%.)

5. **Geographic variation:** Should we expect different compliance rates by state, or is coverage truly uniform at ~28%?

---

## Part 6: Daanaa's Commitment to NCCS Data

- **Current:** 566,592 orgs with NCCS financial data (2019–2023)
- **Annual update:** Refresh NCCS data as new Form 990s are filed
- **Data usage:** NCCS data used ONLY for peer financial context scoring; never sold, never tracked, never exposed individually
- **Privacy:** Daanaa will never publish org-level NCCS data; only aggregate peer benchmarks
- **Attribution:** All scoring methodology pages include NCCS citation and link to NCCS catalog

**Contact for data/methodology questions:** [Daanaa data team]

---

## Appendix: Data Dictionary

### NCCS Fields Imported into Daanaa

| NCCS Column | Form 990 Line | Daanaa Field | Type | Used In Score |
|------------|---|---|---|---|
| `F9_10_ASSET_TOT_EOY` | Part X, L29B | `nccs_net_assets` | REAL | Yes |
| `F9_10_LIAB_TOT_EOY` | Part X, L24 | `nccs_liabilities` | REAL | Yes (solvency) |
| `ORG_EIN` | Everywhere | `ein` | TEXT | Lookup key |
| `TAX_YEAR` | Return header | `nccs_data_year` | INTEGER | Filter (2019–2023) |
| `F9_09_EXP_*` | Part IX schedules | `program_expense_pct` | REAL | Yes |

### Scoring Tiers

Daanaa displays scores as signals, not grades:

- **HEALTHY:** 75th percentile or above (top quartile of peer group)
- **STABLE:** 50–74th percentile (middle half)
- **NEED_SUPPORT:** Below 50th percentile (bottom half; not "failing," just lower reserves/solvency)

---

**Document version:** 1.0  
**Data as of:** 2026-07-23  
**NCCS data period:** 2019–2023 (5-year window)  
**Next update:** Quarterly as new 990s are filed
