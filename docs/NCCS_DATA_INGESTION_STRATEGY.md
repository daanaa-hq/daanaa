# NCCS Data Ingestion Strategy

**Date:** 2026-07-23  
**Status:** Ready to execute (awaiting raw file downloads)

## Overview

The NCCS (National Center for Charitable Statistics) BMF catalog provides public financial data for 501(c)(3) organizations. We are ingesting three main data sources:

- **Part VII:** Executive compensation and Form 990 filing information
- **Part X:** Balance sheet data (net assets, liabilities, revenue, expenses)
- **Part XI:** Overhead ratios and program efficiency metrics

## Data Scope & Filtering

**Years included:** Tax years 2019–2024 only (last 5 years of data)  
**Organizations included:** ACTIVE deductibility status only

**Rationale:**
- **5-year window:** Provides meaningful financial trends without stale data; aligns with nonprofit financial cycles
- **Active orgs only:** Ensures data reflects organizations currently operating; prevents scoring of dissolved/inactive entities
- **Filtering at ingestion:** Skipped records are logged but not stored; cleaner database, lower noise in scoring

## Expected Coverage

Based on prior downloads, we expect:
- **Part X coverage:** ~106K additional orgs (balance sheet data unlocks smaller orgs)
- **Part VII coverage:** Varies by org size; primarily larger orgs file detailed compensation schedules
- **Part XI coverage:** TBD after files downloaded

## Data Columns Added

| Column | Type | Source | Purpose |
|--------|------|--------|---------|
| `nccs_executive_compensation` | REAL | Part VII | Highest-paid officer/employee compensation |
| `nccs_form_990_filed` | INTEGER | Part VII | Whether 990 was filed (1/0) |
| `nccs_net_assets` | REAL | Part X | Total net assets (equity) |
| `nccs_liabilities` | REAL | Part X | Total liabilities |
| `nccs_revenue_part_x` | REAL | Part X | Total revenue (balance sheet) |
| `nccs_expenses_part_x` | REAL | Part X | Total expenses (balance sheet) |
| `nccs_part_x_loaded` | INTEGER | Part X | Flag: Part X data loaded (1/0) |
| `nccs_overhead_ratio` | REAL | Part XI | Overhead as % of total expenses |
| `nccs_program_ratio` | REAL | Part XI | Program expenses as % of total expenses |
| `nccs_efficiency_score` | REAL | Part XI | Computed efficiency metric |
| `nccs_data_year` | INTEGER | All | Tax year of filing |
| `nccs_full_load_date` | TEXT | All | ISO timestamp of ingestion |

## Ingestion Pipeline

### Step 1: Add Database Columns
```bash
python3 scripts/add_nccs_columns.py
```
Safe to re-run (uses `IF NOT EXISTS`).

### Step 2: Ingest Part VII (Compensation)
```bash
python3 scripts/ingest_nccs_part_vii.py
```
Logs output to `~/meritgiving/logs/ingest_part_vii.log`

### Step 3: Ingest Part X (Balance Sheet)
```bash
python3 scripts/ingest_nccs_part_x.py
```
Logs output to `~/meritgiving/logs/ingest_part_x.log`

### Step 4: Ingest Part XI (Overhead) [Future]
```bash
python3 scripts/ingest_nccs_part_xi.py
```
(Script to be created once Part XI files are downloaded)

### Full Orchestration (One-Shot)
```bash
bash scripts/orchestrate_nccs_ingest.sh
```
Runs all steps and validates coverage.

## Execution

**When:** After NCCS agent completes download and organizes files in `~/meritgiving/data/nccs/`  
**Server:** Run on local Ryzen hardware (resource-efficient; batch CSV reads)  
**Database:** `~/meritgiving/data/merit_registry.db` (primary database)

## Validation

After ingestion completes, the orchestration script reports:

```
Ingestion Results:
  Total orgs: 1,700,000+
  Part X coverage: 106,000+ (6.2%)
  Part VII coverage: 45,000+ (2.6%)
```

Coverage is expected to be low because:
- Not all orgs file complete Form 990 (some use simpler 990-N)
- Part X/VII are only on Form 990 (Schedule O)
- Filtering to 5-year window removes older filings

## Integration with Scoring

After ingestion:
1. Run `scripts/overnight_pipeline.py` to recompute peer financial context scores
2. `merit_scorer_v4_0.py` will incorporate new balance sheet / compensation data
3. `build_fts_index.py` rebuilds search index (no changes needed)

## Rollback

To remove NCCS data and revert to pre-ingestion state:

```sql
-- Backup existing data
.backup merit_registry.db merit_registry.backup-$(date +%s).db

-- Clear NCCS columns (set to NULL)
UPDATE registry_enriched
SET nccs_executive_compensation = NULL,
    nccs_form_990_filed = NULL,
    nccs_net_assets = NULL,
    nccs_liabilities = NULL,
    nccs_revenue_part_x = NULL,
    nccs_expenses_part_x = NULL,
    nccs_part_x_loaded = NULL,
    nccs_overhead_ratio = NULL,
    nccs_program_ratio = NULL,
    nccs_efficiency_score = NULL,
    nccs_data_year = NULL,
    nccs_full_load_date = NULL;
```

## References

- NCCS Catalog: https://nccs.urban.org/nccs/catalogs/catalog-bmf.html
- Form 990 Structure: https://www.irs.gov/charities-non-profits/form-990-series-downloads
- STEWARDSHIP.md Principle 3: Trust signals must be evidence-based (all data is public IRS filings)
