-- Track anonymized bookmark analytics for nonprofit dashboards
-- Privacy-first: no user IDs, no tracking, completely aggregated
-- Nonprofits opt-in by claiming their org and can view their metrics

CREATE TABLE IF NOT EXISTS wallet_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    cause_tag TEXT,
    location_state TEXT,
    location_city TEXT,
    bookmark_count INTEGER DEFAULT 1,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast queries by org
CREATE INDEX IF NOT EXISTS idx_analytics_ein ON wallet_analytics(ein);
CREATE INDEX IF NOT EXISTS idx_analytics_cause ON wallet_analytics(ein, cause_tag);
CREATE INDEX IF NOT EXISTS idx_analytics_location ON wallet_analytics(ein, location_state, location_city);

-- Monthly aggregations (for trend tracking, faster queries)
CREATE TABLE IF NOT EXISTS wallet_analytics_monthly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    month_year TEXT NOT NULL,  -- YYYY-MM format
    total_bookmarks INTEGER DEFAULT 0,
    unique_cause_tags INTEGER DEFAULT 0,
    top_causes TEXT,  -- JSON array of {tag, count}
    top_locations TEXT,  -- JSON array of {city, state, count}
    last_computed DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_monthly_ein_month ON wallet_analytics_monthly(ein, month_year);
