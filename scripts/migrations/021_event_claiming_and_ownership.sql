-- Event Claiming & Nonprofit Ownership
-- Enables nonprofits to verify and manage AI-discovered events

BEGIN TRANSACTION;

-- Add columns to volunteer_events table (if table exists)
-- These columns track event claiming, verification, and discovery source
PRAGMA foreign_keys=OFF;

-- Attempt to add columns (use IF NOT EXISTS where available)
CREATE TABLE IF NOT EXISTS volunteer_events_new AS SELECT * FROM volunteer_events WHERE 1=0;

-- Add columns safely via PRAGMA table_info check
-- Since SQLite doesn't support IF NOT EXISTS for ALTER TABLE, we'll rely on
-- the app initialization to add these columns on startup (see droplet_api.py _init_volunteer_events_table)

PRAGMA foreign_keys=ON;

-- Create event_claims table for audit trail
CREATE TABLE IF NOT EXISTS event_claims (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    ein TEXT NOT NULL,
    email TEXT NOT NULL,
    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP,
    verification_token TEXT UNIQUE,
    verification_ip TEXT,
    status TEXT DEFAULT 'pending',  -- pending, verified, rejected
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES volunteer_events(id),
    FOREIGN KEY (ein) REFERENCES registry_enriched(ein)
);

-- Create event_nonprofit_dashboard_settings table
CREATE TABLE IF NOT EXISTS event_nonprofit_dashboard (
    ein TEXT PRIMARY KEY,
    event_count INTEGER DEFAULT 0,
    active_events INTEGER DEFAULT 0,
    total_volunteer_hours REAL DEFAULT 0,
    pending_hours_approvals INTEGER DEFAULT 0,
    last_login TIMESTAMP,
    dashboard_access_enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ein) REFERENCES registry_enriched(ein)
);

-- Create outreach_log table for tracking nonprofit emails
CREATE TABLE IF NOT EXISTS outreach_log (
    id TEXT PRIMARY KEY,
    ein TEXT NOT NULL,
    event_id TEXT,
    email TEXT NOT NULL,
    outreach_type TEXT DEFAULT 'discovery',  -- discovery, claim_reminder, hour_notification
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    bounced INTEGER DEFAULT 0,
    bounce_reason TEXT,
    converted_at TIMESTAMP,  -- When nonprofit claimed event after email
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ein) REFERENCES registry_enriched(ein),
    FOREIGN KEY (event_id) REFERENCES volunteer_events(id)
);

-- Index for claim lookups and verification
CREATE INDEX IF NOT EXISTS idx_volunteer_events_claim_status ON volunteer_events(claim_status);
CREATE INDEX IF NOT EXISTS idx_volunteer_events_claimed_by_ein ON volunteer_events(claimed_by_ein);
CREATE INDEX IF NOT EXISTS idx_volunteer_events_discovery_status ON volunteer_events(discovery_status);
CREATE INDEX IF NOT EXISTS idx_event_claims_ein ON event_claims(ein);
CREATE INDEX IF NOT EXISTS idx_event_claims_status ON event_claims(status);
CREATE INDEX IF NOT EXISTS idx_outreach_log_ein ON outreach_log(ein);
CREATE INDEX IF NOT EXISTS idx_outreach_log_sent_at ON outreach_log(sent_at);

COMMIT;
