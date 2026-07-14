-- Phase 13: Impact Measurement Infrastructure
-- Standardize measurement without enforcing one-size-fits-all

CREATE TABLE IF NOT EXISTS cause_outcome_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cause_area TEXT NOT NULL,  -- NTEE code
    program_type TEXT,  -- 'direct_service', 'advocacy', 'research', 'capacity_building'
    outcome_framework TEXT NOT NULL,  -- Name of framework (e.g., "Education Learning Outcomes")
    description TEXT,
    key_metrics TEXT,  -- JSON array of recommended metrics
    measurement_methods TEXT,  -- JSON: how to collect data
    reporting_frequency TEXT,  -- 'monthly', 'quarterly', 'annual'
    difficulty_to_measure TEXT CHECK (difficulty_to_measure IN ('easy', 'moderate', 'difficult')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nonprofit_impact_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    reporting_period TEXT,  -- 'FY2026', 'Q3 2026'
    program_name TEXT,
    outcome_type TEXT,  -- 'people_served', 'lives_changed', 'community_reached'
    measurement_method TEXT,  -- 'surveys', 'admin_data', 'research', 'mixed'
    outcome_value REAL,
    outcome_unit TEXT,  -- 'people', 'dollars', 'policies', 'lives'
    confidence_level TEXT CHECK (confidence_level IN ('high', 'moderate', 'low')),
    data_quality_notes TEXT,
    reported_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS peer_outcome_benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cause_area TEXT,
    program_type TEXT,
    outcome_type TEXT,
    median_outcome_value REAL,
    percentile_25 REAL,
    percentile_75 REAL,
    org_count_reporting INTEGER,
    year_reported INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS donor_impact_attribution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id TEXT,
    ein TEXT,
    grant_amount INTEGER,
    program_name TEXT,
    impact_outcomes TEXT,  -- JSON array
    impact_attribution_method TEXT,  -- 'direct_program', 'organizational', 'estimated'
    direct_outcomes REAL,  -- How many people/dollars attributed directly
    organizational_impact TEXT,  -- "Your support helped build capacity for X"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS research_grade_datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_name TEXT NOT NULL,
    cause_area TEXT,
    description TEXT,
    data_type TEXT CHECK (data_type IN ('outcome_data', 'process_data', 'cost_data', 'participant_data')),
    org_count INTEGER,  -- How many orgs contributed?
    record_count INTEGER,  -- How many records?
    years_covered TEXT,  -- '2020-2026'
    anonymized INTEGER DEFAULT 1,
    aggregated INTEGER DEFAULT 1,
    access_level TEXT CHECK (access_level IN ('public', 'academic', 'nonprofit_partners')),
    download_url TEXT,
    methodology TEXT,
    limitations TEXT,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS impact_trend_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    outcome_type TEXT,
    year INTEGER,
    outcome_value REAL,
    trend_direction TEXT CHECK (trend_direction IN ('improving', 'stable', 'declining', 'unknown')),
    confidence REAL DEFAULT 0.5,
    analysis_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_templates_cause ON cause_outcome_templates(cause_area, program_type);
CREATE INDEX IF NOT EXISTS idx_reports_ein ON nonprofit_impact_reports(ein, reporting_period DESC);
CREATE INDEX IF NOT EXISTS idx_benchmarks_cause ON peer_outcome_benchmarks(cause_area, outcome_type);
CREATE INDEX IF NOT EXISTS idx_attribution_donor ON donor_impact_attribution(donor_id);
CREATE INDEX IF NOT EXISTS idx_datasets_access ON research_grade_datasets(access_level);
CREATE INDEX IF NOT EXISTS idx_trends_ein ON impact_trend_analysis(ein, outcome_type);
