-- Phase 11: Financial Health Coaching
-- Proactive guidance, early warning, stress testing, peer benchmarking

CREATE TABLE IF NOT EXISTS nonprofit_financial_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL UNIQUE,
    assessment_date TIMESTAMP,
    reserve_ratio REAL,  -- months of reserves
    reserve_months_ideal REAL DEFAULT 6.0,
    reserve_trend TEXT,  -- 'improving', 'stable', 'declining'
    revenue_volatility REAL,  -- std dev of last 3 years
    expense_trend REAL,  -- % growth YoY
    revenue_concentration REAL,  -- % from top funder
    funder_diversity_score REAL,  -- 0-1, higher is better
    health_signal TEXT CHECK (health_signal IN ('HEALTHY', 'STABLE', 'CAUTION', 'CRISIS')),
    signal_confidence REAL DEFAULT 0.8,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS financial_health_guidance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    guidance_type TEXT CHECK (guidance_type IN ('reserve_strength', 'revenue_diversity', 'expense_management', 'funder_risk', 'growth_sustainability')),
    current_status TEXT,  -- "2 months reserves (below 6-month target)"
    recommendation TEXT,  -- "Consider diversifying funding sources"
    urgency_level TEXT CHECK (urgency_level IN ('low', 'medium', 'high', 'critical')),
    peer_comparison TEXT,  -- "Peers in your size have 4.5 months avg reserves"
    action_link TEXT,  -- URL to relevant resource/partner
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS financial_stress_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    test_type TEXT CHECK (test_type IN ('top_funder_loss', 'revenue_decline', 'expense_spike', 'combined_shock')),
    test_scenario TEXT,  -- "Top funder withdraws support (20% of revenue)"
    current_reserves_months REAL,
    post_shock_reserves_months REAL,
    survival_months INTEGER,  -- How long can you operate?
    risk_level TEXT CHECK (risk_level IN ('low', 'moderate', 'high', 'critical')),
    mitigation_strategies TEXT,  -- JSON array of recommendations
    tested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS peer_benchmarking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    peer_group TEXT,  -- NTEE + size bracket + region
    metric_type TEXT,  -- 'reserve_ratio', 'revenue_volatility', 'expense_ratio', 'funder_diversity'
    your_value REAL,
    peer_median REAL,
    peer_25th_percentile REAL,
    peer_75th_percentile REAL,
    your_rank INTEGER,  -- Position among peers
    peer_total INTEGER,  -- Total in peer group
    interpretation TEXT,  -- "Your reserves are above peer median"
    benchmarked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS financial_health_coaching_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    session_type TEXT CHECK (session_type IN ('quarterly_review', 'crisis_support', 'planning', 'peer_learning')),
    topic TEXT,  -- "Reserve Building", "Funder Diversification", etc.
    coach_type TEXT,  -- 'automated', 'peer', 'specialist'
    session_notes TEXT,
    recommendations TEXT,  -- JSON array
    follow_up_actions TEXT,  -- JSON
    status TEXT DEFAULT 'active' CHECK (status IN ('scheduled', 'active', 'completed', 'deferred')),
    scheduled_date TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS financial_goal_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    goal_type TEXT CHECK (goal_type IN ('reserve_target', 'revenue_diversification', 'cost_reduction', 'margin_improvement')),
    goal_description TEXT,  -- "Build 6-month reserve fund"
    goal_target REAL,  -- Target value (months, %, dollars)
    goal_deadline TIMESTAMP,
    current_progress REAL,  -- How far along
    progress_percent INTEGER,  -- 0-100%
    status TEXT DEFAULT 'active' CHECK (status IN ('new', 'active', 'achieved', 'paused', 'abandoned')),
    milestones TEXT,  -- JSON array of checkpoints
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS financial_advisor_marketplace (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    advisor_ein TEXT NOT NULL,  -- Consulting org
    advisor_name TEXT,
    specialization TEXT,  -- 'reserves', 'fundraising', 'grants', 'compliance'
    experience_level TEXT CHECK (experience_level IN ('emerging', 'established', 'expert')),
    nonprofits_served INTEGER DEFAULT 0,
    rating REAL,  -- 0-5 stars from nonprofit feedback
    hourly_rate_low INTEGER,
    hourly_rate_high INTEGER,
    bio TEXT,
    available_for TEXT,  -- JSON array of services
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices for common queries
CREATE INDEX IF NOT EXISTS idx_health_ein ON nonprofit_financial_health(ein, health_signal);
CREATE INDEX IF NOT EXISTS idx_guidance_ein ON financial_health_guidance(ein, urgency_level);
CREATE INDEX IF NOT EXISTS idx_stress_tests_ein ON financial_stress_tests(ein, risk_level);
CREATE INDEX IF NOT EXISTS idx_benchmarking_peer_group ON peer_benchmarking(peer_group, metric_type);
CREATE INDEX IF NOT EXISTS idx_coaching_ein ON financial_health_coaching_sessions(ein, status);
CREATE INDEX IF NOT EXISTS idx_goals_ein ON financial_goal_tracking(ein, status);
CREATE INDEX IF NOT EXISTS idx_advisor_spec ON financial_advisor_marketplace(specialization, experience_level);
