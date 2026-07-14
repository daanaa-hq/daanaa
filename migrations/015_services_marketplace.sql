-- Phase 8: Nonprofit Services Marketplace
-- Connect nonprofits with consultants, vendors, training (separate from Daanaa, no influence on visibility)

CREATE TABLE IF NOT EXISTS nonprofit_service_providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_ein TEXT,  -- If consultant org is registered
    provider_name TEXT NOT NULL,
    service_category TEXT CHECK (service_category IN ('consulting', 'training', 'technology', 'grants', 'compliance', 'fundraising')),
    specialization TEXT,  -- "ED Coaching", "Grant Writing", "Database Migration"
    experience_level TEXT CHECK (experience_level IN ('emerging', 'established', 'expert')),
    client_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,  -- % of clients achieved goals
    hourly_rate_low INTEGER,
    hourly_rate_high INTEGER,
    availability TEXT,  -- 'available', 'waitlist', 'booked'
    bio TEXT,
    testimonials_count INTEGER DEFAULT 0,
    rating REAL DEFAULT 0.0,  -- 0-5 stars
    marketplace_status TEXT DEFAULT 'active' CHECK (marketplace_status IN ('active', 'pending_review', 'inactive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS service_engagements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    provider_ein TEXT,
    service_type TEXT,
    engagement_start TIMESTAMP,
    engagement_end TIMESTAMP,
    scope_of_work TEXT,
    engagement_cost INTEGER,
    outcome_achieved TEXT,
    impact_summary TEXT,
    satisfaction_rating REAL,
    would_recommend INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vendor_impact_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_ein TEXT,
    nonprofit_ein TEXT,
    service_type TEXT,
    cost REAL,
    reported_impact TEXT,  -- "Raised $100K in new grants"
    impact_verified INTEGER DEFAULT 0,
    verified_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_providers_category ON nonprofit_service_providers(service_category, availability);
CREATE INDEX IF NOT EXISTS idx_providers_rating ON nonprofit_service_providers(rating DESC);
CREATE INDEX IF NOT EXISTS idx_engagements_ein ON service_engagements(ein, engagement_start DESC);
