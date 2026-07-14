-- Stewardship language fix: CAUTION → NEED_SUPPORT
-- Reason: nonprofits designed to run lean; "need support" invites action, not shame
-- Affects: nonprofit_financial_health table schema + all rows with CAUTION signal

-- Recreate table with updated CHECK constraint
DROP INDEX IF EXISTS idx_health_ein;
ALTER TABLE nonprofit_financial_health RENAME TO nonprofit_financial_health_old;

CREATE TABLE nonprofit_financial_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL UNIQUE,
    assessment_date TIMESTAMP,
    reserve_ratio REAL,
    reserve_months_ideal REAL DEFAULT 6.0,
    reserve_trend TEXT,
    revenue_volatility REAL,
    expense_trend REAL,
    revenue_concentration REAL,
    funder_diversity_score REAL,
    health_signal TEXT CHECK (health_signal IN ('HEALTHY', 'STABLE', 'NEED_SUPPORT', 'CRISIS')),
    signal_confidence REAL DEFAULT 0.8,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO nonprofit_financial_health
  SELECT id, ein, assessment_date, reserve_ratio, reserve_months_ideal,
         reserve_trend, revenue_volatility, expense_trend, revenue_concentration,
         funder_diversity_score,
         CASE WHEN health_signal = 'CAUTION' THEN 'NEED_SUPPORT' ELSE health_signal END,
         signal_confidence, created_at, updated_at
  FROM nonprofit_financial_health_old;

CREATE INDEX idx_health_ein ON nonprofit_financial_health(ein, health_signal);

DROP TABLE nonprofit_financial_health_old;
