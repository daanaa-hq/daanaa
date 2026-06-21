"""Nonprofit portal endpoints for letter generation."""

import uuid
import sqlite3
import os
from datetime import datetime, timedelta
from flask import request, jsonify, send_file

DB_PATH = 'data/merit_registry.db'

# Email service (imported from scripts/)
try:
    from email_service import nonprofit_signup_email, get_email_service
except ImportError:
    nonprofit_signup_email = None
    get_email_service = None

# Letter generation
try:
    from letter_generator import generate_donation_letter
except ImportError:
    generate_donation_letter = None

def _get_portal_analytics():
    """Get nonprofit portal usage analytics."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Total signups
    cursor.execute('SELECT COUNT(*) FROM nonprofit_accounts')
    total_signups = cursor.fetchone()[0]

    # Total letter requests
    cursor.execute('SELECT COUNT(*) FROM nonprofit_letter_requests')
    total_requests = cursor.fetchone()[0]

    # Letter requests by status
    cursor.execute('''
        SELECT status, COUNT(*) as count
        FROM nonprofit_letter_requests
        GROUP BY status
    ''')
    by_status = dict(cursor.fetchall())

    # Total credits purchased
    cursor.execute('SELECT SUM(COALESCE(lc_original.letters_purchased, 0)) FROM (
        SELECT nonprofit_ein, COUNT(*) as letters_purchased FROM letter_credits GROUP BY nonprofit_ein
    ) as lc_original')
    total_credits_purchased = cursor.fetchone()[0] or 0

    # Total letters generated
    generated_count = by_status.get('generated', 0)

    # Credits remaining (sum across all nonprofits)
    cursor.execute('SELECT SUM(letters_remaining) FROM letter_credits')
    credits_remaining = cursor.fetchone()[0] or 0

    conn.close()

    return {
        'total_signups': total_signups,
        'total_letter_requests': total_requests,
        'requests_by_status': by_status,
        'letters_generated': generated_count,
        'pending_approvals': by_status.get('pending', 0),
        'approved_not_generated': by_status.get('approved', 0),
        'total_credits_purchased': total_credits_purchased * 100,  # Each record = 100 letters
        'total_credits_remaining': credits_remaining,
        'estimated_revenue': total_credits_purchased * 10,  # $10 per 100-letter pack
    }


def register_nonprofit_endpoints(app):
    """Register nonprofit portal routes on Flask app."""

    @app.route('/api/nonprofit/analytics', methods=['GET'])
    def nonprofit_analytics():
        """Get nonprofit portal usage metrics (admin only)."""
        auth = request.headers.get('Authorization', '')
        admin_key = auth.split(' ')[-1] if auth else None
        expected_key = os.environ.get('DAANAA_ADMIN_KEY', '')

        # Allow both admin key and local dev
        if admin_key != expected_key and expected_key:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            analytics = _get_portal_analytics()
            return jsonify(analytics), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

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

            # Send magic link email
            if nonprofit_signup_email and get_email_service:
                magic_link = f"{os.environ.get('DAANAA_FRONTEND_URL', 'https://daanaa.org')}/nonprofit/verify?id={account_id}"
                template = nonprofit_signup_email(org[0], email, magic_link)
                email_service = get_email_service()
                email_service.send(
                    to_email=email,
                    subject=template.subject,
                    html=template.html,
                    plain_text=template.plain_text,
                )

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

        # Get letter details + nonprofit info
        cursor.execute('''
            SELECT nlr.donor_name, nlr.amount, nlr.donation_date,
                   na.name, na.email
            FROM nonprofit_letter_requests nlr
            JOIN nonprofit_accounts na ON nlr.nonprofit_ein = na.ein
            WHERE nlr.id = ? AND nlr.nonprofit_ein = ? AND nlr.status = 'approved'
        ''', (letter_id, nonprofit_ein))

        letter_data = cursor.fetchone()
        if not letter_data:
            conn.close()
            return jsonify({'error': 'Letter not found or not approved'}), 404

        donor_name, amount, donation_date, nonprofit_name, nonprofit_email = letter_data

        # Generate PDF
        if generate_donation_letter:
            try:
                pdf_bytes = generate_donation_letter(
                    nonprofit_name=nonprofit_name,
                    nonprofit_ein=nonprofit_ein,
                    donor_name=donor_name or 'Honored Donor',
                    amount=amount,
                    donation_date=donation_date,
                    nonprofit_address=nonprofit_name  # TODO: fetch real address from registry
                )

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

                # Return PDF as attachment
                from io import BytesIO
                return send_file(
                    BytesIO(pdf_bytes),
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f'donation_letter_{letter_id}.pdf'
                )
            except Exception as e:
                conn.close()
                return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500
        else:
            conn.close()
            return jsonify({'error': 'PDF generation service unavailable'}), 503

    @app.route('/api/nonprofit/purchase-letters', methods=['POST'])
    def purchase_letters():
        """Buy 100 letters for $10 via Stripe."""
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        body = request.json or {}
        stripe_payment_method_id = body.get('paymentMethodId')

        # For now, stub the Stripe call — real integration requires STRIPE_API_KEY env var
        # When Stripe is set up, this will call stripe.PaymentIntent.create() with the payment method
        if not stripe_payment_method_id:
            return jsonify({'error': 'Payment method required'}), 400

        try:
            # TODO: Call Stripe API to charge $10
            # stripe.PaymentIntent.create(
            #   amount=1000,  # $10 in cents
            #   currency='usd',
            #   payment_method=stripe_payment_method_id,
            #   confirm=True,
            # )

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            credit_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO letter_credits (id, nonprofit_ein, letters_remaining)
                VALUES (?, ?, 100)
            ''', (credit_id, nonprofit_ein))

            conn.commit()
            conn.close()

            return jsonify({'credit_id': credit_id, 'letters_added': 100, 'amount': 1000}), 201
        except Exception as e:
            return jsonify({'error': f'Payment failed: {str(e)}'}), 402
