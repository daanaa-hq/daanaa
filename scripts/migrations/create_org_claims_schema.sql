-- Nonprofit claim verification schema
-- Run this migration to set up the org_claims table and update registry_enriched

-- 1. Create org_claims table
CREATE TABLE IF NOT EXISTS org_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    token TEXT UNIQUE NOT NULL,
    pin TEXT NOT NULL,
    claim_status TEXT DEFAULT 'email_sent',  -- 'email_sent', 'verified'
    claimed_at TIMESTAMP,
    claimed_by TEXT,
    lob_letter_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Add columns to registry_enriched for claim tracking
ALTER TABLE registry_enriched ADD COLUMN claim_status TEXT DEFAULT 'unclaimed';
ALTER TABLE registry_enriched ADD COLUMN claimed_by TEXT;
ALTER TABLE registry_enriched ADD COLUMN claimed_at TIMESTAMP;

-- 3. Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_org_claims_ein ON org_claims(ein);
CREATE INDEX IF NOT EXISTS idx_org_claims_token ON org_claims(token);
CREATE INDEX IF NOT EXISTS idx_org_claims_email ON org_claims(email);
CREATE INDEX IF NOT EXISTS idx_registry_enriched_claim_status ON registry_enriched(claim_status);

-- 4. Verify schema (run this to check)
-- SELECT name FROM sqlite_master WHERE type='table' AND name='org_claims';
-- PRAGMA table_info(org_claims);
