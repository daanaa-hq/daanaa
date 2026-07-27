-- Conditional peer context for organizations without usable revenue.
-- Additive, versioned, and never a substitute for an organization's own data.

CREATE TABLE IF NOT EXISTS v6_conditional_band_context (
    run_id TEXT NOT NULL,
    peer_group_key TEXT NOT NULL,
    ntee_code TEXT NOT NULL,
    geography_scope TEXT NOT NULL,
    geography_value TEXT NOT NULL,
    archetype TEXT NOT NULL,
    revenue_band TEXT NOT NULL,
    peer_count INTEGER NOT NULL,
    scoreable_peer_count INTEGER NOT NULL,
    median_reserves REAL,
    p25_reserves REAL,
    p75_reserves REAL,
    source_year_min INTEGER,
    source_year_max INTEGER,
    confidence TEXT NOT NULL,
    methodology_version TEXT NOT NULL,
    PRIMARY KEY (run_id, peer_group_key, revenue_band),
    FOREIGN KEY (run_id) REFERENCES v6_scoring_runs(run_id)
);
CREATE INDEX IF NOT EXISTS idx_v6_conditional_group
    ON v6_conditional_band_context(run_id, ntee_code, geography_scope, geography_value, archetype);
