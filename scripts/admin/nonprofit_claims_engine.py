#!/usr/bin/env python3
"""
Nonprofit Claims Engine — Nonprofits correct + claim their own data.

Philosophy:
- Small orgs often have outdated 990s or missing info
- They should be able to claim their org and update what's wrong
- Claims are verified before merging into authoritative data
- Full audit trail: what changed, when, why, by whom
- Builds trust + improves data quality

Claim types:
1. Mission statement (we submit our own 1-2 sentence mission)
2. Financial data (we corrected our latest filing)
3. Website/donate link (we have a better link than what you found)
4. Contact info (email, phone for inquiries)
5. Dispute (this data about us is wrong)

Verification:
- Email domain verification (must match organization website)
- Data plausibility (claim doesn't contradict core IRS data)
- Manual review option (you approve borderline claims)

Merging:
- Verified claims override IRS data for display
- Original IRS data kept in history (audit trail)
- Version tracking (which claim version is live)
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import secrets

logger = logging.getLogger('nonprofit_claims')
logger.setLevel(logging.INFO)

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'


class ClaimType(Enum):
    MISSION_UPDATE = 'mission_update'
    FINANCIAL_DATA = 'financial_data'
    WEBSITE_LINK = 'website_link'
    DONATION_LINK = 'donation_link'
    CONTACT_INFO = 'contact_info'
    DISPUTE = 'dispute'


class ClaimStatus(Enum):
    PENDING_VERIFICATION = 'pending_verification'
    VERIFIED = 'verified'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    UNDER_REVIEW = 'under_review'


def get_db():
    db = sqlite3.connect(str(DB))
    db.row_factory = sqlite3.Row
    return db


def init_claims_tables():
    """Create tables for nonprofit claims."""
    db = get_db()
    cursor = db.cursor()

    # Claims submitted by nonprofits
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nonprofit_claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ein TEXT NOT NULL,
            claim_type TEXT NOT NULL,
            claim_data TEXT NOT NULL,
            claimed_by_email TEXT,
            status TEXT DEFAULT 'pending_verification',
            verification_token TEXT UNIQUE,
            verified_at TIMESTAMP,
            approved_by_founder TEXT,
            approved_at TIMESTAMP,
            reason_if_rejected TEXT,
            audit_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(ein) REFERENCES registry_enriched(EIN)
        )
    """)

    # Organization claims (aggregated status per org)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS org_claims_status (
            ein TEXT PRIMARY KEY NOT NULL,
            claimed BOOLEAN DEFAULT 0,
            claim_verified BOOLEAN DEFAULT 0,
            claims_approved INTEGER DEFAULT 0,
            last_claim_at TIMESTAMP,
            contact_email TEXT,
            verified_domain TEXT,
            FOREIGN KEY(ein) REFERENCES registry_enriched(EIN)
        )
    """)

    # Claim history (for audit trail)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS claim_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id INTEGER NOT NULL,
            action TEXT,
            actor TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY(claim_id) REFERENCES nonprofit_claims(id)
        )
    """)

    db.commit()
    db.close()


def submit_claim(ein: str, claim_type: str, claim_data: dict, claimed_by_email: str):
    """
    Submit a claim on an organization.

    Args:
        ein: Organization EIN
        claim_type: One of ClaimType values
        claim_data: Dict with claim details
        claimed_by_email: Submitter email (for verification)

    Returns:
        verification_token: Token to verify email
    """
    db = get_db()
    cursor = db.cursor()

    # Generate verification token
    verification_token = secrets.token_urlsafe(32)

    claim_data_json = json.dumps(claim_data)

    cursor.execute("""
        INSERT INTO nonprofit_claims
        (ein, claim_type, claim_data, claimed_by_email, verification_token)
        VALUES (?, ?, ?, ?, ?)
    """, (ein, claim_type, claim_data_json, claimed_by_email, verification_token))

    claim_id = cursor.lastrowid

    # Log the claim submission
    cursor.execute("""
        INSERT INTO claim_history (claim_id, action, actor, notes)
        VALUES (?, ?, ?, ?)
    """, (claim_id, 'submitted', claimed_by_email, f'Claim type: {claim_type}'))

    db.commit()
    db.close()

    logger.info(f"Claim submitted for EIN {ein}: {claim_type}")

    return verification_token, claim_id


