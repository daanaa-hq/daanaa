-- Migration 003: Add composite indexes for search performance optimization
-- Task #5: Schema changes (approved 2026-08-12)
-- Purpose: Optimize queries for location-filtered and score-sorted searches
-- Risk: LOW (non-breaking indexes; can be dropped if needed)
-- Expected impact: 5-10% faster filtered/sorted queries

-- Index 1: Location-filtered searches (state + organization_name)
-- Use case: "Show nonprofits in Texas" or "Search for food banks in California"
-- Query pattern: WHERE STATE = ? AND (org_fts MATCH ? OR organization_name LIKE ?)
CREATE INDEX IF NOT EXISTS idx_state_organization_name
ON registry_enriched(STATE, organization_name);

-- Index 2: Score-based sorting (merit_score DESC + organization_name)
-- Use case: "Sort by financial health score" or "Top 10 most healthy orgs"
-- Query pattern: ORDER BY merit_score DESC, organization_name ASC
CREATE INDEX IF NOT EXISTS idx_merit_score_organization_name
ON registry_enriched(merit_score DESC, organization_name ASC);

-- Index 3: NTEE peer group searches
-- Use case: "Show all nonprofits in the education sector"
-- Query pattern: WHERE NTEE1 = ? OR NTEECC LIKE ?
CREATE INDEX IF NOT EXISTS idx_ntee1
ON registry_enriched(NTEE1);

-- Verify indexes were created
-- SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='registry_enriched';
