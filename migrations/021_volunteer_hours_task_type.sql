-- Migration 021: task_type column for volunteer_hours (short category, e.g.
-- "marshal", "registration", "cleanup"). activity_description stays free text.
ALTER TABLE volunteer_hours ADD COLUMN task_type TEXT;
CREATE INDEX IF NOT EXISTS idx_volunteer_hours_task_type ON volunteer_hours(nonprofit_ein, task_type);
