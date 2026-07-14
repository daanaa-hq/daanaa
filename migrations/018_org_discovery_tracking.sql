-- Org Discovery Tracking & Outreach System
-- Track when orgs get discovered, auto-reach out with proof

CREATE TABLE IF NOT EXISTS org_discovery_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL UNIQUE,
    unique_visitors_week INTEGER DEFAULT 0,
    unique_visitors_month INTEGER DEFAULT 0,
    first_discovery_date TIMESTAMP,
    last_discovery_date TIMESTAMP,
    discovery_sources TEXT,  -- JSON: {search: 50, browse: 20, direct: 10}
    visitor_countries TEXT,  -- JSON: {US: 95, CA: 3, UK: 2}
    avg_time_on_page REAL,
    bounce_rate REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS org_outreach_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    outreach_type TEXT CHECK (outreach_type IN ('discovery_proof', 'traffic_reminder', 'engagement_reminder')),
    contact_email TEXT NOT NULL,
    contact_method TEXT,  -- 'irs_email', 'website_contact', 'claimed_email'
    message_template TEXT,  -- which template was used
    unique_visitors_shown INTEGER,  -- proof point
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    response_received INTEGER DEFAULT 0,
    response_type TEXT,  -- 'claimed_profile', 'updated_info', 'email_reply', 'none'
    claimed_profile_at TIMESTAMP,
    updated_info_at TIMESTAMP,
    status TEXT DEFAULT 'sent' CHECK (status IN ('pending', 'sent', 'opened', 'responded', 'claimed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS discovery_outreach_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT NOT NULL UNIQUE,
    subject_line TEXT NOT NULL,
    body_template TEXT NOT NULL,  -- with {{placeholders}}
    call_to_action TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS org_contact_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    attempt_number INTEGER,
    email_address TEXT,
    contact_source TEXT,  -- 'irs', 'website', 'claimed'
    send_status TEXT,  -- 'success', 'bounced', 'failed', 'pending'
    last_attempt TIMESTAMP,
    next_retry TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS outreach_engagement_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start DATE,
    total_outreach INTEGER DEFAULT 0,
    successful_sends INTEGER DEFAULT 0,
    open_rate REAL DEFAULT 0.0,
    click_rate REAL DEFAULT 0.0,
    claim_rate REAL DEFAULT 0.0,
    profile_completion_rate REAL DEFAULT 0.0,
    avg_days_to_claim INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed default templates
INSERT OR IGNORE INTO discovery_outreach_templates
(template_name, subject_line, body_template, call_to_action)
VALUES
('first_discovery',
 'You''re getting discovered on Daanaa',
 'Hi {{org_name}},

We noticed {{unique_visitors}} people discovered your organization on Daanaa this week while searching for nonprofits to support.

Daanaa helps supporters find and trust organizations like yours. We''re completely free for nonprofits and supporters.

Your profile is already here with public information from the IRS. But you can make it even stronger by:
- Claiming your profile
- Adding your mission statement
- Sharing impact stories
- Connecting with peer organizations

Everything is optional. Supporters are already finding you. This just makes it easier.

Learn more at daanaa.org',
 'Claim your profile');

-- Indices
CREATE INDEX IF NOT EXISTS idx_discovery_metrics_ein ON org_discovery_metrics(ein);
CREATE INDEX IF NOT EXISTS idx_discovery_metrics_visitors ON org_discovery_metrics(unique_visitors_week DESC);
CREATE INDEX IF NOT EXISTS idx_outreach_log_ein ON org_outreach_log(ein, sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_outreach_log_status ON org_outreach_log(status, sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_contact_attempts_ein ON org_contact_attempts(ein, last_attempt DESC);
CREATE INDEX IF NOT EXISTS idx_engagement_metrics_week ON outreach_engagement_metrics(week_start DESC);
