-- Phase 7: Institutional Memory
-- Preserve organizational knowledge, timelines, decision logs, and transitions

CREATE TABLE IF NOT EXISTS org_timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    event_date TIMESTAMP,
    event_type TEXT CHECK (event_type IN ('founding', 'leadership_change', 'expansion', 'crisis', 'partnership', 'grant', 'award', 'milestone')),
    event_title TEXT NOT NULL,
    event_description TEXT,
    impact TEXT,  -- How did it affect the org?
    sources TEXT,  -- JSON array of evidence sources (IRS, news, org claim)
    verified_by TEXT,  -- who confirmed this
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS org_leadership_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    leader_name TEXT NOT NULL,
    position TEXT,  -- ED, Executive Director, Co-Founder, etc.
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    tenure_years REAL,
    background TEXT,  -- Where did they come from?
    transition_notes TEXT,  -- How smooth was transition?
    accomplishments TEXT,  -- What did they achieve?
    successor_name TEXT,  -- Who replaced them?
    visibility_score REAL DEFAULT 0.5,  -- 0-1, how well documented?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS org_knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    knowledge_type TEXT CHECK (knowledge_type IN ('process', 'contact', 'history', 'financial', 'program', 'partnership')),
    topic TEXT,  -- "Grant writing process", "Key funder contacts", "Emergency procedures"
    content TEXT,  -- Markdown formatted
    owner_name TEXT,  -- Who knows this?
    owner_contact TEXT,
    last_updated TIMESTAMP,
    criticality TEXT CHECK (criticality IN ('high', 'medium', 'low')),  -- How essential is it?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS org_decision_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    decision_date TIMESTAMP,
    decision_title TEXT NOT NULL,
    decision_context TEXT,  -- Why was this needed?
    decision_details TEXT,  -- What was decided?
    decision_maker TEXT,  -- Who decided?
    rationale TEXT,  -- Why this choice?
    outcomes TEXT,  -- How did it work out?
    lessons TEXT,  -- What did we learn?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS board_evolution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    snapshot_date TIMESTAMP,
    board_size INTEGER,
    board_composition TEXT,  -- JSON: demographics, skills, tenure
    board_diversity_score REAL,  -- 0-1
    key_committees TEXT,  -- JSON array
    meeting_frequency TEXT,  -- monthly, quarterly
    governance_improvements TEXT,  -- What changed?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS organizational_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    change_date TIMESTAMP,
    change_type TEXT CHECK (change_type IN ('mission_adjustment', 'program_launch', 'program_closure', 'merger', 'restructure', 'location_change')),
    change_description TEXT,
    change_reason TEXT,
    impact_on_staff INTEGER,  -- Jobs added/lost
    impact_on_programs TEXT,
    lessons_learned TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_timeline_ein ON org_timeline(ein, event_date DESC);
CREATE INDEX IF NOT EXISTS idx_leadership_ein ON org_leadership_history(ein, start_date DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_ein ON org_knowledge_base(ein, knowledge_type);
CREATE INDEX IF NOT EXISTS idx_decisions_ein ON org_decision_log(ein, decision_date DESC);
CREATE INDEX IF NOT EXISTS idx_board_evolution_ein ON board_evolution(ein, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_org_changes_ein ON organizational_changes(ein, change_date DESC);
