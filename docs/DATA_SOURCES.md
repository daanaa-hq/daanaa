# Complete IRS Data Source Audit — Daanaa

## Currently Active Sources (in cron)

### 1. **IRS BMF (Business Master File)** — ACTIVE ✅
- **Frequency:** Daily (9 PM via `daily_irs_check.py`)
- **Source:** `https://www.irs.gov/pub/irs-soi/eo[1-4].csv`
- **Coverage:** ~1.7M active 501(c)(3) orgs
- **Last Updated:** June 8, 2026 (26,565 new orgs added June 9)
- **Status:** Primary roster source; essential for new org discovery
- **Script:** `scripts/daily_irs_check.py` + `scripts/refresh_bmf_apply.py`

### 2. **IRS Revocation List** — ACTIVE ✅
- **Frequency:** Daily (9 PM via `daily_irs_check.py`)
- **Source:** `https://apps.irs.gov/pub/epostcard/data-download-revocation.zip`
- **Coverage:** ~96K currently revoked orgs
- **Last Updated:** July 3, 2026 (synced July 4)
- **Status:** Fail-closed filter in API; prevents browsing/donating to revoked orgs
- **Script:** `scripts/daily_irs_check.py` + `scripts/sync_irs_revocations.py`

### 3. **IRS 990-N ePostcard** — ACTIVE ✅
- **Frequency:** Daily (9 PM via `daily_irs_check.py`)
- **Source:** `https://apps.irs.gov/pub/epostcard/data-download-epostcard.zip`
- **Coverage:** Small orgs filing simplified 990-N (gross receipts <$50K)
- **Last Updated:** June 22, 2026 (synced June 30)
- **Status:** Supplemental; currently low priority vs 990 full forms
- **Script:** `scripts/daily_irs_check.py`

### 4. **IRS SOI 990 Extracts (Annual)** — SEMI-ACTIVE ⚠️
- **Frequency:** Monthly first-of-month check (1 AM) + on-demand
- **Source:** `https://www.irs.gov/pub/irs-soi/[YY]eoextract990.zip`
- **Local Files:** 2019–2024 (last cached May 14, 2026)
- **Coverage:** 
  - 2024: 183,711 orgs with financial data
  - 2023: 461,582 orgs
  - 2019–2022: Historical data
- **Latest Available:** 2024 (2025 not yet published)
- **Script:** `scripts/download_irs_soi.sh` + `scripts/backfill_revenue_history.py`

### 5. **NCCS eFile Data** — ACTIVE ✅
- **Frequency:** On-demand (cached; can be scheduled for backfill)
- **Source:** `https://nccs-efile.s3.us-east-1.amazonaws.com/public/efile_v2_1/`
- **Coverage:** Program expense percentages (Part IX) for 2009–2024
- **Local Cache:** 1.9GB (F9-P09-T00-EXPENSES-[YEAR].CSV for 2017–2023)
- **Status:** Backfill-only; enriches financial health signals
- **Script:** `scripts/backfill_program_expenses.py`

### 6. **ProPublica 990 API** — ACTIVE ✅
- **Frequency:** Real-time on-demand; batch processing via GPU pipeline
- **Source:** `https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json`
- **Coverage:** 86,569 orgs with 2025 tax year data (more recent than IRS SOI)
- **Status:** Primary real-time source for recent 990 filings
- **Script:** `scripts/auto_ingest.py`, `agent12_parallel_propublica.py`, GPU batch pipeline

---

## Legacy/Partially Used Sources

### 7. **GivingTuesday GT990 Index** — WEEKLY CRON ✅
- **Frequency:** Weekly Sunday 1 AM via cron
- **Source:** `s3://gt990datalake-rawdata/Indices/990xmls/` (AWS, no-sign-request)
- **Coverage:** 158,122 orgs; pre-extracted 990 financials with URLs
- **Local File:** `data/cache/gt990_index_2026-03-20.csv` (65MB, March 20, 2026)
- **Status:** Weekly refresh active; used for org stub backfill
- **Columns:** BuildTs, EIN, TotalAssets, TotalRevenue, TotalExpenses, TotalLiabilities, TaxYear, Website, FormType, etc.
- **Script:** `scripts/ingest_gt990_index.py --index /data/cache/gt990_latest.csv`
- **Last Run:** Check logs: `logs/gt990_refresh.log`

