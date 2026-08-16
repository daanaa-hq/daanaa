"""Audit Logging System

Centralized logging for all critical actions:
- Event claims
- Donation link changes
- Hour approvals/rejections
- Hour submissions
- Account modifications
- Fraud reports

Usage:
  from audit_logging import log_event_claim, log_donation_link_change, etc.
  log_event_claim(ein, email, event_id, ip, user_agent)
"""

import sqlite3
import json
import secrets
import os
from datetime import datetime
from typing import Optional, Dict, Any

DB_PATH = os.environ.get("LIVE_DB_PATH", os.path.expanduser("~/meritgiving/data/daanaa_live.db"))

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

# ============================================================================
# EVENT CLAIM LOGGING
# ============================================================================

def log_event_claim(
    ein: str,
    email: str,
    event_id: int,
    ip_address: str,
    user_agent: str,
    status: str = 'verified'
) -> str:
    """Log event claim (non-repudiation trail)."""
    db = get_db()
    log_id = f"eventclaim_{secrets.token_hex(6)}"

    db.execute('''
        INSERT INTO event_claim_audit_log
        (id, ein, email, event_id, ip_address, user_agent, timestamp, status)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?)
    ''', (log_id, ein, email, event_id, ip_address, user_agent, status))

    db.commit()
    db.close()
    return log_id

# ============================================================================
# DONATION LINK CHANGE LOGGING
# ============================================================================

def log_donation_link_change(
    ein: str,
    email: str,
    old_url: Optional[str],
    new_url: str,
    ip_address: str,
    user_agent: str,
    status: str = 'pending_review'
) -> str:
    """Log donation link change request."""
    db = get_db()
    log_id = f"donlink_{secrets.token_hex(6)}"

    db.execute('''
        INSERT INTO donation_link_change_log
        (id, ein, requested_by_email, old_url, new_url, ip_address, user_agent,
         requested_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
    ''', (log_id, ein, email, old_url, new_url, ip_address, user_agent, status))

    db.commit()
    db.close()
    return log_id

def log_donation_link_review(
    log_id: str,
    reviewed_by: str,
    decision: str,  # 'approved' or 'rejected'
    reason: str
) -> None:
    """Log review of donation link change."""
    db = get_db()

    db.execute('''
        UPDATE donation_link_change_log
        SET reviewed_by = ?, reviewed_at = datetime('now'), decision = ?, reason = ?
        WHERE id = ?
    ''', (reviewed_by, decision, reason, log_id))

    db.commit()
    db.close()

# ============================================================================
# HOUR APPROVAL/REJECTION LOGGING
# ============================================================================

def log_hour_approval(
    hour_id: str,
    event_id: int,
    volunteer_id: str,
    volunteer_name: str,
    hours_approved: float,
    approved_by_email: str,
    ip_address: str,
    user_agent: str,
    status: str = 'approved',
    reason: Optional[str] = None
) -> str:
    """Log hour approval or rejection."""
    db = get_db()
    log_id = f"hourappr_{secrets.token_hex(6)}"

    db.execute('''
        INSERT INTO hour_approval_log
        (id, hour_id, event_id, volunteer_id, volunteer_name, hours_approved,
         approved_by_email, ip_address, user_agent, approved_at, status, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?)
    ''', (log_id, hour_id, event_id, volunteer_id, volunteer_name, hours_approved,
          approved_by_email, ip_address, user_agent, status, reason))

    db.commit()
    db.close()
    return log_id

# ============================================================================
# HOUR SUBMISSION LOGGING
# ============================================================================

def log_hour_submission(
    hour_id: str,
    event_id: int,
    volunteer_id: str,
    volunteer_email: str,
    hours_claimed: float,
    job_description: str,
    ip_address: str,
    user_agent: str,
    is_edit: bool = False,
    original_hours: Optional[float] = None
) -> str:
    """Log volunteer hour submission."""
    db = get_db()
    log_id = f"hourlsub_{secrets.token_hex(6)}"

    db.execute('''
        INSERT INTO hour_submission_log
        (id, hour_id, event_id, volunteer_id, volunteer_email, hours_claimed,
         job_description, ip_address, user_agent, submitted_at, is_edit, original_hours)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?)
    ''', (log_id, hour_id, event_id, volunteer_id, volunteer_email, hours_claimed,
          job_description, ip_address, user_agent, is_edit, original_hours))

    db.commit()
    db.close()
    return log_id

