-- 027_deductible_active_index.sql
--
-- Fixes a full-table-scan on every request that uses _DEDUCTIBILITY_FILTER /
-- DEDUCTIBLE_FILTER (registry_filters.py) -- the canonical "active,
-- tax-deductible 501(c)(3)" predicate used by the directory, search, homepage
-- stats, and every count/aggregate that reaches a user. None of the existing
-- indexes on registry_enriched cover subsection/deductibility, so every one
-- of those requests did SCAN r (full 2.06M-row scan) instead of a seek.
--
-- Found 2026-08-19 investigating a live user report ("orgs aren't loading"
-- on /directory) -- EXPLAIN QUERY PLAN confirmed SCAN r, ~2.8s per COUNT(*)
-- alone before the actual data query even ran. Pre-existing, not caused by
-- any same-day change; just newly bad enough to be visibly broken.
--
-- Tested on a local throwaway copy before touching anything live:
--   SCAN r                              -> SEARCH r USING INDEX ... (seek)
--   2.797s                              -> 0.455s
--
-- COALESCE(irs_revoked, 0) != 1 and COALESCE(org_status, '') != 'revoked'
-- aren't sargable (COALESCE defeats a plain index), so org_status is
-- included in the index to at least narrow the post-seek residual scan --
-- irs_revoked isn't, since it's rarely the selective column here and a
-- 4-column index has diminishing returns past this point.

CREATE INDEX IF NOT EXISTS idx_deductible_active
    ON registry_enriched(subsection, deductibility, org_status);
