-- Migration 004: Add nonprofit data submission transparency columns to registry_enriched
-- Tracks when IRS data is overridden by nonprofit-submitted data

ALTER TABLE registry_enriched ADD COLUMN data_submitted_by_org INTEGER DEFAULT 0;
-- 0 = IRS data, 1 = nonprofit-submitted data

ALTER TABLE registry_enriched ADD COLUMN data_submitted_at TIMESTAMP;
-- When the nonprofit data was submitted

CREATE INDEX IF NOT EXISTS idx_registry_data_submitted_by_org ON registry_enriched(data_submitted_by_org);
