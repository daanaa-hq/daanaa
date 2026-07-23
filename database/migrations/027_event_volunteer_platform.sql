-- Migration 027: Event Volunteer Tracking Platform
-- Date: 2026-07-22
-- Purpose: Core tables for AKF event platform (volunteer registration, hour logging, dashboards)
-- Safety: New tables only, no schema changes to existing tables

BEGIN TRANSACTION;

-- ============================================================================
-- EVENTS — Core event information (e.g., AKF Golf Tournament)
-- ============================================================================
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    event_date DATE NOT NULL,
    location TEXT,
    organizer_id TEXT NOT NULL,  -- Firebase UID of org creating event
    organizer_name TEXT,  -- Cached org name
    status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'active', 'completed')),

    -- Donation integration
    donation_url TEXT,  -- Link to donate page (e.g., Funraisin URL)
    donation_enabled BOOLEAN DEFAULT false,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_organizer CHECK(organizer_id != '')
);

CREATE INDEX IF NOT EXISTS idx_events_organizer ON events(organizer_id);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);

-- ============================================================================
-- EVENT_VOLUNTEERS — Volunteer registrations for each event
-- ============================================================================
CREATE TABLE IF NOT EXISTS event_volunteers (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    volunteer_id TEXT NOT NULL,  -- Firebase UID or email
    volunteer_name TEXT NOT NULL,
    volunteer_email TEXT NOT NULL,

    -- Role/position at event
    role TEXT,  -- e.g., "setup", "scoring", "cleanup", "volunteer"

    -- Status in event
    status TEXT DEFAULT 'registered' CHECK(status IN ('registered', 'checked_in', 'completed', 'no_show')),

    -- Registration details
    phone TEXT,
    team_id TEXT,  -- Foreign key to event_teams

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checked_in_at TIMESTAMP,

    FOREIGN KEY (event_id) REFERENCES events(id),
    UNIQUE(event_id, volunteer_id)
);

CREATE INDEX IF NOT EXISTS idx_event_volunteers_event ON event_volunteers(event_id);
CREATE INDEX IF NOT EXISTS idx_event_volunteers_volunteer ON event_volunteers(volunteer_id);
CREATE INDEX IF NOT EXISTS idx_event_volunteers_team ON event_volunteers(team_id);
CREATE INDEX IF NOT EXISTS idx_event_volunteers_status ON event_volunteers(status);

-- ============================================================================
-- VOLUNTEER_HOURS — Hour submissions per volunteer per event
-- ============================================================================
CREATE TABLE IF NOT EXISTS volunteer_hours (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    volunteer_id TEXT NOT NULL,

    -- Hours details
    hours REAL NOT NULL CHECK(hours > 0),
    job_description TEXT,  -- e.g., "Setup", "Registration", "Scoring"
    service_date DATE NOT NULL,

    -- Status and approval
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
    approved_by TEXT,  -- Organizer who approved
    approved_at TIMESTAMP,

    -- Notes
    notes TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (event_id) REFERENCES events(id),
    FOREIGN KEY (volunteer_id) REFERENCES event_volunteers(volunteer_id)
);

CREATE INDEX IF NOT EXISTS idx_volunteer_hours_event ON volunteer_hours(event_id);
CREATE INDEX IF NOT EXISTS idx_volunteer_hours_volunteer ON volunteer_hours(volunteer_id);
CREATE INDEX IF NOT EXISTS idx_volunteer_hours_status ON volunteer_hours(status);
CREATE INDEX IF NOT EXISTS idx_volunteer_hours_date ON volunteer_hours(service_date);

-- ============================================================================
-- EVENT_TEAMS — Organize volunteers into teams (e.g., golf foursomes)
-- ============================================================================
CREATE TABLE IF NOT EXISTS event_teams (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    team_name TEXT NOT NULL,
    team_lead_id TEXT,  -- Volunteer who leads the team
    team_lead_name TEXT,

    -- Team stats (cached, updated on hour submission)
    total_hours REAL DEFAULT 0,
    volunteer_count INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (event_id) REFERENCES events(id),
    UNIQUE(event_id, team_name)
);

CREATE INDEX IF NOT EXISTS idx_event_teams_event ON event_teams(event_id);

-- ============================================================================
-- EVENT_STATS — Cached stats for dashboard (updated on hour submission)
-- ============================================================================
CREATE TABLE IF NOT EXISTS event_stats (
    event_id TEXT PRIMARY KEY,

    -- Counts
    volunteer_count INTEGER DEFAULT 0,
    checked_in_count INTEGER DEFAULT 0,
    total_hours_approved REAL DEFAULT 0,
    total_hours_pending REAL DEFAULT 0,

    -- Derived stats
    avg_hours_per_volunteer REAL DEFAULT 0,
    retention_rate REAL DEFAULT 0,  -- Percentage who completed hours

    -- Last updated
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (event_id) REFERENCES events(id)
);

CREATE INDEX IF NOT EXISTS idx_event_stats_updated ON event_stats(updated_at);

-- ============================================================================
-- EVENT_AUDIT_LOG — Track all actions on events (for compliance)
-- ============================================================================
CREATE TABLE IF NOT EXISTS event_audit_log (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    action TEXT NOT NULL,  -- e.g., "volunteer_registered", "hours_submitted", "hours_approved"
    actor_id TEXT,  -- Who performed the action
    actor_type TEXT,  -- "organizer" or "volunteer"
    details TEXT,  -- JSON details of what changed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (event_id) REFERENCES events(id)
);

CREATE INDEX IF NOT EXISTS idx_audit_log_event ON event_audit_log(event_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON event_audit_log(action);

COMMIT;
