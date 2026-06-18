-- Vendor partnership review system
-- Fully automated, zero-touch moderation

CREATE TABLE IF NOT EXISTS vendors (
    vendor_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,  -- 'compliance_tools' | 'giving_services' | 'financial' | etc
    description TEXT,
    contact_email TEXT NOT NULL,
    contact_phone TEXT,
    website TEXT,
    discount_code TEXT UNIQUE NOT NULL,
    discount_description TEXT,  -- "10% off annual plan"
    logo_url TEXT,
    active BOOLEAN DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vendor_ratings (
    rating_id TEXT PRIMARY KEY,
    vendor_id TEXT NOT NULL REFERENCES vendors(vendor_id),
    nonprofit_ein TEXT NOT NULL,  -- Who rated (from registry_enriched)
    stars INTEGER NOT NULL CHECK(stars >= 1 AND stars <= 5),
    savings_amount INTEGER DEFAULT 0 CHECK(savings_amount >= 0),  -- Dollars only, no negatives
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vendor_id, nonprofit_ein)  -- One rating per nonprofit per vendor
);

-- Aggregated stats, refreshed nightly
CREATE TABLE IF NOT EXISTS vendor_stats (
    vendor_id TEXT PRIMARY KEY REFERENCES vendors(vendor_id),
    avg_rating REAL,  -- 1.0 to 5.0
    rating_count INTEGER DEFAULT 0,
    total_savings INTEGER DEFAULT 0,  -- Sum of all savings
    nonprofits_contributed INTEGER DEFAULT 0,  -- Count of nonprofits who disclosed savings
    last_aggregated_at TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_vendor_ratings_vendor ON vendor_ratings(vendor_id);
CREATE INDEX IF NOT EXISTS idx_vendor_ratings_nonprofit ON vendor_ratings(nonprofit_ein);
CREATE INDEX IF NOT EXISTS idx_vendor_ratings_created ON vendor_ratings(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_vendors_active ON vendors(active) WHERE active=1;
