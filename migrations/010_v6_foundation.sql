-- Daanaa v6 data foundation (additive and rerunnable)
-- Creates source-traceable tables without altering legacy data.

CREATE TABLE IF NOT EXISTS org_financial_years (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    tax_year INTEGER NOT NULL,
    filing_form TEXT,
    source_name TEXT NOT NULL,
    source_record_id TEXT,
    source_url TEXT,
    retrieved_at TEXT,
    record_hash TEXT,
    total_revenue REAL,
    contributions_and_grants REAL,
    program_service_revenue REAL,
    investment_income REAL,
    membership_dues REAL,
    government_grants REAL,
    other_revenue REAL,
    total_expenses REAL,
    program_expenses REAL,
    management_expenses REAL,
    fundraising_expenses REAL,
    total_assets REAL,
    total_liabilities REAL,
    net_assets REAL,
    employees INTEGER,
    volunteers INTEGER,
    months_of_reserve REAL,
    data_quality_status TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ein, tax_year, source_name, source_record_id)
);
CREATE INDEX IF NOT EXISTS idx_org_fy_ein ON org_financial_years(ein);
CREATE INDEX IF NOT EXISTS idx_org_fy_year ON org_financial_years(tax_year);

CREATE TABLE IF NOT EXISTS org_classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    classification_type TEXT NOT NULL,
    classification_value TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_url TEXT,
    confidence TEXT,
    is_inferred INTEGER DEFAULT 0,
    effective_from TEXT,
    effective_to TEXT,
    reviewed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ein, classification_type, classification_value, source_name)
);
CREATE INDEX IF NOT EXISTS idx_org_class_ein ON org_classifications(ein);
CREATE INDEX IF NOT EXISTS idx_org_class_type ON org_classifications(classification_type);

CREATE TABLE IF NOT EXISTS org_operating_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    tax_year INTEGER NOT NULL,
    program_count INTEGER,
    populations_served TEXT,
    geographic_service_area TEXT,
    employee_count INTEGER,
    volunteer_count INTEGER,
    board_size INTEGER,
    board_independent_count INTEGER,
    program_expense_ratio REAL,
    overhead_ratio REAL,
    source_name TEXT NOT NULL,
    source_url TEXT,
    retrieved_at TEXT,
    confidence TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ein, tax_year, source_name)
);
CREATE INDEX IF NOT EXISTS idx_org_ctx_ein ON org_operating_context(ein);
CREATE INDEX IF NOT EXISTS idx_org_ctx_year ON org_operating_context(tax_year);

CREATE TABLE IF NOT EXISTS org_data_assertions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    field_name TEXT NOT NULL,
    proposed_value TEXT,
    source_type TEXT NOT NULL,
    source_url TEXT,
    submitted_by_org INTEGER DEFAULT 0,
    review_status TEXT,
    reviewed_by TEXT,
    reviewed_at TEXT,
    effective_from TEXT,
    effective_to TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ein, field_name, source_type)
);
CREATE INDEX IF NOT EXISTS idx_org_assert_ein ON org_data_assertions(ein);

CREATE TABLE IF NOT EXISTS ingestion_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    batch_id TEXT NOT NULL,
    source_record_count INTEGER,
    valid_records INTEGER,
    quarantined_records INTEGER,
    duplicate_records INTEGER,
    validation_errors TEXT,
    ingested_at TEXT DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    UNIQUE(source_name, batch_id)
);

CREATE TABLE IF NOT EXISTS ingestion_quarantine (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    source_record_id TEXT,
    record_type TEXT,
    raw_data TEXT NOT NULL,
    validation_errors TEXT NOT NULL,
    quarantined_at TEXT DEFAULT CURRENT_TIMESTAMP,
    reviewed_by TEXT,
    resolution_notes TEXT,
    resolved_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_quarantine_source ON ingestion_quarantine(source_name);
CREATE INDEX IF NOT EXISTS idx_quarantine_status ON ingestion_quarantine(resolved_at);
