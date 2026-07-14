-- Phase 6: Donor Learning System
-- Track giving impact, learning journeys, and result analytics (privacy-first)

CREATE TABLE IF NOT EXISTS donor_learning_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id TEXT NOT NULL UNIQUE,  -- anonymous hash, no PII
    cause_interests TEXT,  -- JSON array of NTEE codes
    size_preference TEXT,  -- 'micro', 'professional', 'established'
    giving_style TEXT,  -- 'one_time', 'monthly', 'annual'
    learning_preference TEXT,  -- 'research', 'stories', 'metrics', 'mixed'
    outcome_focus TEXT,  -- 'scale', 'depth', 'innovation', 'resilience'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS donor_giving_intent (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id TEXT NOT NULL,
    ein TEXT NOT NULL,
    intent_amount_estimate INTEGER,  -- $
    intent_frequency TEXT,  -- 'one_time', 'monthly', 'annual'
    intention_date TIMESTAMP,
    likelihood_score REAL DEFAULT 0.0,  -- 0-1, based on interaction
    status TEXT DEFAULT 'considered' CHECK (status IN ('considering', 'committed', 'completed', 'abandoned')),
    intent_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(donor_id, ein)
);

CREATE TABLE IF NOT EXISTS impact_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id TEXT NOT NULL,
    ein TEXT NOT NULL,
    outcome_type TEXT,  -- 'people_served', 'funds_leveraged', 'policy_change', 'capacity_built', 'research_published'
    outcome_value REAL,
    outcome_unit TEXT,  -- 'people', 'dollars', 'policies', 'organizations'
    outcome_timeframe TEXT,  -- 'immediate', '6_months', '1_year', '2_years'
    report_source TEXT,  -- 'org_reported', 'third_party', 'inferred'
    confidence_score REAL DEFAULT 0.5,  -- 0-1
    last_reported TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS donor_learning_cohorts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cohort_name TEXT NOT NULL,
    cohort_topic TEXT,  -- 'climate', 'education', 'health', 'economic_justice', etc.
    cohort_type TEXT CHECK (cohort_type IN ('topic_focused', 'impact_focused', 'methodology', 'peer_learning')),
    member_count INTEGER DEFAULT 0,
    duration_weeks INTEGER DEFAULT 8,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    facilitator TEXT,  -- Can be org, expert, peer
    description TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('forming', 'active', 'completed', 'archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cohort_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cohort_id INTEGER NOT NULL,
    donor_id TEXT NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active' CHECK (status IN ('invited', 'active', 'completed', 'dropped')),
    UNIQUE(cohort_id, donor_id),
    FOREIGN KEY (cohort_id) REFERENCES donor_learning_cohorts(id)
);

CREATE TABLE IF NOT EXISTS learning_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_type TEXT CHECK (resource_type IN ('research_paper', 'case_study', 'podcast', 'webinar', 'video', 'guide')),
    title TEXT NOT NULL,
    description TEXT,
    cause_area TEXT,  -- NTEE code
    url TEXT,
    source TEXT,  -- 'daanaa', 'external_partner', 'nonprofit'
    published_at TIMESTAMP,
    view_count INTEGER DEFAULT 0,
    completion_rate REAL DEFAULT 0.0,  -- % of started who finished
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS learning_engagement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id TEXT NOT NULL,
    resource_id INTEGER NOT NULL,
    engagement_type TEXT CHECK (engagement_type IN ('view', 'started', 'completed', 'shared')),
    duration_seconds INTEGER,  -- Time spent
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resource_id) REFERENCES learning_resources(id)
);

CREATE TABLE IF NOT EXISTS donor_result_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id TEXT NOT NULL,
    reporting_period TEXT,  -- 'monthly', 'quarterly', 'annual'
    total_giving_amount INTEGER,  -- $
    org_count INTEGER,  -- How many orgs supported
    cause_diversity TEXT,  -- JSON array of causes
    impact_summary TEXT,  -- "You supported 3 orgs, reached ~500 people"
    learning_summary TEXT,  -- "Completed 2 courses, joined 1 peer cohort"
    progress_vs_goals TEXT,  -- How are goals tracking?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices for common queries
CREATE INDEX IF NOT EXISTS idx_donor_profiles_cause ON donor_learning_profiles(cause_interests);
CREATE INDEX IF NOT EXISTS idx_giving_intent_donor ON donor_giving_intent(donor_id, status);
CREATE INDEX IF NOT EXISTS idx_impact_tracking_donor ON impact_tracking(donor_id, ein);
CREATE INDEX IF NOT EXISTS idx_cohort_active ON donor_learning_cohorts(status, start_date DESC);
CREATE INDEX IF NOT EXISTS idx_cohort_participants_donor ON cohort_participants(donor_id, status);
CREATE INDEX IF NOT EXISTS idx_learning_resources_cause ON learning_resources(cause_area);
CREATE INDEX IF NOT EXISTS idx_engagement_donor ON learning_engagement(donor_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_donor ON donor_result_analytics(donor_id, reporting_period DESC);
