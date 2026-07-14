-- Phase 12: Succession Planning Toolkit
-- Support leadership transitions and institutional continuity

CREATE TABLE IF NOT EXISTS succession_readiness (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL UNIQUE,
    assessment_date TIMESTAMP,
    leadership_pipeline_strength REAL DEFAULT 0.0,  -- 0-1
    board_strength REAL DEFAULT 0.0,
    knowledge_transfer_status REAL DEFAULT 0.0,
    organizational_readiness_score REAL DEFAULT 0.0,
    risk_level TEXT CHECK (risk_level IN ('low', 'moderate', 'high', 'critical')),
    risk_factors TEXT,  -- JSON array of concerns
    readiness_narrative TEXT,
    action_items TEXT,  -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS succession_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    candidate_name TEXT,
    position_applied_for TEXT,
    internal_external TEXT CHECK (internal_external IN ('internal', 'external')),
    relevant_experience TEXT,
    fit_score REAL DEFAULT 0.0,  -- 0-1
    readiness_level TEXT CHECK (readiness_level IN ('ready_now', 'ready_6mo', 'ready_12mo', 'developing')),
    development_plan TEXT,
    mentorship_assigned TEXT,
    interview_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transition_timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    outgoing_leader_name TEXT,
    incoming_leader_name TEXT,
    transition_start_date TIMESTAMP,
    transition_end_date TIMESTAMP,
    phase TEXT,  -- 'announcement', 'overlap', 'handoff', 'onboarding'
    milestones TEXT,  -- JSON
    knowledge_transfer_plan TEXT,
    communication_plan TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS board_development_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    plan_date TIMESTAMP,
    board_gaps TEXT,  -- Skills/expertise needed
    recruitment_targets TEXT,  -- JSON: needed skills, diversity goals
    development_priorities TEXT,  -- Training, team building, governance
    timeline TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_readiness_ein ON succession_readiness(ein, risk_level);
CREATE INDEX IF NOT EXISTS idx_candidates_ein ON succession_candidates(ein, readiness_level);
CREATE INDEX IF NOT EXISTS idx_transition_ein ON transition_timeline(ein, transition_start_date DESC);
