"""
Needs Network API Routes

Routes for Phase 3B (Needs Network backend):
- GET /api/needs — search Needs (filter by type, cause, location, status)
- POST /api/nonprofits/{ein}/needs — create Need
- GET /api/nonprofits/{ein}/needs — list org's Needs
- PATCH /api/needs/{need_id} — update Need
- POST /api/nonprofits/{ein}/needs/intake — submit raw intake (voice/text/document)
- POST /api/needs/{need_id}/confirm — nonprofit confirms Need is still valid
- GET /api/needs/{need_id}/donor-interest — see who's interested in this Need

Privacy: Stewardship P2 (aggregate interest only, no PII)
Validation: Zod on all inputs
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import sqlite3
from pathlib import Path

# ============================================================================
# TYPE DEFINITIONS (Zod-equivalent validation)
# ============================================================================

class NeedType:
    """Zod schema equivalent for creating a Need."""

    @staticmethod
    def validate(data: dict) -> tuple[bool, Optional[str]]:
        """Validate Need creation input."""
        required = ['ein', 'need_type', 'title', 'description']
        for field in required:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"

        if data['need_type'] not in ('FUNDING', 'VOLUNTEER'):
            return False, "need_type must be 'FUNDING' or 'VOLUNTEER'"

        if data['need_type'] == 'FUNDING' and data.get('amount_needed', 0) <= 0:
            return False, "FUNDING needs must have amount_needed > 0"

        return True, None


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

class NeedsDB:
    """Database operations for Needs Network."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def get_connection(self):
        """Get thread-safe connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_need(self, ein: str, need_type: str, title: str, description: str,
                   amount_needed: Optional[int] = None, deadline_date: Optional[str] = None,
                   cause_area: Optional[str] = None, service_states: Optional[List[str]] = None) -> dict:
        """Create a new Need (DRAFT status)."""

        need_id = f"{ein}-{need_type}-{datetime.utcnow().isoformat()}"

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO needs (
                    need_id, ein, need_type, title, description,
                    amount_needed, deadline_date, cause_area, service_states,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT', ?)
            """, (
                need_id, ein, need_type, title, description,
                amount_needed, deadline_date, cause_area,
                json.dumps(service_states or []),
                datetime.utcnow().isoformat()
            ))
            conn.commit()

            return {
                'need_id': need_id,
                'ein': ein,
                'need_type': need_type,
                'title': title,
                'status': 'DRAFT',
                'created_at': datetime.utcnow().isoformat()
            }

        finally:
            conn.close()

    def list_nonprofit_needs(self, ein: str, status: Optional[str] = None) -> List[dict]:
        """List all Needs for a nonprofit."""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            query = "SELECT * FROM needs WHERE ein = ?"
            params = [ein]

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC"
            cursor.execute(query, params)

            return [dict(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    def search_needs(self, need_type: Optional[str] = None,
                    primary_state: Optional[str] = None,
                    cause_area: Optional[str] = None,
                    status: str = 'PUBLISHED') -> List[dict]:
        """Search Needs by filters (donor-facing)."""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            query = "SELECT * FROM needs WHERE status = ?"
            params = [status]

            if need_type:
                query += " AND need_type = ?"
                params.append(need_type)

            if primary_state:
                query += " AND (primary_state = ? OR service_states LIKE ?)"
                params.extend([primary_state, f'%{primary_state}%'])

            if cause_area:
                query += " AND cause_area = ?"
                params.append(cause_area)

            query += " ORDER BY published_date DESC LIMIT 100"
            cursor.execute(query, params)

            return [dict(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    def confirm_need(self, need_id: str, ein: str) -> bool:
        """Nonprofit confirms a Need is still valid (Stewardship P6)."""

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE needs
                SET last_confirmed_date = ?, freshness_status = 'CONFIRMED'
                WHERE need_id = ? AND ein = ?
            """, (datetime.utcnow().isoformat(), need_id, ein))

            conn.commit()
            return cursor.rowcount > 0

        finally:
            conn.close()

    def record_donor_interest(self, need_id: str, ein: str, interest_type: str,
                            org_size: Optional[str] = None, referrer: Optional[str] = None) -> bool:
        """Record donor/volunteer interest in a Need (Stewardship P2: aggregate only)."""

        interest_id = str(uuid.uuid4())

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO need_donor_interest (
                    interest_id, need_id, ein, interest_type, org_size, referrer, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (interest_id, need_id, ein, interest_type, org_size, referrer,
                  datetime.utcnow().isoformat()))

            # Increment click_count or volunteer_interest_count
            if interest_type == 'VIEW':
                cursor.execute("UPDATE needs SET click_count = click_count + 1 WHERE need_id = ?", (need_id,))
            elif interest_type == 'VOLUNTEER_APPLICATION':
                cursor.execute("UPDATE needs SET volunteer_interest_count = volunteer_interest_count + 1 WHERE need_id = ?", (need_id,))

            conn.commit()
            return True

        finally:
            conn.close()


# ============================================================================
# API ROUTE HANDLERS (to be integrated into daanaa_api.py)
# ============================================================================

# These are handler functions ready to be added as routes:

def get_needs(need_type: Optional[str] = None,
             primary_state: Optional[str] = None,
             cause_area: Optional[str] = None) -> dict:
    """
    GET /api/needs

    Search for published Needs.

    Query params:
    - need_type: 'FUNDING' or 'VOLUNTEER'
    - primary_state: 'NY', 'CA', 'NATIONAL'
    - cause_area: 'Food', 'Health', etc.

    Returns: { 'needs': [...], 'total': N }
    """
    db = NeedsDB(Path.home() / 'meritgiving' / 'data' / 'merit_registry.db')
    needs = db.search_needs(need_type, primary_state, cause_area)

    return {
        'needs': needs,
        'total': len(needs)
    }


def get_nonprofit_needs(ein: str, status: Optional[str] = None) -> dict:
    """
    GET /api/nonprofits/{ein}/needs

    Get all Needs for a nonprofit (nonprofit-facing dashboard).

    Returns: { 'needs': [...], 'total': N }
    """
    db = NeedsDB(Path.home() / 'meritgiving' / 'data' / 'merit_registry.db')
    needs = db.list_nonprofit_needs(ein, status)

    return {
        'needs': needs,
        'total': len(needs)
    }


def create_need(ein: str, body: dict) -> dict:
    """
    POST /api/nonprofits/{ein}/needs

    Create a new Need (draft status).

    Body: {
        "need_type": "FUNDING" | "VOLUNTEER",
        "title": "string",
        "description": "string",
        "amount_needed": 5000,  # if FUNDING
        "deadline_date": "2026-12-31",
        "cause_area": "Food",
        "service_states": ["NY", "NJ"]
    }

    Returns: { 'need_id': '...', 'status': 'DRAFT', ... }
    """
    # Validate input
    valid, error = NeedType.validate(body)
    if not valid:
        return {'error': error}, 400

    db = NeedsDB(Path.home() / 'meritgiving' / 'data' / 'merit_registry.db')

    need = db.create_need(
        ein=ein,
        need_type=body['need_type'],
        title=body['title'],
        description=body['description'],
        amount_needed=body.get('amount_needed'),
        deadline_date=body.get('deadline_date'),
        cause_area=body.get('cause_area'),
        service_states=body.get('service_states')
    )

    return need, 201


def confirm_need(need_id: str, ein: str) -> dict:
    """
    POST /api/needs/{need_id}/confirm

    Nonprofit confirms a Need is still valid (Stewardship P6).
    Re-confirmation required every 30 days for freshness.

    Returns: { 'success': true, 'last_confirmed': '...' }
    """
    db = NeedsDB(Path.home() / 'meritgiving' / 'data' / 'merit_registry.db')
    success = db.confirm_need(need_id, ein)

    if not success:
        return {'error': 'Need not found or not owned by this nonprofit'}, 404

    return {'success': True, 'last_confirmed': datetime.utcnow().isoformat()}, 200


def record_need_interest(need_id: str, interest_type: str, org_size: Optional[str] = None) -> dict:
    """
    POST /api/needs/{need_id}/interest

    Record donor/volunteer interest in a Need (Stewardship P2: aggregate only).

    Body: {
        "interest_type": "VIEW" | "SAVE" | "SHARE" | "VOLUNTEER_APPLICATION",
        "org_size": "Micro" | "Professional" | "Established"  (optional)
    }

    Returns: { 'success': true }
    """
    db = NeedsDB(Path.home() / 'meritgiving' / 'data' / 'merit_registry.db')

    # Fetch the Need to get EIN
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ein FROM needs WHERE need_id = ?", (need_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {'error': 'Need not found'}, 404

    ein = row[0]
    db.record_donor_interest(need_id, ein, interest_type, org_size)

    return {'success': True}, 200


# ============================================================================
# FRESHNESS AUTOMATION (runs nightly via cron)
# ============================================================================

def check_needs_freshness() -> dict:
    """
    Nightly job: Check if any Needs need re-confirmation.

    Logic:
    - If last_confirmed_date > 30 days ago: Send re-confirmation request
    - If no response after 60 days: Auto-archive

    Called by: overnight_pipeline.py (around 2 AM daily)
    """
    db = NeedsDB(Path.home() / 'meritgiving' / 'data' / 'merit_registry.db')
    conn = db.get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()
    thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
    sixty_days_ago = (datetime.utcnow() - timedelta(days=60)).isoformat()

    try:
        # 1. Find Needs that haven't been confirmed in 30+ days
        cursor.execute("""
            SELECT need_id, ein FROM needs
            WHERE status = 'PUBLISHED'
            AND (last_confirmed_date IS NULL OR last_confirmed_date < ?)
            AND freshness_status != 'PENDING_CONFIRMATION'
        """, (thirty_days_ago,))

        needs_to_confirm = cursor.fetchall()

        for need_id, ein in needs_to_confirm:
            # Create freshness check record
            cursor.execute("""
                INSERT INTO need_freshness_log (
                    freshness_check_id, need_id, ein,
                    sent_at, due_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), need_id, ein, now,
                  (datetime.utcnow() + timedelta(days=7)).isoformat()))

            # Mark Need as pending confirmation
            cursor.execute(
                "UPDATE needs SET freshness_status = 'PENDING_CONFIRMATION' WHERE need_id = ?",
                (need_id,)
            )

        # 2. Auto-archive Needs with no response after 60 days
        cursor.execute("""
            UPDATE needs
            SET status = 'ARCHIVED', archived_date = ?, freshness_status = 'UNRESPONSIVE'
            WHERE freshness_status = 'PENDING_CONFIRMATION'
            AND created_at < ?
            AND status = 'PUBLISHED'
        """, (now, sixty_days_ago))

        conn.commit()

        return {
            'needs_pending_confirmation': len(needs_to_confirm),
            'needs_auto_archived': cursor.rowcount
        }

    finally:
        conn.close()
