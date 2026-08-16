-- Migration 023: org_revenue_history + irs_990_functional_expense_filings
-- Date: 2026-08-16
-- Founder-approved (2026-08-16 session) after both were scoped in DECISIONS.md.
--
-- Two additive, standalone tables. Neither touches registry_enriched's
-- existing columns. Both have a clean rollback (DROP TABLE, no data loss
-- to any live-served field).
--
-- 1. org_revenue_history: backs the real 5-year financial trends feature
--    (FinancialTrends.tsx was found showing a fabricated "5-year history
--    available" claim with no real data behind it -- see DECISIONS.md
--    2026-08-16 "FinancialTrends claimed 5-year history it never had").
--    Sourced from data/cache/gt990_latest.csv (per-EIN, per-year rows,
--    already contains TotalRevenueCY/TotalAssetsBkEOY/TaxYear pre-extracted,
--    no XML download needed for this table). Validated feasible: 95.8% of
--    a 2,000-org large-org sample had 5+ years of history available.
--
-- 2. irs_990_functional_expense_filings: evidence table for recovering
--    trustworthy program/management/fundraising expense figures (Track B,
--    see DECISIONS.md 2026-08-16 "Expense breakdown chart hidden site-wide").
--    Confirmed the existing registry_enriched.program_expenses/
--    management_expenses/fundraising_expenses/program_expense_pct columns
--    are unreliable at scale two independent ways; this table is populated
--    from direct 990 XML Part IX parsing, kept separate from and never
--    overwriting the legacy columns, until validated at scale.

CREATE TABLE IF NOT EXISTS org_revenue_history (
    EIN             TEXT NOT NULL,
    tax_year        INTEGER NOT NULL,
    total_revenue   REAL,
    total_assets    REAL,
    total_expenses  REAL,
    form_type       TEXT,               -- '990' only for now (EZ/PF have a different statement shape)
    source          TEXT DEFAULT 'gt990_index',
    extracted_at    TEXT,
    PRIMARY KEY (EIN, tax_year)
);
CREATE INDEX IF NOT EXISTS idx_org_revenue_history_ein ON org_revenue_history(EIN);

CREATE TABLE IF NOT EXISTS irs_990_functional_expense_filings (
    EIN                     TEXT NOT NULL,
    tax_year                INTEGER NOT NULL,
    object_id               TEXT,       -- gt990 index ObjectId, identifies the specific filing
    source_url              TEXT,       -- S3 URL of the raw XML, for auditability
    file_sha256             TEXT,       -- gt990 index checksum
    total_amt               REAL,       -- Part IX line 25, column A
    program_services_amt    REAL,       -- Part IX line 25, column B
    management_general_amt  REAL,       -- Part IX line 25, column C
    fundraising_amt         REAL,       -- Part IX line 25, column D
    reconciles              INTEGER,    -- 1 if B+C+D matches A within $1, else 0
    validation_status       TEXT DEFAULT 'pending',  -- 'pending' | 'accepted' | 'rejected'
    rejection_reason        TEXT,
    parser_version          TEXT,
    extracted_at            TEXT,
    PRIMARY KEY (EIN, tax_year, object_id)
);
CREATE INDEX IF NOT EXISTS idx_irs990_expense_ein ON irs_990_functional_expense_filings(EIN);
CREATE INDEX IF NOT EXISTS idx_irs990_expense_status ON irs_990_functional_expense_filings(validation_status);
