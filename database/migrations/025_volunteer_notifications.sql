-- Migration 025: Volunteer Hours Notifications
-- Date: 2026-07-22
-- Purpose: Add notification tracking to prevent duplicates and ensure reliability
-- Safety: Email failures don't roll back database changes

BEGIN TRANSACTION;

-- ============================================================================
-- 1. NOTIFICATION_JOBS — Track all notification attempts
-- ============================================================================
CREATE TABLE IF NOT EXISTS volunteer_notification_jobs (
    job_id TEXT PRIMARY KEY,

    -- What triggered this notification
    hour_id TEXT NOT NULL,
    notification_type TEXT NOT NULL CHECK(notification_type IN ('submitted', 'approved', 'rejected')),

    -- Recipient info (stored to avoid PII lookups after deletion)
    recipient_email TEXT NOT NULL,
    recipient_type TEXT NOT NULL CHECK(recipient_type IN ('volunteer', 'nonprofit')),

    -- Content (never logged, only stored for idempotency)
    subject TEXT NOT NULL,

    -- Status tracking
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'sent', 'failed', 'skipped')),
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,

    -- Timing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    next_retry_at TIMESTAMP,

    -- Context (for troubleshooting, no PII)
    error_message TEXT,
    is_test_run BOOLEAN DEFAULT 0,

    -- Tracking to prevent duplicates
    -- For submitted: one per (hour_id, 'submitted')
    -- For approved/rejected: one per (hour_id, notification_type)
    UNIQUE(hour_id, notification_type),
    FOREIGN KEY (hour_id) REFERENCES volunteer_hours(id)
);

CREATE INDEX IF NOT EXISTS idx_notification_status ON volunteer_notification_jobs(status);
CREATE INDEX IF NOT EXISTS idx_notification_retry ON volunteer_notification_jobs(next_retry_at);
CREATE INDEX IF NOT EXISTS idx_notification_hour ON volunteer_notification_jobs(hour_id);

COMMIT;
