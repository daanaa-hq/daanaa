-- Track nonprofit-submitted financial updates
-- These override IRS data for scoring purposes and can be corrected before scoring

CREATE TABLE IF NOT EXISTS org_nonprofit_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    claim_token TEXT NOT NULL UNIQUE,

    -- Original IRS data (for comparison)
    irs_total_revenue REAL,
    irs_total_expenses REAL,
    irs_program_expense_pct REAL,
    irs_months_of_reserve REAL,
    irs_tax_year INTEGER,

    -- Nonprofit-submitted updates
    submitted_total_revenue REAL,
    submitted_total_expenses REAL,
    submitted_program_expense_pct REAL,
    submitted_months_of_reserve REAL,
    submitted_explanation TEXT,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Review & processing
    status TEXT DEFAULT 'pending_review',  -- pending_review, validated, included_in_run, flagged, rejected
    admin_notes TEXT,
    validated_at DATETIME,
    validated_by TEXT,
    included_in_run_at DATETIME,

    -- Flags for manual review
    revenue_change_pct REAL,  -- % change from IRS
    expense_change_pct REAL,
    sanity_check_failed BOOLEAN DEFAULT 0,

    FOREIGN KEY (ein) REFERENCES registry_enriched(EIN),
    CONSTRAINT valid_revenue CHECK (submitted_total_revenue IS NULL OR submitted_total_revenue >= 0),
    CONSTRAINT valid_expenses CHECK (submitted_total_expenses IS NULL OR submitted_total_expenses >= 0),
    CONSTRAINT valid_program_pct CHECK (submitted_program_expense_pct IS NULL OR (submitted_program_expense_pct >= 0 AND submitted_program_expense_pct <= 100)),
    CONSTRAINT valid_reserves CHECK (submitted_months_of_reserve IS NULL OR submitted_months_of_reserve >= -1)
);

CREATE INDEX IF NOT EXISTS idx_updates_ein ON org_nonprofit_updates(ein);
CREATE INDEX IF NOT EXISTS idx_updates_status ON org_nonprofit_updates(status);
CREATE INDEX IF NOT EXISTS idx_updates_submitted_at ON org_nonprofit_updates(submitted_at);
CREATE INDEX IF NOT EXISTS idx_updates_flagged ON org_nonprofit_updates(sanity_check_failed) WHERE sanity_check_failed = 1;

-- Track which scoring run included which updates
CREATE TABLE IF NOT EXISTS org_update_scoring_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    update_id INTEGER NOT NULL,
    scoring_run_id TEXT,  -- reference to score_snapshots or run log
    run_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    result_v5_percentile REAL,
    result_health_signal TEXT,
    result_archetype TEXT,
    result_band TEXT,
    FOREIGN KEY (update_id) REFERENCES org_nonprofit_updates(id)
);

CREATE INDEX IF NOT EXISTS idx_run_tracking_update ON org_update_scoring_runs(update_id);
CREATE INDEX IF NOT EXISTS idx_run_tracking_date ON org_update_scoring_runs(run_date);
