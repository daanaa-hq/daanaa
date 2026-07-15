#!/usr/bin/env python3
"""
Nonprofit Claims API — Publicly accessible endpoint for claims submission + management.

Endpoints:
- POST /api/claims/submit — Submit a claim (nonprofits)
- GET /api/claims/{ein}/status — Check org claims status (public)
- GET /api/claims/pending — Get pending claims (founder only)
- POST /api/claims/{id}/approve — Approve claim (founder only)
- POST /api/claims/{id}/reject — Reject claim (founder only)
"""

from flask import Blueprint, jsonify, request
import sqlite3
from datetime import datetime
from pathlib import Path
import logging

claims_bp = Blueprint('claims', __name__, url_prefix='/api/claims')

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
logger = logging.getLogger('nonprofit_claims_api')

# Import claims functions
try:
    from nonprofit_claims_engine import (
        submit_claim,
        verify_claim_email,
        get_pending_claims,
        approve_claim,
        reject_claim,
        get_org_claims_status,
        get_claim_history,
    )
except ImportError:
    logger.warning("Could not import claims engine functions")


@claims_bp.route('/submit', methods=['POST'])
def submit_nonprofit_claim():
    """Submit a claim on organization data."""
    data = request.get_json()

    ein = data.get('ein')
    claim_type = data.get('claim_type')
    claim_data = data.get('claim_data', {})
    email = data.get('email')

    if not all([ein, claim_type, email]):
        return jsonify({'error': 'ein, claim_type, and email required'}), 400

    try:
        token, claim_id = submit_claim(ein, claim_type, claim_data, email)

        return jsonify({
            'status': 'submitted',
            'claim_id': claim_id,
            'verification_token': token,
            'message': f'Verification link sent to {email}',
            'verify_url': f'/api/claims/verify?token={token}'
        }), 201

    except Exception as e:
        logger.error(f"Error submitting claim: {e}")
        return jsonify({'error': str(e)}), 500


@claims_bp.route('/verify', methods=['GET'])
def verify_email():
    """Verify nonprofit email ownership (called from email link)."""
    token = request.args.get('token')

    if not token:
        return jsonify({'error': 'token required'}), 400

    try:
        verified = verify_claim_email(token)

        if verified:
            return jsonify({
                'status': 'verified',
                'message': 'Your email has been verified. Your claim is now under review.'
            })
        else:
            return jsonify({
                'status': 'under_review',
                'message': 'Email verification could not be completed automatically. Your claim will be manually reviewed.'
            }), 202

    except Exception as e:
        logger.error(f"Error verifying email: {e}")
        return jsonify({'error': str(e)}), 500


@claims_bp.route('/<ein>/status', methods=['GET'])
def get_status(ein):
    """Get claims status for an organization (public)."""
    try:
        status = get_org_claims_status(ein)

        if status:
            return jsonify(status)
        else:
            return jsonify({
                'ein': ein,
                'claimed': False,
                'message': 'No claims submitted for this organization'
            })

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500


@claims_bp.route('/pending', methods=['GET'])
def get_pending():
    """Get pending claims (founder only)."""
    # TODO: Add authentication check (X-Admin-Key header)
    try:
        claims = get_pending_claims()

        return jsonify({
            'pending_claims': claims,
            'total': len(claims),
            'awaiting_review': sum(1 for c in claims if c['status'] == 'under_review'),
            'verified': sum(1 for c in claims if c['status'] == 'verified'),
        })

    except Exception as e:
        logger.error(f"Error getting pending claims: {e}")
        return jsonify({'error': str(e)}), 500


@claims_bp.route('/<int:claim_id>/approve', methods=['POST'])
def approve(claim_id):
    """Approve a claim (founder only)."""
    # TODO: Add authentication check
    data = request.get_json()
    founder_email = data.get('founder_email', 'system')

    try:
        success = approve_claim(claim_id, founder_email)

        if success:
            return jsonify({'status': 'approved', 'claim_id': claim_id})
        else:
            return jsonify({'error': 'Claim not found'}), 404

    except Exception as e:
        logger.error(f"Error approving claim: {e}")
        return jsonify({'error': str(e)}), 500


@claims_bp.route('/<int:claim_id>/reject', methods=['POST'])
def reject(claim_id):
    """Reject a claim (founder only)."""
    data = request.get_json()
    reason = data.get('reason', 'No reason provided')
    founder_email = data.get('founder_email', 'system')

    try:
        success = reject_claim(claim_id, reason, founder_email)

        if success:
            return jsonify({'status': 'rejected', 'claim_id': claim_id})
        else:
            return jsonify({'error': 'Claim not found'}), 404

    except Exception as e:
        logger.error(f"Error rejecting claim: {e}")
        return jsonify({'error': str(e)}), 500


@claims_bp.route('/<int:claim_id>/history', methods=['GET'])
def history(claim_id):
    """Get audit history for a claim."""
    try:
        hist = get_claim_history(claim_id)

        return jsonify({
            'claim_id': claim_id,
            'history': hist,
        })

    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return jsonify({'error': str(e)}), 500


@claims_bp.route('/health', methods=['GET'])
def health():
    """Health check."""
    try:
        db = sqlite3.connect(str(DB))
        cursor = db.cursor()
        cursor.execute("SELECT 1 FROM nonprofit_claims LIMIT 1")
        db.close()
        return jsonify({'status': 'healthy'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503
