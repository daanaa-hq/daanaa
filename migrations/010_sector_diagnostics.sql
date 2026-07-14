-- Phase 10: Sector Health Diagnostics
-- Analyze cause areas, movement capacity, collaboration patterns, research data

CREATE TABLE IF NOT EXISTS sector_health_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cause_area TEXT NOT NULL,  -- NTEE1 code
    org_count INTEGER,
    total_revenue_millions REAL,
    median_revenue REAL,
    avg_financial_health_score REAL,
    healthy_pct REAL,  -- % with HEALTHY signal
    stable_pct REAL,
    caution_pct REAL,
    growth_rate REAL,  -- YoY change
    median_reserve_months REAL,
    avg_peer_percentile REAL,
    leadership_turnover_pct REAL,
    created_org_count INTEGER,  -- new orgs this period
    closed_org_count INTEGER,
    UNIQUE(cause_area, snapshot_date)
);

CREATE TABLE IF NOT EXISTS sector_coverage_gaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cause_area TEXT NOT NULL,
    geographic_region TEXT,  -- state or region
    service_type TEXT,  -- 'direct_service', 'policy', 'research', 'capacity_building'
    target_population TEXT,
    coverage_assessment TEXT,  -- 'strong', 'moderate', 'weak', 'none'
    org_count_in_gap INTEGER,
    population_served_estimate INTEGER,
    notes TEXT,
    last_assessed TIMESTAMP,
    UNIQUE(cause_area, geographic_region, service_type, target_population)
);

CREATE TABLE IF NOT EXISTS sector_collaboration_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein_1 TEXT NOT NULL,
    ein_2 TEXT NOT NULL,
    collaboration_strength FLOAT,  -- 0-1, based on overlap
    target_population_overlap FLOAT,  -- % overlap in who they serve
    geographic_overlap FLOAT,  -- % geographic overlap
    funding_opportunity BOOLEAN,  -- could benefit from co-funding?
    suggested_action TEXT,
    assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ein_1, ein_2)
);

CREATE TABLE IF NOT EXISTS sector_research_datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    research_name TEXT NOT NULL,
    cause_area TEXT,
    data_type TEXT CHECK (data_type IN ('financial_trends', 'movement_health', 'impact_analysis', 'funder_flows', 'leadership_pipeline')),
    description TEXT,
    methodology TEXT,
    findings_summary TEXT,
    published_at TIMESTAMP,
    org_count_analyzed INTEGER,
    years_covered TEXT,  -- '2020-2026'
    download_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sector_funding_flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period TEXT,  -- '2026-Q2'
    cause_area TEXT,
    funding_source TEXT,  -- 'individual', 'foundation', 'government', 'corporate'
    total_funding_millions REAL,
    top_funder_ein TEXT,
    top_funder_pct REAL,  -- % of funding from top funder
    concentration_score REAL,  -- Gini coefficient of concentration
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(period, cause_area, funding_source)
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_sector_snapshots_cause ON sector_health_snapshots(cause_area, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_coverage_gaps_cause ON sector_coverage_gaps(cause_area, coverage_assessment);
CREATE INDEX IF NOT EXISTS idx_collab_signals_ein ON sector_collaboration_signals(ein_1, collaboration_strength DESC);
CREATE INDEX IF NOT EXISTS idx_research_cause ON sector_research_datasets(cause_area, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_funding_flows_cause ON sector_funding_flows(cause_area, period);
