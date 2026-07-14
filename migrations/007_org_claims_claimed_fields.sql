-- Add claimed fields (donate_url, cause_tags_json) to org_claims for lock-free nonprofit overrides.
-- These complement the IRS record in registry_enriched without write locks on immutable data.

ALTER TABLE org_claims ADD COLUMN donate_url TEXT;
ALTER TABLE org_claims ADD COLUMN cause_tags_json TEXT;
