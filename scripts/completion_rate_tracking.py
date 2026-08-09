#!/usr/bin/env python3
"""
Completion Rate Tracking Infrastructure (Phase 3A)

Measures one-click giving effectiveness:
- "Donate Now" button clicks (entry point)
- Donation completion (from callback URL)
- Conversion rate (clicks → completed donations)

Uses:
- Plausible/Firebase events (frontend tracking)
- Callback URL query params (backend tracking)
- Database table: donation_completions

Phase 3A success metric: 30% completion rate (vs 5% cold baseline)
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

DB_PATH = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'

# ============================================================================
# DATABASE SCHEMA (to add to daanaa_api.py migrations)
# ============================================================================

SCHEMA = """
-- Track completion rates for "Donate Now" button (Phase 3A measurement)
CREATE TABLE IF NOT EXISTS donate_tracking (
    tracking_id TEXT PRIMARY KEY,  -- UUID: ein-timestamp
    ein TEXT NOT NULL,
    organization_name TEXT,

    -- Donor info (optional, from pre-fill)
    donor_email TEXT,
    donor_name TEXT,
    suggested_amount INTEGER,

    -- Events
    button_clicked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    redirect_url TEXT,  -- Where we sent the donor

    -- Completion signal (from callback)
    completion_url TEXT,  -- Where donor's org redirected back
    completed_at TEXT,    -- When callback arrived
    completed BOOLEAN DEFAULT FALSE,
    completion_amount INTEGER,  -- If provided in callback
    completion_reason TEXT,     -- Why completed (or failed)

    -- Metadata
    traffic_source TEXT,  -- direct, search, directory, email, etc.
    device_type TEXT,     -- mobile, desktop, tablet
    donor_segment TEXT,   -- Micro/Professional/Established org size

    -- Metrics
    time_to_completion_minutes REAL,  -- NULL if not completed
    status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'COMPLETED', 'ABANDONED', 'ERROR')),

    FOREIGN KEY(ein) REFERENCES registry_enriched(EIN),
    INDEX idx_donate_ein (ein),
    INDEX idx_donate_status (status),
    INDEX idx_donate_clicked (button_clicked_at),
    INDEX idx_donate_completed (completed_at)
);

-- Summary stats (refreshed nightly)
CREATE TABLE IF NOT EXISTS donate_completion_stats (
    stat_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    ein TEXT,

    total_clicks INTEGER DEFAULT 0,
    completed_count INTEGER DEFAULT 0,
    completion_rate REAL DEFAULT 0.0,  -- completed_count / total_clicks

    average_completion_time_minutes REAL,
    average_completion_amount INTEGER,

    traffic_breakdown TEXT,  -- JSON: {direct: N, search: N, ...}
    device_breakdown TEXT,   -- JSON: {mobile: N, desktop: N, ...}

    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(ein) REFERENCES registry_enriched(EIN),
    INDEX idx_stats_date (date),
    INDEX idx_stats_ein (ein)
);
"""

# ============================================================================
# TRACKING FUNCTIONS (to add to daanaa_api.py)
# ============================================================================

def track_donate_button_click(ein: str, donor_email: Optional[str] = None,
                             donor_name: Optional[str] = None,
                             suggested_amount: Optional[int] = None,
                             traffic_source: Optional[str] = None) -> str:
    """
    Track when "Donate Now" button is clicked.

    Called from frontend: trackCompletionMetric('donate_click', {ein, email, ...})

    Returns: tracking_id (to include in redirect URL)
    """
    import uuid
    tracking_id = str(uuid.uuid4())

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO donate_tracking (
                tracking_id, ein, donor_email, donor_name, suggested_amount,
                traffic_source, button_clicked_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING')
        """, (tracking_id, ein, donor_email, donor_name, suggested_amount,
              traffic_source, datetime.utcnow().isoformat()))

        conn.commit()
        return tracking_id

    finally:
        conn.close()


def track_donate_completion(tracking_id: str, completion_amount: Optional[int] = None,
                           completion_reason: Optional[str] = None) -> bool:
    """
    Track when donation is completed (callback from org's processor).

    Called via: GET /api/donate/complete?tracking_id=X&amount=Y&reason=Z

    Returns: True if recorded, False if not found
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT button_clicked_at FROM donate_tracking WHERE tracking_id = ?
        """, (tracking_id,))

        row = cursor.fetchone()
        if not row:
            return False

        button_clicked_at = row[0]
        completed_at = datetime.utcnow().isoformat()

        # Calculate time to completion (in minutes)
        from datetime import datetime as dt
        clicked = dt.fromisoformat(button_clicked_at)
        completed = dt.fromisoformat(completed_at)
        time_to_completion = (completed - clicked).total_seconds() / 60

        cursor.execute("""
            UPDATE donate_tracking
            SET completed = TRUE,
                completed_at = ?,
                completion_amount = ?,
                completion_reason = ?,
                time_to_completion_minutes = ?,
                status = 'COMPLETED'
            WHERE tracking_id = ?
        """, (completed_at, completion_amount, completion_reason,
              time_to_completion, tracking_id))

        conn.commit()
        return True

    finally:
        conn.close()


