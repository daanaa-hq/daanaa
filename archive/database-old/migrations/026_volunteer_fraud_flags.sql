-- Migration 026: Volunteer Fraud Detection
-- Date: 2026-07-22
-- Purpose: Add fraud flagging system for suspicious volunteer submissions
-- Safety: Flags for review only, no auto-rejection

BEGIN TRANSACTION;

-- ============================================================================
-- VOLUNTEER_FRAUD_FLAGS — Track flagged submissions for admin review
-- ============================================================================
CREATE TABLE IF NOT EXISTS volunteer_fraud_flags (
    flag_id TEXT PRIMARY KEY,

    -- What submission triggered the flag
    hour_id TEXT NOT NULL,
    nonprofit_ein TEXT NOT NULL,

    -- Risk assessment (data-driven, no human judgment)
    risk_score REAL NOT NULL CHECK(risk_score >= 0 AND risk_score <= 100),
    reason TEXT NOT NULL,  -- Human-readable explanation (no PII)
    severity TEXT NOT NULL CHECK(severity IN ('low', 'medium', 'high', 'critical')),

    -- Admin review
    status TEXT DEFAULT 'pending_review' CHECK(status IN ('pending_review', 'reviewed', 'dismissed', 'resolved')),
    reviewed_by TEXT,  -- Admin UID who reviewed
    admin_notes TEXT,
    reviewed_at TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(hour_id),  -- One flag per submission
    FOREIGN KEY (hour_id) REFERENCES volunteer_hours(id)
);

CREATE INDEX IF NOT EXISTS idx_fraud_status ON volunteer_fraud_flags(status);
CREATE INDEX IF NOT EXISTS idx_fraud_nonprofit ON volunteer_fraud_flags(nonprofit_ein);
CREATE INDEX IF NOT EXISTS idx_fraud_risk ON volunteer_fraud_flags(risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_fraud_severity ON volunteer_fraud_flags(severity);

COMMIT;
