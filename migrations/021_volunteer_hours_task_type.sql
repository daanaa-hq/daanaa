-- Migration 021: task_type column for volunteer_hours (short category, e.g.
-- "marshal", "registration", "cleanup"). activity_description stays free text.
--
-- IDEMPOTENCY NOTE (SQLite limitation):
-- SQLite does not support ALTER TABLE ... IF NOT EXISTS. If this migration is
-- re-run, it will fail on "column already exists" error. Verify schema via
-- PRAGMA table_info(volunteer_hours) before re-running.
ALTER TABLE volunteer_hours ADD COLUMN task_type TEXT;
CREATE INDEX IF NOT EXISTS idx_volunteer_hours_task_type ON volunteer_hours(nonprofit_ein, task_type);
