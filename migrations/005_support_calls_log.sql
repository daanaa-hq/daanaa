-- Migration 005: Support calls log for voice support line
-- Tracks inbound calls to +1-747-832-2622, transfers to founder

CREATE TABLE IF NOT EXISTS support_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_phone TEXT NOT NULL,
    call_sid TEXT UNIQUE,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_support_calls_phone ON support_calls(from_phone);
CREATE INDEX IF NOT EXISTS idx_support_calls_received ON support_calls(received_at);