### 8. **AWS S3 irs-form-990 Index** — DISCOVERED, NOT ACTIVE ❌
- **Frequency:** None (referenced in code, not in cron)
- **Source:** `s3://irs-form-990/index_{year}.json`
- **Status:** Legacy reference; superceded by GT990 + NCCS + ProPublica
- **Script:** `scripts/merit_worker_f.py` (not in active pipeline)
- **Note:** This appears to be a public mirror of IRS 990 XML files; GT990 is the newer index

---

## Potential New Sources (Not Yet Active)

### 9. **IRS Publication 78 (Tax Deductibility List)** — REFERENCED, NOT DOWNLOADED ❌
- **Source:** `https://apps.irs.gov/pub/epostcard/data-download-pub78.zip`
- **Potential Use:** Deductibility verification (currently using org_status)
- **Status:** Could validate donation eligibility without making API calls
- **Action:** Consider automated refresh if deductibility status drifts

### 10. **Form 990 XML Direct from IRS** — LEGACY ❌
- **Source:** IRS eServices direct XML downloads
- **Status:** Slower than ProPublica + NCCS; not active
- **Note:** GT990 + NCCS provide faster, pre-parsed access to same data

---

## Data Gaps & Recommendations

| Gap | Current Status | Recommendation |
|-----|---|---|
| **2025 IRS SOI Extract** | Not published yet (ETA mid-2026) | Monitor via monthly cron; ProPublica covers recent filings |
| **Leadership/Compensation Data** | ProPublica has it; Daanaa shows it tagged with filing year | Good; currently showing `tax_prd_yr` on org pages |
| **501(c)(3) Deductibility** | Currently via `org_status` (BMF flag); Pub78 available | Consider Pub78 refresh as backup verification source |
| **Program Expenses** | NCCS covers 2009–2023 (2024 pending) | Keep NCCS cache warm; request 2024 refresh when available |
| **Small Org Financials (<$50K)** | 990-N ePostcard (basic); no 990 full form | Expected; these orgs file simplified returns; financial data sparse by design |
| **Nonprofit Leadership/Board** | Not systematically ingested | Out of scope; ProPublica has it but not required for scoring |

---

## Summary: What We Have vs What's Missing

### ✅ Have Full Coverage:
- Active 501(c)(3) roster (BMF, 1.7M orgs)
- Revocation status (daily sync)
- Basic 990 financials (2019–2024 IRS SOI + ProPublica real-time)
- Program expense ratios (NCCS 2009–2023)

### ⚠️ Have Partial Coverage:
- 2025+ financials (ProPublica only until IRS publishes SOI)
- Form 990 URLs (GT990 index + websites field)
- Deductibility status (BMF only; Pub78 available as backup)

### ❌ Don't Have (Out of Current Scope):
- Leadership/compensation data (available but not ingested)
- Nonprofit tax identification (not needed; we use EIN)
- 990-N filers with <$50K (intentionally; they file no full 990)
- Real-time Charitable solicitation registration status (state-specific; too granular)

---

## Recommended Next Steps

1. **Monitor IRS 2025 SOI** — Automatic via existing `daily_irs_check.py` (monthly alert when published)
2. **Pub78 Deductibility Backup** — Optional; add monthly refresh to catch delisted orgs faster
3. **NCCS 2024 Expenses** — Watch NCCS S3 for 2024 release; update `backfill_program_expenses.py` cache when available
4. **GT990 Weekly Refresh** — Already in cron; confirm logs stay healthy
5. **ProPublica Real-time** — Currently working; no action needed
