-- Migration: Create Needs Network Schema (Phase 3B Foundation)
-- Date: 2026-08-09
-- Purpose: Enable nonprofits to submit funding/volunteer Needs
-- Tables: needs, need_intakes, need_approvals, need_freshness_log

-- ====================================================================
-- Table: needs
-- Purpose: Live Needs published by nonprofits
-- Stewardship P4 (fairness): Small orgs get equal visibility for Needs
-- ====================================================================
CREATE TABLE IF NOT EXISTS needs (
    need_id TEXT PRIMARY KEY,  -- UUID: ein-needtype-timestamp
    ein TEXT NOT NULL,
    need_type TEXT NOT NULL CHECK(need_type IN ('FUNDING', 'VOLUNTEER')),

    -- Descriptive
    title TEXT NOT NULL,
    description TEXT,
    amount_needed INTEGER,  -- For FUNDING: requested amount (USD)
    deadline_date TEXT,     -- ISO 8601 date (e.g., "2026-12-31")

    -- Context
    cause_area TEXT,        -- NTEE category (e.g., "Food", "Health")
    service_states TEXT,    -- JSON array: ["NY", "NJ"] or ["NATIONAL"]
    primary_state TEXT,     -- State where primary need is (for geo targeting)

    -- Status
    status TEXT NOT NULL DEFAULT 'DRAFT' CHECK(status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'PUBLISHED', 'ARCHIVED', 'EXPIRED')),
    published_date TEXT,
    archived_date TEXT,

    -- Freshness (Stewardship P6: catch stale data)
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_confirmed_date TEXT,  -- When nonprofit last confirmed this Need is still valid
    freshness_status TEXT DEFAULT 'UNCONFIRMED' CHECK(freshness_status IN ('UNCONFIRMED', 'CONFIRMED', 'PENDING_CONFIRMATION', 'UNRESPONSIVE')),

    -- Tracking
    click_count INTEGER DEFAULT 0,
    volunteer_interest_count INTEGER DEFAULT 0,

    -- Metadata
    data_source TEXT DEFAULT 'nonprofit_intake' CHECK(data_source IN ('nonprofit_intake', 'ai_generated')),
    confidence TEXT DEFAULT 'high' CHECK(confidence IN ('high', 'moderate', 'low')),

    FOREIGN KEY(ein) REFERENCES registry_enriched(EIN),
    INDEX idx_needs_ein (ein),
    INDEX idx_needs_status (status),
    INDEX idx_needs_type (need_type),
    INDEX idx_needs_freshness (freshness_status),
    INDEX idx_needs_published (published_date)
);

-- ====================================================================
-- Table: need_intakes
-- Purpose: Track nonprofit submissions + AI draft generation
-- Stewardship P10: AI is a tool; nonprofit must approve before publishing
-- ====================================================================
CREATE TABLE IF NOT EXISTS need_intakes (
    intake_id TEXT PRIMARY KEY,  -- UUID
    ein TEXT NOT NULL,
    need_type TEXT NOT NULL,

    -- Input modality (Stewardship P4: low friction for small orgs)
    input_mode TEXT NOT NULL CHECK(input_mode IN ('VOICE', 'TEXT', 'DOCUMENT', 'API')),
    voice_transcript TEXT,  -- If voice: raw transcription
    text_input TEXT,        -- If text: form submission
    document_url TEXT,      -- If document: S3 URL to uploaded file

    -- AI Generation (Stewardship P10: transparent about AI involvement)
    ai_draft_title TEXT,
    ai_draft_description TEXT,
    ai_confidence REAL DEFAULT 0.0,  -- 0.0-1.0 confidence in draft
    ai_model_version TEXT,           -- e.g., "qwen3-30b-q4"

    -- Nonprofit Action
    nonprofit_approved BOOLEAN DEFAULT FALSE,
    nonprofit_approval_date TEXT,
    nonprofit_edits TEXT,  -- JSON object of what nonprofit changed

    -- Status
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'APPROVED', 'REJECTED', 'PUBLISHED_TO_NEED')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TEXT,

    FOREIGN KEY(ein) REFERENCES registry_enriched(EIN),
    INDEX idx_intakes_ein (ein),
    INDEX idx_intakes_status (status),
    INDEX idx_intakes_created (created_at)
);

