#!/usr/bin/env python3
"""
Link Verification Dashboard API.

Endpoints for reviewing, approving, editing, and rejecting discovered links
before they're deployed live.
"""

from flask import Blueprint, jsonify, request
import sqlite3
import json
from datetime import datetime
from pathlib import Path

verification_bp = Blueprint('verification', __name__, url_prefix='/api/verification')

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'


def get_db():
    """Get database connection."""
    db = sqlite3.connect(str(DB))
    db.row_factory = sqlite3.Row
    return db


def init_verification_table():
    """Create verification tracking table."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS link_verification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ein INTEGER NOT NULL UNIQUE,
            org_name TEXT NOT NULL,
            donate_url TEXT,
            donate_url_original TEXT,
            volunteer_url TEXT,
            volunteer_url_original TEXT,
            status TEXT DEFAULT 'pending',
            verified_by TEXT,
            verified_at TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.commit()
    db.close()


@verification_bp.route('/pending', methods=['GET'])
def get_pending_links():
    """Get next batch of unverified links."""
    limit = request.args.get('limit', 10, type=int)

    db = get_db()
    cursor = db.cursor()

    # Get pending links from test queue or deployment queue (with website)
    cursor.execute("""
        SELECT
            ldq.ein,
            re.organization_name,
            re.website,
            ldq.links
        FROM link_deployment_queue ldq
        JOIN registry_enriched re ON ldq.ein = re.EIN
        WHERE ldq.deployed_at IS NULL
        ORDER BY ldq.created_at ASC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    db.close()

    items = []
    for row in rows:
        links = json.loads(row['links'])
        website = row['website']
        # Add scheme if missing
        if website and not website.startswith(('http://', 'https://')):
            website = 'https://' + website

        items.append({
            'ein': row['ein'],
            'org_name': row['organization_name'],
            'website': website,
            'donate_url': links.get('donate_url', ''),
            'volunteer_url': links.get('volunteer_url', ''),
            'donate_button_text': links.get('donate_button_text', ''),
            'status': 'pending'
        })

    return jsonify({
        'total_pending': len(items),
        'items': items
    })


@verification_bp.route('/approve', methods=['POST'])
def approve_link():
    """Approve a link for deployment."""
    data = request.get_json()
    ein = data.get('ein')
    verified_by = data.get('verified_by', 'manual')
    notes = data.get('notes', '')

    if not ein:
        return jsonify({'error': 'EIN required'}), 400

    db = get_db()
    cursor = db.cursor()

    # Mark as deployed
    cursor.execute("""
        UPDATE link_deployment_queue
        SET deployed_at = ?
        WHERE ein = ? AND deployed_at IS NULL
    """, (datetime.now().isoformat(), ein))

    # Update org in registry
    cursor.execute("""
        SELECT links FROM link_deployment_queue WHERE ein = ?
    """, (ein,))

    result = cursor.fetchone()
    if result:
        links = json.loads(result['links'])

        updates = []
        values = []

        if 'donate_url' in links:
            updates.extend(["donate_url = ?", "donate_url_status = 'verified'", "donate_checked_at = ?"])
            values.extend([links['donate_url'], datetime.now().isoformat()])

        if 'volunteer_url' in links:
            updates.append("volunteer_url = ?")
            values.append(links['volunteer_url'])

        if updates:
            updates.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(ein)

            query = f"UPDATE registry_enriched SET {', '.join(updates)} WHERE EIN = ?"
            cursor.execute(query, values)

    db.commit()
    db.close()

    return jsonify({'status': 'approved', 'ein': ein})


@verification_bp.route('/reject', methods=['POST'])
def reject_link():
    """Reject a link and remove from queue."""
    data = request.get_json()
    ein = data.get('ein')
    reason = data.get('reason', 'Rejected by user')

    if not ein:
        return jsonify({'error': 'EIN required'}), 400

    db = get_db()
    cursor = db.cursor()

    # Move to rejected queue
    cursor.execute("""
        INSERT INTO link_test_queue (ein, reason)
        SELECT ein, ? FROM link_deployment_queue WHERE ein = ?
    """, (reason, ein))

    # Remove from deployment queue
    cursor.execute("DELETE FROM link_deployment_queue WHERE ein = ?", (ein,))

    db.commit()
    db.close()

    return jsonify({'status': 'rejected', 'ein': ein})


@verification_bp.route('/edit', methods=['POST'])
def edit_link():
    """Edit and approve a link."""
    data = request.get_json()
    ein = data.get('ein')
    donate_url = data.get('donate_url')
    volunteer_url = data.get('volunteer_url')

    if not ein:
        return jsonify({'error': 'EIN required'}), 400

    db = get_db()
    cursor = db.cursor()

    # Update queue with corrected links
    links = {}
    if donate_url:
        links['donate_url'] = donate_url
    if volunteer_url:
        links['volunteer_url'] = volunteer_url

    cursor.execute("""
        UPDATE link_deployment_queue
        SET links = ?, deployed_at = ?
        WHERE ein = ?
    """, (json.dumps(links), datetime.now().isoformat(), ein))

    db.commit()
    db.close()

    return jsonify({'status': 'edited_and_approved', 'ein': ein})


@verification_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get verification stats."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM link_deployment_queue WHERE deployed_at IS NULL")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM link_deployment_queue WHERE deployed_at IS NOT NULL")
    approved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM link_test_queue")
    rejected = cursor.fetchone()[0]

    db.close()

    return jsonify({
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'total': pending + approved + rejected
    })


# Initialize on first load
init_verification_table()