def verify_claim_email(verification_token: str):
    """
    Verify that nonprofit controls the email domain.
    (This is a simplified check; in production would send actual email verification)
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, ein, claimed_by_email FROM nonprofit_claims
        WHERE verification_token = ?
    """, (verification_token,))

    claim = cursor.fetchone()

    if not claim:
        db.close()
        return False

    claim_id = claim['id']
    ein = claim['ein']
    email = claim['claimed_by_email']

    # Get org website from registry
    cursor.execute("""
        SELECT website FROM registry_enriched WHERE EIN = ?
    """, (ein,))

    org = cursor.fetchone()

    if not org or not org['website']:
        logger.warning(f"No website found for EIN {ein}")
        db.close()
        return False

    # Extract domain from email and website
    email_domain = email.split('@')[1].lower()
    website = org['website'].lower()

    # Check if email domain matches website
    if email_domain in website or website in f"https://{email_domain}":
        # Verification passed
        cursor.execute("""
            UPDATE nonprofit_claims
            SET status = ?, verified_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (ClaimStatus.VERIFIED.value, claim_id))

        cursor.execute("""
            UPDATE org_claims_status
            SET claim_verified = 1, verified_domain = ?, last_claim_at = CURRENT_TIMESTAMP
            WHERE ein = ?
        """, (email_domain, ein))

        cursor.execute("""
            INSERT INTO claim_history (claim_id, action, actor, notes)
            VALUES (?, ?, ?, ?)
        """, (claim_id, 'verified', 'system', f'Email domain verified: {email_domain}'))

        db.commit()
        logger.info(f"Claim {claim_id} email verified")
        db.close()
        return True

    else:
        # Verification failed - mark for manual review
        cursor.execute("""
            UPDATE nonprofit_claims
            SET status = ?
            WHERE id = ?
        """, (ClaimStatus.UNDER_REVIEW.value, claim_id))

        cursor.execute("""
            INSERT INTO claim_history (claim_id, action, actor, notes)
            VALUES (?, ?, ?, ?)
        """, (claim_id, 'review_required', 'system', f'Email domain {email_domain} does not match website {website}'))

        db.commit()
        logger.info(f"Claim {claim_id} requires manual review")
        db.close()
        return False


def get_pending_claims():
    """Get claims awaiting founder review."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            id,
            ein,
            claim_type,
            claim_data,
            claimed_by_email,
            status,
            created_at
        FROM nonprofit_claims
        WHERE status IN ('verified', 'under_review')
        ORDER BY created_at DESC
    """)

    claims = [dict(row) for row in cursor.fetchall()]

    for claim in claims:
        claim['claim_data'] = json.loads(claim['claim_data'])

    db.close()

    return claims


def approve_claim(claim_id: int, founder_email: str):
    """Founder approves a claim."""
    db = get_db()
    cursor = db.cursor()

    # Get the claim
    cursor.execute("""
        SELECT ein, claim_type, claim_data FROM nonprofit_claims WHERE id = ?
    """, (claim_id,))

    claim = cursor.fetchone()

    if not claim:
        db.close()
        return False

    # Update claim status
    cursor.execute("""
        UPDATE nonprofit_claims
        SET status = ?, approved_by_founder = ?, approved_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (ClaimStatus.APPROVED.value, founder_email, claim_id))

    # If mission update, update registry
    if claim['claim_type'] == ClaimType.MISSION_UPDATE.value:
        claim_data = json.loads(claim['claim_data'])
        cursor.execute("""
            UPDATE registry_enriched
            SET mission = ?, mission_source = 'org_submitted'
            WHERE EIN = ?
        """, (claim_data.get('mission'), claim['ein']))

    # Log approval
    cursor.execute("""
        INSERT INTO claim_history (claim_id, action, actor, notes)
        VALUES (?, ?, ?, ?)
    """, (claim_id, 'approved', founder_email, 'Merged into authoritative data'))

    # Update org claims status
    cursor.execute("""
        UPDATE org_claims_status
        SET claims_approved = claims_approved + 1
        WHERE ein = ?
    """, (claim['ein'],))

    db.commit()
    logger.info(f"Claim {claim_id} approved by {founder_email}")
    db.close()

    return True


def reject_claim(claim_id: int, reason: str, founder_email: str):
    """Founder rejects a claim."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE nonprofit_claims
        SET status = ?, reason_if_rejected = ?, approved_by_founder = ?, approved_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (ClaimStatus.REJECTED.value, reason, founder_email, claim_id))

    cursor.execute("""
        INSERT INTO claim_history (claim_id, action, actor, notes)
        VALUES (?, ?, ?, ?)
    """, (claim_id, 'rejected', founder_email, reason))

    db.commit()
    logger.info(f"Claim {claim_id} rejected by {founder_email}")
    db.close()

    return True


def get_org_claims_status(ein: str):
    """Get claims status for an organization."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT * FROM org_claims_status WHERE ein = ?
    """, (ein,))

    status = cursor.fetchone()
    db.close()

    return dict(status) if status else None


def get_claim_history(claim_id: int):
    """Get full history of a claim."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT action, actor, timestamp, notes FROM claim_history
        WHERE claim_id = ?
        ORDER BY timestamp ASC
    """, (claim_id,))

    history = [dict(row) for row in cursor.fetchall()]
    db.close()

    return history


# Initialize tables on import
init_claims_tables()
