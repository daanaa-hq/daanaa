-- Migration 022: Performance indexes for org-detail endpoint
-- Date: 2026-08-15
--
-- Fixes two full-table-scan bottlenecks discovered while diagnosing a
-- latency regression on GET /api/organizations/<ein> (3.3-9s, was ~50-100ms):
--
-- 1. _find_similar_orgs() tier-1 fallback (WHERE NTEECC = ? AND revenue_band = ?)
--    had NO supporting index at all, forcing a full sequential SCAN of the
--    2.06M-row registry_enriched table on every request that fell through to it.
--
-- 2. Category-rank computation (WHERE NTEE1 = ? AND total_revenue > ?) could
--    only use idx_ntee1 for the NTEE1 filter, then had to check total_revenue
--    row-by-row without index support — expensive for large NTEE1 categories
--    (X/religious=299K rows, B/education=221K, P/human-services=182K, etc.)
--
-- Combined with a separate fix to _find_similar_orgs' ORDER BY (see
-- droplet_api.py commit 3ea21d53371 — computed-expression sort bounded via
-- subquery LIMIT), these four indexes brought worst-case org-detail response
-- time from 3.3-9s down to 25-85ms (verified on EIN 391644738, NTEE1='X',
-- the single largest category).
--
-- Idempotent: safe to re-run.

CREATE INDEX IF NOT EXISTS idx_nteecc_band
    ON registry_enriched(NTEECC, revenue_band);

CREATE INDEX IF NOT EXISTS idx_ntee1_band
    ON registry_enriched(NTEE1, revenue_band);

CREATE INDEX IF NOT EXISTS idx_ntee1_revenue
    ON registry_enriched(NTEE1, total_revenue);

CREATE INDEX IF NOT EXISTS idx_state_ntee1_revenue
    ON registry_enriched(STATE, NTEE1, total_revenue);
