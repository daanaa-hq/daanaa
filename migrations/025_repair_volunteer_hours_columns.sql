-- Migration 025: Repair volunteer_hours missing columns from migration 020
--
-- Context: Migration 020 (2026-07-22, logged as run) attempted to add 4 new
-- columns to volunteer_hours (submitted_via, edit_count, locked_at, task_type)
-- but due to a migration-runner bug (comments in SQL broke the statement splitter),
-- only event_id landed. The other 3 never applied. This additive migration adds
-- them now. nonprofit_ein is NOT added here -- the broken endpoints will be fixed
-- to join volunteer_hours.event_id -> volunteer_events.id -> volunteer_events.ein
-- instead of querying a nonexistent nonprofit_ein column (that column does not
-- appear on any other row of the live volunteer_hours table, confirming the
-- nonprofit-portal schema was never the live schema).
--
-- IDEMPOTENCY NOTE (SQLite limitation):
-- SQLite does not support ALTER TABLE ... IF NOT EXISTS. If this migration is
-- re-run, it will fail on "column already exists" error. This is acceptable for
-- a one-time migration; in production, verify schema via PRAGMA table_info
-- before re-running, or use scripts/verify_migrations.py.

-- Add the 3 columns that migration 020 intended but never applied
ALTER TABLE volunteer_hours ADD COLUMN submitted_via TEXT DEFAULT 'nonprofit_entry';
ALTER TABLE volunteer_hours ADD COLUMN edit_count INTEGER DEFAULT 0;
ALTER TABLE volunteer_hours ADD COLUMN locked_at TEXT;
ALTER TABLE volunteer_hours ADD COLUMN task_type TEXT;

-- Create/recreate indexes added in migration 020 but that should've existed
-- (these were in 020 but never ran)
CREATE INDEX IF NOT EXISTS idx_volunteer_hours_task_type ON volunteer_hours(task_type);
