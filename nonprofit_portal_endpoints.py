"""Nonprofit portal endpoints for letter generation."""

import uuid
import sqlite3
from datetime import datetime, timedelta
from flask import request, jsonify

DB_PATH = 'data/merit_registry.db'

def register_nonprofit_endpoints(app):
    """Register nonprofit portal routes on Flask app."""

    @app.route('/api/nonprofit/signup', methods=['POST'])
    def nonprofit_signup():
        """EIN + email signup."""
        data = request.json
        ein = data.get('ein', '').strip()
        email = data.get('email', '').strip()

        if not ein or not email:
            return jsonify({'error': 'EIN and email required'}), 400

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Check if org exists in registry
            cursor.execute('SELECT organization_name FROM registry_enriched WHERE EIN = ?', (ein,))
            org = cursor.fetchone()
            if not org:
                return jsonify({'error': 'Organization not found'}), 404

            # Create account
            account_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO nonprofit_accounts (id, ein, email, name)
                VALUES (?, ?, ?, ?)
            ''', (account_id, ein, email, org[0]))

            conn.commit()
            conn.close()

            # TODO: Send magic link email
            return jsonify({'account_id': account_id, 'message': 'Check email for verification link'}), 201

        except sqlite3.IntegrityError:
            return jsonify({'error': 'Email or EIN already registered'}), 409

    @app.route('/api/nonprofit/dashboard', methods=['GET'])
    def nonprofit_dashboard():
        """Get nonprofit dashboard (pending letters, credits)."""
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get org info
        cursor.execute('SELECT name FROM nonprofit_accounts WHERE ein = ?', (nonprofit_ein,))
        org = cursor.fetchone()
        if not org:
            return jsonify({'error': 'Not found'}), 404

        # Get pending letter requests
        cursor.execute('''
            SELECT id, donor_name, amount, donation_date, status
            FROM nonprofit_letter_requests
            WHERE nonprofit_ein = ? AND status = 'pending'
            ORDER BY created_at DESC
        ''', (nonprofit_ein,))
        pending = [{'id': row[0], 'donor_name': row[1], 'amount': row[2], 'donation_date': row[3], 'status': row[4]} for row in cursor.fetchall()]

        # Get letter credits
        cursor.execute('SELECT letters_remaining FROM letter_credits WHERE nonprofit_ein = ? ORDER BY purchased_at DESC LIMIT 1', (nonprofit_ein,))
        credit = cursor.fetchone()
        letters_remaining = credit[0] if credit else 0

        conn.close()

        return jsonify({
            'nonprofit_ein': nonprofit_ein,
            'name': org[0],
            'pending_letters': pending,
            'letters_remaining': letters_remaining
        })

    @app.route('/api/nonprofit/letter/<letter_id>/approve', methods=['POST'])
    def approve_letter(letter_id):
        """ED approves a letter request."""
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE nonprofit_letter_requests
            SET status = 'approved', approved_by = ?, approved_at = ?
            WHERE id = ? AND nonprofit_ein = ?
        ''', (nonprofit_ein, datetime.now().isoformat(), letter_id, nonprofit_ein))

        conn.commit()
        conn.close()

        return jsonify({'status': 'approved'}), 200

    @app.route('/api/nonprofit/letter/<letter_id>/generate', methods=['POST'])
    def generate_letter(letter_id):
        """Generate letter PDF after ED approval."""
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check letter is approved
        cursor.execute('''
            SELECT donor_name, amount, donation_date
            FROM nonprofit_letter_requests
            WHERE id = ? AND nonprofit_ein = ? AND status = 'approved'
        ''', (letter_id, nonprofit_ein))

        letter_data = cursor.fetchone()
        if not letter_data:
            conn.close()
            return jsonify({'error': 'Letter not found or not approved'}), 404

        # TODO: Generate PDF (use reportlab or weasyprint)
        # For now, return placeholder
        pdf_url = f's3://daanaa-letters/{nonprofit_ein}/{letter_id}.pdf'

        # Update letter status
        cursor.execute('''
            UPDATE nonprofit_letter_requests
            SET status = 'generated'
            WHERE id = ?
        ''', (letter_id,))

        # Decrement credits
        cursor.execute('''
            UPDATE letter_credits
            SET letters_remaining = letters_remaining - 1
            WHERE nonprofit_ein = ?
        ''', (nonprofit_ein,))

        conn.commit()
        conn.close()

        return jsonify({'pdf_url': pdf_url, 'status': 'generated'}), 200

    @app.route('/api/nonprofit/purchase-letters', methods=['POST'])
    def purchase_letters():
        """Buy 100 letters for $10 (Stripe integration)."""
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        # TODO: Integrate Stripe
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        credit_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO letter_credits (id, nonprofit_ein, letters_remaining)
            VALUES (?, ?, 100)
        ''', (credit_id, nonprofit_ein))

        conn.commit()
        conn.close()

        return jsonify({'credit_id': credit_id, 'letters_added': 100}), 201
