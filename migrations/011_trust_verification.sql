-- Phase 5: Trust Verification
-- Badges, verification tracking, audit trail for credibility signals

CREATE TABLE IF NOT EXISTS nonprofit_verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    verification_type TEXT NOT NULL CHECK (verification_type IN
        ('website_active', 'donate_link_verified', 'mission_claimed', 'leadership_verified', 'financial_filed')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'verified', 'expired', 'failed')),
    verification_method TEXT,  -- 'automated', 'manual', 'self_attested', 'third_party'
    verified_at TIMESTAMP,
    verified_by TEXT,  -- who verified (system, org, admin, partner)
    expires_at TIMESTAMP,
    confidence_score REAL DEFAULT 0.0,  -- 0-1
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ein, verification_type)
);

CREATE TABLE IF NOT EXISTS nonprofit_badges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    badge_type TEXT NOT NULL CHECK (badge_type IN
        ('verified_org', 'active_mission', 'financial_health', 'responsive', 'transparent', 'peer_trusted')),
    badge_name TEXT NOT NULL,  -- "Verified Organization", "Active Mission", etc.
    badge_description TEXT,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    earned_by TEXT,  -- earned through verification_type (e.g., 'website_active')
    display_order INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ein, badge_type)
);

CREATE TABLE IF NOT EXISTS verification_timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    event TEXT NOT NULL,  -- 'verification_started', 'verification_completed', 'badge_earned', 'expired', 'renewed'
    event_type TEXT,  -- 'website_active', 'donate_link', etc.
    status TEXT,
    result TEXT,  -- 'success', 'failed', 'pending'
    details TEXT,  -- JSON: {method, confidence, notes}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS verification_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    action TEXT NOT NULL,  -- 'verification_started', 'manual_review', 'badge_awarded', 'verification_revoked'
    actor TEXT,  -- 'system', 'admin', 'nonprofit', 'partner'
    reason TEXT,
    evidence_url TEXT,
    result TEXT,  -- 'success', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS verification_expiry_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    verification_type TEXT,
    expires_at TIMESTAMP,
    renewal_window_days INTEGER DEFAULT 30,
    notification_sent INTEGER DEFAULT 0,
    notified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices for common queries
CREATE INDEX IF NOT EXISTS idx_verifications_ein ON nonprofit_verifications(ein, status);
CREATE INDEX IF NOT EXISTS idx_verifications_type ON nonprofit_verifications(verification_type, status);
CREATE INDEX IF NOT EXISTS idx_badges_ein ON nonprofit_badges(ein, is_active);
CREATE INDEX IF NOT EXISTS idx_timeline_ein ON verification_timeline(ein, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_ein ON verification_audit_log(ein, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_expiry_schedule_expires ON verification_expiry_schedule(expires_at ASC);
