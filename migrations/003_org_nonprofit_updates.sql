-- Migration 003: Create org_nonprofit_updates table for nonprofit-submitted data corrections
-- Purpose: Stores nonprofit-submitted financial data updates during claiming flow
-- Used during pre-claim review and incorporated into nightly scoring runs

CREATE TABLE IF NOT EXISTS org_nonprofit_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    claim_token TEXT NOT NULL UNIQUE,

    -- Original IRS data (from registry_enriched)
    irs_total_revenue REAL,
    irs_total_expenses REAL,
    irs_program_expense_pct REAL,
    irs_months_of_reserve REAL,
    irs_tax_year INTEGER,

    -- Nonprofit-submitted updates (during claiming)
    submitted_total_revenue REAL,
    submitted_total_expenses REAL,
    submitted_program_expense_pct REAL,
    submitted_months_of_reserve REAL,
    submitted_explanation TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Review & processing
    status TEXT DEFAULT 'pending_review',
    -- Values: pending_review, validated, pending_scoring, included_in_run, rejected

    sanity_check_failed INTEGER DEFAULT 0,  -- 1 if >50% change in any metric
    admin_notes TEXT,
    validated_at TIMESTAMP,
    validated_by TEXT,

    -- Scoring integration
    scoring_run_date TIMESTAMP,  -- Which run will include this
    included_in_run_at TIMESTAMP,
    result_v5_percentile REAL,
    result_health_signal TEXT,

    FOREIGN KEY (ein) REFERENCES registry_enriched(EIN)
);

-- Index for quick lookups by EIN and claim_token
CREATE INDEX IF NOT EXISTS idx_nonprofit_updates_ein ON org_nonprofit_updates(ein);
CREATE INDEX IF NOT EXISTS idx_nonprofit_updates_claim_token ON org_nonprofit_updates(claim_token);
CREATE INDEX IF NOT EXISTS idx_nonprofit_updates_status ON org_nonprofit_updates(status);
CREATE INDEX IF NOT EXISTS idx_nonprofit_updates_submitted_at ON org_nonprofit_updates(submitted_at);
CREATE INDEX IF NOT EXISTS idx_nonprofit_updates_scoring_run ON org_nonprofit_updates(scoring_run_date);

-- Table to track which updates are included in which scoring runs
CREATE TABLE IF NOT EXISTS org_nonprofit_update_scoring_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    update_id INTEGER NOT NULL,
    scoring_run_id INTEGER,
    scoring_run_date TIMESTAMP,
    included_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (update_id) REFERENCES org_nonprofit_updates(id)
);

CREATE INDEX IF NOT EXISTS idx_update_scoring_runs_update_id ON org_nonprofit_update_scoring_runs(update_id);
CREATE INDEX IF NOT EXISTS idx_update_scoring_runs_date ON org_nonprofit_update_scoring_runs(scoring_run_date);
