-- Migration 020: Volunteer hours — event-linked self-submission, audit trail,
-- yearly impact cache, and impact_logs schema repair.
--
-- Context: volunteer_hours already exists (nonprofit-entry + claim-code flow).
-- This adds a self-service path (volunteer submits directly via event QR/link),
-- an immutable audit trail, 30-day edit lock support, and a nonprofit-facing
-- yearly impact cache. It also fixes a pre-existing schema drift in impact_logs
-- that silently broke the Wallet -> community-stats pipeline (the API/aggregator
-- code writes ein/type/hours/log_date, but the live table only had
-- org_ein/impact_type/amount/source/verified/notes).
--
-- IDEMPOTENCY NOTE (SQLite limitation):
-- SQLite does not support ALTER TABLE ... IF NOT EXISTS. If this migration is
-- re-run against an existing database, it will fail on column-already-exists
-- errors. This is acceptable for a one-time migration; in production, verify
-- schema via PRAGMA table_info(impact_logs) and PRAGMA table_info(volunteer_hours)
-- before running again, or use the Python verification script in scripts/verify_migrations.py

-- ── Fix impact_logs schema drift (additive, non-destructive) ────────────────
ALTER TABLE impact_logs ADD COLUMN ein TEXT;
ALTER TABLE impact_logs ADD COLUMN type TEXT;
ALTER TABLE impact_logs ADD COLUMN hours REAL;
ALTER TABLE impact_logs ADD COLUMN log_date TEXT;

CREATE INDEX IF NOT EXISTS idx_impact_logs_ein_date ON impact_logs(ein, log_date);
CREATE INDEX IF NOT EXISTS idx_impact_logs_type_date ON impact_logs(type, log_date);

-- ── volunteer_hours: event linkage + self-submission + edit lock ───────────
ALTER TABLE volunteer_hours ADD COLUMN event_id INTEGER;
ALTER TABLE volunteer_hours ADD COLUMN submitted_via TEXT DEFAULT 'nonprofit_entry';
ALTER TABLE volunteer_hours ADD COLUMN edit_count INTEGER DEFAULT 0;
ALTER TABLE volunteer_hours ADD COLUMN locked_at TEXT;

CREATE INDEX IF NOT EXISTS idx_volunteer_hours_event ON volunteer_hours(event_id);
CREATE INDEX IF NOT EXISTS idx_volunteer_hours_ein_status ON volunteer_hours(nonprofit_ein, status);
CREATE INDEX IF NOT EXISTS idx_volunteer_hours_service_date ON volunteer_hours(nonprofit_ein, service_date);

-- ── Immutable audit log for all volunteer_hours state changes ──────────────
CREATE TABLE IF NOT EXISTS volunteer_hours_audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    hour_id         TEXT NOT NULL,
    action          TEXT NOT NULL,   -- submitted, edited, approved, rejected, locked, deleted
    changed_by      TEXT,            -- firebase uid, 'volunteer', or 'system' (maintenance job)
    changed_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    change_details  TEXT,            -- JSON: {"field": "hours", "old": 4, "new": 6}
    FOREIGN KEY (hour_id) REFERENCES volunteer_hours(id)
);
CREATE INDEX IF NOT EXISTS idx_vh_audit_hour ON volunteer_hours_audit_log(hour_id, changed_at);

-- ── Nonprofit yearly impact cache (fast dashboard reads) ────────────────────
CREATE TABLE IF NOT EXISTS nonprofit_yearly_impact_cache (
    nonprofit_ein         TEXT NOT NULL,
    year                  INTEGER NOT NULL,
    total_hours_approved  REAL DEFAULT 0,
    volunteer_count       INTEGER DEFAULT 0,
    event_count           INTEGER DEFAULT 0,
    hours_by_task_type    TEXT,   -- JSON
    hours_by_month        TEXT,   -- JSON
    is_public             INTEGER DEFAULT 0,
    last_updated          TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (nonprofit_ein, year)
);

-- ── Nonprofit data-use acknowledgement (Tier 2 disclosure, Stewardship P2/P9) ─
CREATE TABLE IF NOT EXISTS nonprofit_data_agreements (
    nonprofit_ein   TEXT PRIMARY KEY,
    agreed_by       TEXT,
    agreed_at       TEXT DEFAULT CURRENT_TIMESTAMP,
    agreement_version TEXT DEFAULT 'v1'
);