# ============================================================================
# ACCOUNT MODIFICATION LOGGING
# ============================================================================

def log_account_change(
    ein: str,
    user_email: str,
    change_type: str,  # 'password_reset', 'email_change', 'access_revoked', etc.
    ip_address: str,
    user_agent: str,
    changed_by: str,  # 'user_self' or admin email
    reason: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> str:
    """Log account security changes."""
    db = get_db()
    log_id = f"acctchg_{secrets.token_hex(6)}"

    details_json = json.dumps(details) if details else None

    db.execute('''
        INSERT INTO account_change_log
        (id, ein, user_email, change_type, ip_address, user_agent, changed_at,
         changed_by, reason, details)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?, ?, ?)
    ''', (log_id, ein, user_email, change_type, ip_address, user_agent,
          changed_by, reason, details_json))

    db.commit()
    db.close()
    return log_id

# ============================================================================
# FRAUD REPORT LOGGING
# ============================================================================

def log_fraud_report(
    report_type: str,  # 'event_nonexistent', 'fake_donation_link', 'hours_mismatch', etc.
    reported_by_email: str,
    event_id: Optional[int],
    ein: Optional[str],
    description: str,
    ip_address: str,
    user_agent: str,
    evidence_url: Optional[str] = None
) -> str:
    """Log fraud report."""
    db = get_db()
    log_id = f"fraud_{secrets.token_hex(6)}"

    db.execute('''
        INSERT INTO fraud_report_log
        (id, report_type, reported_by_email, event_id, ein, description,
         ip_address, user_agent, reported_at, evidence_url, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, 'under_review')
    ''', (log_id, report_type, reported_by_email, event_id, ein, description,
          ip_address, user_agent, evidence_url))

    db.commit()
    db.close()
    return log_id

def log_fraud_review(
    log_id: str,
    reviewed_by: str,
    finding: str,  # 'confirmed_fraud', 'dismissed', 'requires_investigation'
    action_taken: Optional[str] = None,  # 'organization_suspended', 'volunteer_banned', etc.
    law_enforcement_contacted: bool = False
) -> None:
    """Log fraud investigation result."""
    db = get_db()

    db.execute('''
        UPDATE fraud_report_log
        SET reviewed_by = ?, reviewed_at = datetime('now'), status = ?,
            action_taken = ?, law_enforcement_contacted = ?
        WHERE id = ?
    ''', (reviewed_by, finding, action_taken, law_enforcement_contacted, log_id))

    db.commit()
    db.close()

# ============================================================================
# QUERY HELPERS (for admin/compliance)
# ============================================================================

def get_audit_trail(ein: str, days: int = 90) -> Dict[str, Any]:
    """Get complete audit trail for an organization (compliance report)."""
    db = get_db()

    cutoff_date = f"datetime('now', '-{days} days')"

    event_claims = db.execute(f'''
        SELECT * FROM event_claim_audit_log
        WHERE ein = ? AND timestamp > {cutoff_date}
        ORDER BY timestamp DESC
    ''', (ein,)).fetchall()

    donation_changes = db.execute(f'''
        SELECT * FROM donation_link_change_log
        WHERE ein = ? AND requested_at > {cutoff_date}
        ORDER BY requested_at DESC
    ''', (ein,)).fetchall()

    hour_approvals = db.execute(f'''
        SELECT * FROM hour_approval_log
        WHERE (SELECT ein FROM volunteer_events WHERE id = hour_approval_log.event_id) = ?
        AND approved_at > {cutoff_date}
        ORDER BY approved_at DESC
    ''', (ein,)).fetchall()

    account_changes = db.execute(f'''
        SELECT * FROM account_change_log
        WHERE ein = ? AND changed_at > {cutoff_date}
        ORDER BY changed_at DESC
    ''', (ein,)).fetchall()

    fraud_reports = db.execute(f'''
        SELECT * FROM fraud_report_log
        WHERE ein = ? AND reported_at > {cutoff_date}
        ORDER BY reported_at DESC
    ''', (ein,)).fetchall()

    db.close()

    return {
        'ein': ein,
        'days_covered': days,
        'event_claims': [dict(r) for r in event_claims],
        'donation_link_changes': [dict(r) for r in donation_changes],
        'hour_approvals': [dict(r) for r in hour_approvals],
        'account_changes': [dict(r) for r in account_changes],
        'fraud_reports': [dict(r) for r in fraud_reports]
    }