def get_completion_stats(ein: Optional[str] = None,
                        date_range: Optional[tuple] = None) -> Dict:
    """
    Get completion rate statistics.

    date_range: (start_date, end_date) in ISO format
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Total clicks
        query = "SELECT COUNT(*) FROM donate_tracking WHERE status IN ('COMPLETED', 'PENDING', 'ABANDONED')"
        params = []

        if ein:
            query += " AND ein = ?"
            params.append(ein)

        if date_range:
            query += " AND button_clicked_at >= ? AND button_clicked_at <= ?"
            params.extend(date_range)

        cursor.execute(query, params)
        total_clicks = cursor.fetchone()[0]

        # Completed clicks
        query = "SELECT COUNT(*) FROM donate_tracking WHERE status = 'COMPLETED'"
        params = []

        if ein:
            query += " AND ein = ?"
            params.append(ein)

        if date_range:
            query += " AND completed_at >= ? AND completed_at <= ?"
            params.extend(date_range)

        cursor.execute(query, params)
        completed_count = cursor.fetchone()[0]

        # Completion rate
        completion_rate = (completed_count / total_clicks * 100) if total_clicks > 0 else 0

        # Average time to completion
        query = "SELECT AVG(time_to_completion_minutes) FROM donate_tracking WHERE status = 'COMPLETED'"
        params = []

        if ein:
            query += " AND ein = ?"
            params.append(ein)

        cursor.execute(query, params)
        avg_time = cursor.fetchone()[0]

        # Average completion amount
        query = "SELECT AVG(completion_amount) FROM donate_tracking WHERE status = 'COMPLETED' AND completion_amount > 0"
        params = []

        if ein:
            query += " AND ein = ?"
            params.append(ein)

        cursor.execute(query, params)
        avg_amount = cursor.fetchone()[0]

        return {
            'total_clicks': total_clicks,
            'completed_count': completed_count,
            'completion_rate_percent': round(completion_rate, 2),
            'average_time_to_completion_minutes': round(avg_time, 2) if avg_time else None,
            'average_completion_amount': round(avg_amount, 2) if avg_amount else None,
            'status': 'PASS' if completion_rate >= 30 else ('NEUTRAL' if completion_rate >= 15 else 'NEEDS_IMPROVEMENT')
        }

    finally:
        conn.close()


def refresh_completion_stats():
    """
    Nightly job: aggregate daily stats into donate_completion_stats table.

    Called from: overnight_pipeline.py
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get all EINs with activity today
        cursor.execute("""
            SELECT DISTINCT ein FROM donate_tracking
            WHERE DATE(button_clicked_at) = DATE('now')
        """)

        eins = [row[0] for row in cursor.fetchall()]

        for ein in eins:
            stats = get_completion_stats(ein=ein)

            cursor.execute("""
                INSERT OR REPLACE INTO donate_completion_stats
                (stat_id, date, ein, total_clicks, completed_count, completion_rate, updated_at)
                VALUES (?, DATE('now'), ?, ?, ?, ?, ?)
            """, (f"{ein}-{datetime.utcnow().date()}", ein,
                  stats['total_clicks'], stats['completed_count'],
                  stats['completion_rate_percent'], datetime.utcnow().isoformat()))

        conn.commit()

    finally:
        conn.close()


# ============================================================================
# FRONTEND INTEGRATION (TypeScript)
# ============================================================================

FRONTEND_INTEGRATION = """
// Add to frontend/src/utils/analytics.ts or analytics.tsx

/**
 * Track Donate Now button clicks + completions (Phase 3A measurement)
 * Stewardship P3: Evidence-based measurement of one-click giving effectiveness
 */
export function trackDonateClick(ein: string, amount?: number, source?: string) {
  logEvent('donate_click', {
    ein,
    amount: amount?.toString() || 'unspecified',
    source: source || 'direct'
  })
}

export function trackDonateCompletion(trackingId: string, amount?: number) {
  logEvent('donate_completed', {
    tracking_id: trackingId,
    amount: amount?.toString() || 'unspecified'
  })
}

// In OrgInfoHierarchy.tsx or donation flow:
const handleDonateClick = (orgEin: string) => {
  trackDonateClick(orgEin, suggestedAmount, 'org_detail')

  // Redirect with tracking ID
  const trackingId = await fetch(
    '/api/donate/track?ein=' + orgEin + '&email=' + userEmail
  ).then(r => r.json()).then(d => d.tracking_id)

  // Include tracking_id in donate URL
  window.location.href = org.donate_url + '?tracking_id=' + trackingId
}
"""

if __name__ == '__main__':
    print("=" * 70)
    print("COMPLETION RATE TRACKING INFRASTRUCTURE")
    print("=" * 70)
    print("\nSchema (add to migrations):")
    print(SCHEMA)
    print("\n" + "=" * 70)
    print("Example usage:")
    print("=" * 70)
    print("""
# 1. Track button click
tracking_id = track_donate_button_click(
    ein='532000161',
    donor_email='donor@example.com',
    suggested_amount=50,
    traffic_source='directory'
)
print(f"Tracking ID: {tracking_id}")

# 2. Track completion (from callback)
track_donate_completion(tracking_id, completion_amount=50)

# 3. Get stats
stats = get_completion_stats(ein='532000161')
print(f"Completion rate: {stats['completion_rate_percent']}%")
print(f"Status: {stats['status']}")
    """)
    print("\n" + "=" * 70)
    print("Frontend integration code:")
    print("=" * 70)
    print(FRONTEND_INTEGRATION)