-- ====================================================================
-- Table: need_approvals
-- Purpose: Audit trail for Need approval workflow
-- Stewardship P6: Track corrections/changes for accountability
-- ====================================================================
CREATE TABLE IF NOT EXISTS need_approvals (
    approval_id TEXT PRIMARY KEY,  -- UUID
    need_id TEXT NOT NULL,
    ein TEXT NOT NULL,

    -- Who & When
    reviewed_by TEXT,  -- Nonprofit contact email or "SYSTEM"
    reviewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Decision
    action TEXT NOT NULL CHECK(action IN ('APPROVED', 'REJECTED', 'REQUESTED_CHANGES')),
    reason TEXT,
    feedback TEXT,

    -- Tracking
    version_number INTEGER,  -- Which version of the Need (for edit history)

    FOREIGN KEY(need_id) REFERENCES needs(need_id),
    FOREIGN KEY(ein) REFERENCES registry_enriched(EIN),
    INDEX idx_approvals_need (need_id),
    INDEX idx_approvals_ein (ein),
    INDEX idx_approvals_reviewed (reviewed_at)
);

-- ====================================================================
-- Table: need_freshness_log
-- Purpose: Track re-confirmation requests to keep Needs current
-- Stewardship P6: Automate catching stale data
-- ====================================================================
CREATE TABLE IF NOT EXISTS need_freshness_log (
    freshness_check_id TEXT PRIMARY KEY,  -- UUID
    need_id TEXT NOT NULL,
    ein TEXT NOT NULL,

    -- Request
    sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_at TEXT,  -- When response is due (sent_at + 7 days)

    -- Response
    nonprofit_confirmed BOOLEAN DEFAULT FALSE,
    response_received_at TEXT,
    nonprofit_action TEXT CHECK(nonprofit_action IN ('CONFIRMED', 'ARCHIVED', 'UPDATED', 'NO_RESPONSE')),

    -- Auto-archival (if no response after 60 days)
    auto_archived BOOLEAN DEFAULT FALSE,
    auto_archived_at TEXT,

    FOREIGN KEY(need_id) REFERENCES needs(need_id),
    FOREIGN KEY(ein) REFERENCES registry_enriched(EIN),
    INDEX idx_freshness_need (need_id),
    INDEX idx_freshness_ein (ein),
    INDEX idx_freshness_due (due_at)
);

-- ====================================================================
-- Table: need_donor_interest
-- Purpose: Track donor/volunteer interest in Needs (for metrics + matching)
-- Stewardship P2: Privacy — track interest, not identity
-- ====================================================================
CREATE TABLE IF NOT EXISTS need_donor_interest (
    interest_id TEXT PRIMARY KEY,  -- UUID
    need_id TEXT NOT NULL,
    ein TEXT NOT NULL,

    -- Interest signal (Stewardship P2: anonymous aggregation only)
    interest_type TEXT NOT NULL CHECK(interest_type IN ('VIEW', 'SAVE', 'SHARE', 'VOLUNTEER_APPLICATION')),

    -- Metadata (org-level only, no PII)
    org_size TEXT,  -- Micro/Professional/Established
    referrer TEXT,  -- Where did user come from? (search, directory, donation page, etc.)

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(need_id) REFERENCES needs(need_id),
    FOREIGN KEY(ein) REFERENCES registry_enriched(EIN),
    INDEX idx_interest_need (need_id),
    INDEX idx_interest_ein (ein),
    INDEX idx_interest_type (interest_type),
    INDEX idx_interest_created (created_at)
);

-- ====================================================================
-- Indexes for Common Queries
-- ====================================================================

-- Donor discovery: "Show me FUNDING Needs in NY"
CREATE INDEX IF NOT EXISTS idx_needs_discovery ON needs(need_type, primary_state, status, published_date DESC);

-- Nonprofit dashboard: "Show me my published Needs"
CREATE INDEX IF NOT EXISTS idx_needs_nonprofit_dashboard ON needs(ein, status, published_date DESC);

-- Freshness check: "Which Needs need re-confirmation today?"
CREATE INDEX IF NOT EXISTS idx_needs_freshness_batch ON needs(ein, freshness_status, last_confirmed_date);

-- Interest trending: "Which Needs are getting most views?"
CREATE INDEX IF NOT EXISTS idx_interest_trending ON need_donor_interest(need_id, interest_type, created_at DESC);
