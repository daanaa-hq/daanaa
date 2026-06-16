# Database Audit Report — 2026-06-16

## Executive Summary

Audit of `data/merit_registry.db` (rebuilt 2026-06-13) identified **5 critical data quality issues** that would propagate through every data pipeline run and compromise the foundation:

1. **Negative revenue values** (1,833 orgs) — impossible data, breaks scoring
2. **Missing NTEE1 classification** (582,550 orgs = 29.4%) — breaks peer grouping
3. **Invalid STATE codes** (1,377 orgs with empty/bad states) — breaks geography filtering
4. **Bad deductibility values** (needs re-validation) — breaks filtering
5. **Missing critical fields** (mission, website data) — not yet backfilled

**Recommendation:** Rebuild database using `rebuild_from_scratch_v2.py` with validation gates, then validate with `validate_database.py` before any further work.

---

## Issues Found

### Issue #1: Negative Revenue Values
**Severity:** CRITICAL  
**Count:** 1,833 orgs  
**Examples:**
- EIN 042997367 (PHEMUS CORPORATION): -$150,302,637
- EIN 383250137 (CONSUMERS POWER COMPANY): -$79,431,111
- EIN 943363675 (TOMPKINS CONSERVATION): -$55,603,445

**Impact:** Breaks v4 and v5 financial scoring (both use revenue as denominator in calculations). These orgs should not be scored or should have revenue set to NULL.

**Root Cause:** Source data (BMF + 990-N CSVs) contains negative values; rebuild script did not validate.

**Fix:** Filtering already implemented in `rebuild_from_scratch_v2.py` (rejects any org with total_revenue < 0).

---

### Issue #2: Negative Expense Values
**Severity:** CRITICAL  
**Count:** 63 orgs  
**Impact:** Same as negative revenue — breaks scoring.

**Fix:** Implemented in `rebuild_from_scratch_v2.py`.

---

### Issue #3: Missing NTEE1 Classification
**Severity:** HIGH  
**Count:** 582,550 orgs (29.4% of total)  
**By Source:**
- EO_990N: 249,592 missing (70.6% of 990-N records)
- IRS_BMF: 332,958 missing (20.5% of BMF records)

**Impact:** 
- Cannot assign peer groups (depends on NTEE1)
- Cannot compute v4 or v5 scores (both group by NTEE1)
- Browse filters by cause/category become unreliable

**Root Cause:** Source data has many orgs with unclassifiable or missing NTEE codes.

**Fix:** `rebuild_from_scratch_v2.py` logs these as "unclassifiable NTEE" and allows them to load (NTEE1 = NULL), but they won't be scoreable. This is data-driven and acceptable — we can't invent classifications.

---

### Issue #4: Invalid STATE Codes
**Severity:** MEDIUM  
**Count:** 1,377 orgs with empty STATE (blank string)  
**Additional:** 62 unique STATE values (too many — should be ≤57 valid US states/territories)

**Impact:**
- Empty STATE breaks geography filtering
- Some orgs have invalid state codes (e.g., empty, "AA", "AS", etc.)

**Root Cause:** Source CSV had blank STATE; rebuild script accepted it.

**Fix:** `rebuild_from_scratch_v2.py` now validates STATE against whitelist of 50 US states + territories (AL, AK, ..., VI) and rejects invalid ones.

---

### Issue #5: Missing Critical Fields
**Severity:** MEDIUM  
**Count:**
- mission: 0 orgs (not yet backfilled)
- website: 0 orgs (not yet backfilled)
- donate_url: 0 orgs (discovery pipeline not run)

**Impact:** Browse pages show incomplete org data; "similar organizations" recommendation cannot run without embeddings.

**Fix:** Not part of this rebuild. These will be backfilled by separate pipelines:
- `generate_missions.py` → fills mission (via AI + NTEE labels)
- `web_finder_agent.py` → fills website
- `donation_link_pipeline.py` → fills donate_url

---

## Validation Checklist

After rebuild, verify with `python3 scripts/validate_database.py`:

- [ ] No NULLs in required columns (EIN, organization_name, STATE, subsection, deductibility, updated_at)
- [ ] No invalid deductibility values (must be 0 or 1)
- [ ] No invalid STATE codes (must be 2-char valid code)
- [ ] No negative revenue or expense values
- [ ] No program_expense_pct > 100%
- [ ] NTEE1 coverage ≥ 70% (29% unclassifiable is acceptable from source)
- [ ] All STATE values are valid 2-char codes

---

## Pipeline Changes

### What Changed
1. **`rebuild_from_scratch.py`** → **`rebuild_from_scratch_v2.py`**
   - Added validation gates for all incoming data
   - Rejects rows with invalid STATE, negative revenue/expenses, missing names
   - Logs all filtered rows with reason for auditability
   - Improved schema with NOT NULL constraints

2. **New validation script** → **`validate_database.py`**
   - Runs post-rebuild to detect corruption before deployment
   - Checks all critical fields, data validity, coverage stats
   - Generates audit report with examples of bad data

### Usage

```bash
# Rebuild with validation
python3 scripts/rebuild_from_scratch_v2.py

# Validate the result
python3 scripts/validate_database.py
```

---

## Future Prevention

**In CLAUDE.md:**
> Before any future data pipeline runs that modify `registry_enriched`, ensure:
> 1. New/modified `rebuild_from_scratch.py` includes validation gates for the new data source
> 2. `validate_database.py` is run post-rebuild and must pass all checks
> 3. No negative values allowed in numeric fields
> 4. STATE, NTEE1, and other categorical fields must be validated against known lists
> 5. All NULL counts in required fields must be logged and justified

---

## References

- **Script:** `/home/akbar/meritgiving/scripts/rebuild_from_scratch_v2.py` (improved rebuild with validation)
- **Validator:** `/home/akbar/meritgiving/scripts/validate_database.py` (post-rebuild health check)
- **Data:** `data/bmf.csv` (IRS Business Master File) + `data/eo*.csv` (990-N extracts)
- **API:** `daanaa_api.py` (depends on clean, validated database)

---

**Date:** 2026-06-16  
**Auditor:** Claude Code  
**Status:** Audit complete; rebuild scripts ready for execution
