-- Phase 9: Nonprofit Peer Network
-- Keystone feature: peer connections, resource sharing, mutual aid, learning

CREATE TABLE IF NOT EXISTS nonprofit_peer_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein_from TEXT NOT NULL,
    ein_to TEXT NOT NULL,
    connection_type TEXT NOT NULL CHECK (connection_type IN
        ('peer_mentor', 'collab_partner', 'learning_peer', 'sector_neighbor')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'active', 'archived')),
    initiated_by TEXT NOT NULL,  -- which org initiated
    initiated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP,
    context_note TEXT,  -- "Working on similar homelessness issues in Portland"
    UNIQUE(ein_from, ein_to, connection_type),
    CHECK (ein_from != ein_to)
);

CREATE TABLE IF NOT EXISTS nonprofit_resource_shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_ein TEXT NOT NULL,
    to_ein TEXT NOT NULL,
    resource_type TEXT NOT NULL CHECK (resource_type IN
        ('volunteer_expertise', 'equipment', 'space', 'knowledge', 'funds', 'network_connection')),
    description TEXT NOT NULL,
    value_estimate_dollars INTEGER,
    status TEXT DEFAULT 'offered' CHECK (status IN ('offered', 'in_progress', 'completed', 'archived')),
    impact_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nonprofit_case_studies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    title TEXT NOT NULL,
    problem_statement TEXT NOT NULL,
    solution_description TEXT NOT NULL,
    results_achieved TEXT NOT NULL,
    lessons_learned TEXT NOT NULL,
    author_name TEXT,
    author_title TEXT,
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    peer_feedback_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nonprofit_case_study_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_study_id INTEGER NOT NULL,
    feedback_ein TEXT NOT NULL,
    feedback_text TEXT NOT NULL,
    is_helpful INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_study_id) REFERENCES nonprofit_case_studies(id)
);

CREATE TABLE IF NOT EXISTS nonprofit_peer_cohorts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cohort_name TEXT NOT NULL,
    cohort_type TEXT NOT NULL CHECK (cohort_type IN
        ('leadership_transition', 'growth_acceleration', 'crisis_response', 'cause_focused', 'regional')),
    cause_area TEXT,
    size_bracket TEXT CHECK (size_bracket IN ('micro', 'professional', 'established', 'mixed')),
    max_members INTEGER DEFAULT 8,
    season TEXT,  -- '2026-Q3', '2026-Q4'
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    facilitator_ein TEXT,
    facilitator_name TEXT,
    meeting_frequency TEXT,  -- 'monthly', 'biweekly', 'weekly'
    description TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('forming', 'active', 'completed', 'archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nonprofit_cohort_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cohort_id INTEGER NOT NULL,
    ein TEXT NOT NULL,
    contact_name TEXT NOT NULL,
    contact_email TEXT NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active' CHECK (status IN ('pending', 'active', 'left')),
    UNIQUE(cohort_id, ein),
    FOREIGN KEY (cohort_id) REFERENCES nonprofit_peer_cohorts(id)
);

-- Indices for common queries
CREATE INDEX IF NOT EXISTS idx_peer_connections_ein_from ON nonprofit_peer_connections(ein_from, status);
CREATE INDEX IF NOT EXISTS idx_peer_connections_ein_to ON nonprofit_peer_connections(ein_to, status);
CREATE INDEX IF NOT EXISTS idx_resource_shares_from ON nonprofit_resource_shares(from_ein, status);
CREATE INDEX IF NOT EXISTS idx_resource_shares_to ON nonprofit_resource_shares(to_ein, status);
CREATE INDEX IF NOT EXISTS idx_case_studies_ein ON nonprofit_case_studies(ein, published_at);
CREATE INDEX IF NOT EXISTS idx_cohort_members_cohort ON nonprofit_cohort_members(cohort_id, ein);
