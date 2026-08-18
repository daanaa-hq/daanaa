-- Migration 026: Add inferred revenue band for non-filing orgs
--
-- Context: 1,341,640 orgs (65% of registry) currently show NULL total_revenue.
-- Of those, 1,337,364 (99.7%) have zero full-form 990/990-EZ filing on record --
-- consistent with e-Postcard (990-N) filing status, which IRS requires for
-- orgs with gross receipts normally under 50,000 dollars and does not collect
-- financial data on. This is an indirect inference from absence of a filing,
-- not a directly confirmed IRS figure -- board deliberation (2026-08-17,
-- see docs institution board process) recommended shipping it as a clearly
-- labeled estimate, never merged into total_revenue itself, per Stewardship
-- P3 (say so when evidence is uncertain) and Charter Promise 7 (thin data
-- gets "we don't know enough," not a confident-sounding false precision).
--
-- These columns are additive and nullable -- existing total_revenue is
-- untouched. revenue_band_estimate is populated ONLY where total_revenue is
-- NULL/0; it is a display hint, not a scoring input (v6 scoring already
-- assigns tiers to 99.0% of these orgs without needing revenue -- confirmed
-- before this migration, not a scoring dependency).

ALTER TABLE registry_enriched ADD COLUMN revenue_band_estimate TEXT;
ALTER TABLE registry_enriched ADD COLUMN revenue_band_estimate_reason TEXT;

CREATE INDEX IF NOT EXISTS idx_registry_revenue_band_estimate ON registry_enriched(revenue_band_estimate);
