"""Nonprofit portal endpoints for letter generation, volunteer hours, and donor templates."""

import uuid
import sqlite3
import os
import threading
import csv
import secrets
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from flask import request, jsonify, send_file

# Respect the DB_PATH env override (same contract as daanaa_api.py). The old
# hardcoded relative literal meant tests could never isolate this module from
# the live DB — every portal endpoint 500'd under pytest ("database is locked"
# by the dev gunicorn) and test fixtures wrote rows into production data.
# Prod behavior is unchanged: DB_PATH is not set in .env or systemd.
DB_PATH = os.environ.get('DB_PATH', 'data/merit_registry.db')

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

    # Total credits purchased (estimate from credit records)
    cursor.execute('SELECT COUNT(*) FROM letter_credits')
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
        expected_key = os.environ.get('DAANAA_ADMIN_KEY', '')

        # If key is configured, require auth
        if expected_key:
            auth = request.headers.get('Authorization', '')
            admin_key = auth.split(' ')[-1] if auth else ''
            if admin_key != expected_key:
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
        """Disabled: requires verified nonprofit auth, not yet implemented."""
        return jsonify({
            'error': 'Nonprofit dashboard requires verified account authorization. '
                     'EIN-only access is not supported.'
        }), 401

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

    @app.route('/api/nonprofit/volunteer-hours', methods=['GET'])
    def get_volunteer_hours():
        """Disabled: volunteer hour feature requires verified nonprofit auth, not yet implemented."""
        return jsonify({
            'error': 'Volunteer hour logging is not yet available. '
                     'This feature requires verified nonprofit account authorization.'
        }), 503

        filter_status = request.args.get('status', 'all')  # all|pending|verified|rejected

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if filter_status == 'all':
            cursor.execute('''
                SELECT id, volunteer_name, volunteer_email, hours, service_date,
                       activity_description, status, submitted_at
                FROM volunteer_hours
                WHERE nonprofit_ein = ?
                ORDER BY submitted_at DESC
            ''', (nonprofit_ein,))
        else:
            cursor.execute('''
                SELECT id, volunteer_name, volunteer_email, hours, service_date,
                       activity_description, status, submitted_at
                FROM volunteer_hours
                WHERE nonprofit_ein = ? AND status = ?
                ORDER BY submitted_at DESC
            ''', (nonprofit_ein, filter_status))

        rows = cursor.fetchall()
        conn.close()

        records = [
            {
                'id': row[0],
                'volunteer_name': row[1],
                'volunteer_email': row[2],
                'hours': row[3],
                'service_date': row[4],
                'activity_description': row[5],
                'status': row[6],
                'submitted_at': row[7],
            }
            for row in rows
        ]

        return jsonify({'records': records, 'count': len(records)}), 200

    @app.route('/api/nonprofit/volunteer-hours', methods=['POST'])
    def submit_volunteer_hours():
        """Disabled: EIN-only auth is not a valid credential; feature not yet live."""
        return jsonify({
            'error': 'Volunteer hour submission is not yet available. '
                     'This feature requires verified nonprofit account authorization.'
        }), 503

        data = request.json or {}
        volunteer_name = data.get('volunteer_name', '').strip()
        volunteer_email = data.get('volunteer_email', '').strip()
        hours = data.get('hours', 0)
        service_date = data.get('service_date', '').strip()
        activity_description = data.get('activity_description', '').strip()

        if not all([volunteer_name, volunteer_email, hours, service_date, activity_description]):
            return jsonify({'error': 'All fields required'}), 400

        try:
            record_id = str(uuid.uuid4())
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO volunteer_hours
                (id, nonprofit_ein, volunteer_name, volunteer_email, hours,
                 service_date, activity_description, status, submitted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            ''', (record_id, nonprofit_ein, volunteer_name, volunteer_email, hours,
                  service_date, activity_description, datetime.now().isoformat()))

            conn.commit()
            conn.close()

            return jsonify({'id': record_id, 'status': 'pending'}), 201
        except Exception as e:
            return jsonify({'error': f'Failed to submit: {str(e)}'}), 500

    @app.route('/api/nonprofit/volunteer-hours/<record_id>/approve', methods=['POST'])
    def approve_volunteer_hours(record_id):
        """ED approves volunteer hours submission."""
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE volunteer_hours
                SET status = 'verified', approved_by = ?, approved_at = ?
                WHERE id = ? AND nonprofit_ein = ?
            ''', (nonprofit_ein, datetime.now().isoformat(), record_id, nonprofit_ein))

            conn.commit()
            conn.close()

            return jsonify({'status': 'verified'}), 200
        except Exception as e:
            return jsonify({'error': f'Failed to approve: {str(e)}'}), 500

    @app.route('/api/nonprofit/volunteer-hours/<record_id>/reject', methods=['POST'])
    def reject_volunteer_hours(record_id):
        """ED rejects volunteer hours submission with reason."""
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.json or {}
        reason = data.get('reason', '').strip()

        if not reason:
            return jsonify({'error': 'Rejection reason required'}), 400

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE volunteer_hours
                SET status = 'rejected', rejection_reason = ?, rejected_by = ?, rejected_at = ?
                WHERE id = ? AND nonprofit_ein = ?
            ''', (reason, nonprofit_ein, datetime.now().isoformat(), record_id, nonprofit_ein))

            conn.commit()
            conn.close()

            return jsonify({'status': 'rejected'}), 200
        except Exception as e:
            return jsonify({'error': f'Failed to reject: {str(e)}'}), 500

    @app.route('/api/nonprofit/volunteer-hours/export', methods=['POST'])
    def export_volunteer_hours():
        """
        Export volunteer hours as CSV (async background job).

        Authorization: Bearer token with nonprofit_ein
        Returns: { job_id: str, status: 'pending', message: str }
        Status codes:
          - 202: Export started (job_id returned, CSV will be generated async)
          - 401: Missing/invalid auth token
          - 500: Server error

        CSV output: volunteer_name, email, hours, service_date, activity, status, approved_date
        CSV written to /tmp/daanaa_exports/{job_id}.csv
        Poll /api/nonprofit/background-jobs/{job_id} to track status and get download_link
        """
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            job_id = str(uuid.uuid4())
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Create background job record
            cursor.execute('''
                INSERT INTO background_jobs (id, nonprofit_ein, job_type, status)
                VALUES (?, ?, 'export_volunteer_hours', 'pending')
            ''', (job_id, nonprofit_ein))
            conn.commit()
            conn.close()

            # Spawn background thread to generate CSV
            thread = threading.Thread(
                target=_generate_volunteer_csv_async,
                args=(job_id, nonprofit_ein)
            )
            thread.daemon = True
            thread.start()

            return jsonify({
                'job_id': job_id,
                'status': 'pending',
                'message': 'Export started. Poll /api/nonprofit/background-jobs/{} to check status'.format(job_id)
            }), 202
        except Exception as e:
            return jsonify({'error': f'Failed to start export: {str(e)}'}), 500

    @app.route('/api/nonprofit/background-jobs/<job_id>', methods=['GET'])
    def get_background_job_status(job_id):
        """
        Get status of a background job (CSV export, etc).

        Returns: { job_id, status, download_link?, created_at, completed_at?, error_message? }
        Status codes:
          - 200: Job found
          - 401: Unauthorized
          - 404: Job not found or not owned by nonprofit
        """
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, status, result_path, created_at, completed_at, error_message
                FROM background_jobs
                WHERE id = ? AND nonprofit_ein = ?
            ''', (job_id, nonprofit_ein))

            job = cursor.fetchone()
            conn.close()

            if not job:
                return jsonify({'error': 'Job not found'}), 404

            result = {
                'job_id': job[0],
                'status': job[1],
                'created_at': job[3],
            }

            if job[1] == 'complete':
                result['download_link'] = f'/api/nonprofit/exports/{job_id}.csv'
            elif job[1] == 'failed':
                result['error_message'] = job[5]

            if job[4]:
                result['completed_at'] = job[4]

            return jsonify(result), 200
        except Exception as e:
            return jsonify({'error': f'Failed to get job status: {str(e)}'}), 500

    @app.route('/api/nonprofit/exports/<job_id>.csv', methods=['GET'])
    def download_volunteer_export(job_id):
        """
        Download CSV export file for a completed background job.

        Returns: CSV file as attachment
        Status codes:
          - 200: File download
          - 401: Unauthorized
          - 404: Job not found or file not ready
        """
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT result_path, status
                FROM background_jobs
                WHERE id = ? AND nonprofit_ein = ?
            ''', (job_id, nonprofit_ein))

            job = cursor.fetchone()
            conn.close()

            if not job or not job[0] or job[1] != 'complete':
                return jsonify({'error': 'Export not ready or not found'}), 404

            result_path = job[0]
            if not os.path.exists(result_path):
                return jsonify({'error': 'Export file not found'}), 404

            return send_file(
                result_path,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'volunteer_hours_{nonprofit_ein}_{job_id[:8]}.csv'
            )
        except Exception as e:
            return jsonify({'error': f'Failed to download export: {str(e)}'}), 500

    @app.route('/api/nonprofit/volunteer-hours/summary', methods=['GET'])
    def get_volunteer_hours_summary():
        """
        Get volunteer hours summary: total hours, trend, top volunteers.

        Query params:
          - period: 'month' (default) | 'all'

        Returns:
        {
          "total_hours_period": 120,
          "total_hours_previous_period": 100,
          "trend_direction": "up",
          "trend_percent": 20,
          "top_volunteers": [
            {"name": "Alice", "hours": 40},
            ...
          ],
          "approved_count": 45,
          "pending_count": 8,
          "rejected_count": 2
        }
        """
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        period = request.args.get('period', 'month')

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get counts by status
            cursor.execute('''
                SELECT status, COUNT(*) FROM volunteer_hours
                WHERE nonprofit_ein = ?
                GROUP BY status
            ''', (nonprofit_ein,))
            status_counts = dict(cursor.fetchall())

            if period == 'all':
                # All-time hours
                cursor.execute('''
                    SELECT COALESCE(SUM(hours), 0) FROM volunteer_hours
                    WHERE nonprofit_ein = ? AND status = 'verified'
                ''', (nonprofit_ein,))
                total_hours = cursor.fetchone()[0]
                total_hours_previous = 0
                trend_percent = 0
            else:
                # This month vs previous month
                today = datetime.now()
                month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                prev_month_end = month_start - timedelta(days=1)
                prev_month_start = prev_month_end.replace(day=1)

                cursor.execute('''
                    SELECT COALESCE(SUM(hours), 0) FROM volunteer_hours
                    WHERE nonprofit_ein = ? AND status = 'verified'
                      AND service_date >= ? AND service_date < ?
                ''', (nonprofit_ein, month_start.isoformat()[:10], today.isoformat()[:10]))
                total_hours = cursor.fetchone()[0]

                cursor.execute('''
                    SELECT COALESCE(SUM(hours), 0) FROM volunteer_hours
                    WHERE nonprofit_ein = ? AND status = 'verified'
                      AND service_date >= ? AND service_date <= ?
                ''', (nonprofit_ein, prev_month_start.isoformat()[:10], prev_month_end.isoformat()[:10]))
                total_hours_previous = cursor.fetchone()[0]

                if total_hours_previous > 0:
                    trend_percent = round((total_hours - total_hours_previous) / total_hours_previous * 100, 1)
                else:
                    trend_percent = 100 if total_hours > 0 else 0

            # Determine trend direction
            if trend_percent > 5:
                trend_direction = 'up'
            elif trend_percent < -5:
                trend_direction = 'down'
            else:
                trend_direction = 'flat'

            # Top 3 volunteers
            cursor.execute('''
                SELECT volunteer_name, SUM(hours) as total_hours
                FROM volunteer_hours
                WHERE nonprofit_ein = ? AND status = 'verified'
                GROUP BY volunteer_name
                ORDER BY total_hours DESC
                LIMIT 3
            ''', (nonprofit_ein,))
            top_volunteers = [
                {'name': row[0], 'hours': row[1]}
                for row in cursor.fetchall()
            ]

            conn.close()

            return jsonify({
                'total_hours_period': total_hours,
                'total_hours_previous_period': total_hours_previous,
                'trend_direction': trend_direction,
                'trend_percent': trend_percent,
                'top_volunteers': top_volunteers,
                'approved_count': status_counts.get('verified', 0),
                'pending_count': status_counts.get('pending', 0),
                'rejected_count': status_counts.get('rejected', 0),
            }), 200
        except Exception as e:
            return jsonify({'error': f'Failed to get summary: {str(e)}'}), 500

    @app.route('/api/nonprofit/donor-templates', methods=['GET'])
    def get_donor_templates():
        """
        Get donor thank-you templates (defaults + custom).

        Returns: { templates: [ { id, template_name, template_body, is_default, sample_preview }, ... ] }
        """
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get org name for sample preview
            cursor.execute('SELECT name FROM nonprofit_accounts WHERE ein = ?', (nonprofit_ein,))
            org = cursor.fetchone()
            org_name = org[0] if org else 'Your Organization'

            # Get custom templates
            cursor.execute('''
                SELECT id, template_name, template_body, is_default, created_at, updated_at
                FROM donor_templates
                WHERE nonprofit_ein = ?
                ORDER BY is_default DESC, created_at ASC
            ''', (nonprofit_ein,))
            custom_templates = cursor.fetchall()
            conn.close()

            # Build template list with sample previews
            templates = []

            # Add custom templates first
            for row in custom_templates:
                preview = _substitute_template_vars(
                    row[2],
                    donor_name='Jane Donor',
                    amount='$250.00',
                    date=datetime.now().strftime('%Y-%m-%d'),
                    org_name=org_name
                )
                templates.append({
                    'id': row[0],
                    'template_name': row[1],
                    'template_body': row[2],
                    'is_default': bool(row[3]),
                    'sample_preview': preview,
                    'created_at': row[4],
                    'updated_at': row[5],
                })

            # Add hardcoded defaults (if not already present)
            default_names = [t['template_name'] for t in templates if t['is_default']]
            defaults = [
                {
                    'id': 'default_simple',
                    'template_name': 'Simple Thank You',
                    'template_body': 'Dear {donor_name}, Thank you for your generous {amount} gift. Your support makes a real difference to {org_name}. With gratitude, {org_name}',
                    'is_default': True,
                },
                {
                    'id': 'default_tax',
                    'template_name': 'Tax Deduction Emphasis',
                    'template_body': 'Dear {donor_name}, Thank you for your contribution of {amount} received on {date}. This donation is fully tax-deductible. {org_name} is a 501(c)(3) nonprofit and will send you additional documentation for your records.',
                    'is_default': True,
                },
                {
                    'id': 'default_impact',
                    'template_name': 'Mission Impact Focus',
                    'template_body': 'Dear {donor_name}, Your {amount} gift to {org_name} enables us to continue our mission. Thanks to supporters like you, we can [describe your impact]. We\'re grateful for your partnership.',
                    'is_default': True,
                },
                {
                    'id': 'default_sustaining',
                    'template_name': 'Sustaining Supporter',
                    'template_body': 'Dear {donor_name}, We\'re honored by your ongoing support. Your {amount} contribution on {date} strengthens {org_name}\'s ability to serve our community. Thank you for being a sustaining partner.',
                    'is_default': True,
                },
                {
                    'id': 'default_corporate',
                    'template_name': 'Corporate Giving',
                    'template_body': 'Dear {donor_name}, {org_name} appreciates your company\'s {amount} donation. Together, we\'re building a stronger community. We\'d welcome the opportunity to discuss partnership opportunities.',
                    'is_default': True,
                },
            ]

            for default_template in defaults:
                if default_template['template_name'] not in default_names:
                    preview = _substitute_template_vars(
                        default_template['template_body'],
                        donor_name='Jane Donor',
                        amount='$250.00',
                        date=datetime.now().strftime('%Y-%m-%d'),
                        org_name=org_name
                    )
                    templates.append({
                        **default_template,
                        'sample_preview': preview,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat(),
                    })

            return jsonify({'templates': templates}), 200
        except Exception as e:
            return jsonify({'error': f'Failed to get templates: {str(e)}'}), 500

    @app.route('/api/nonprofit/donor-templates', methods=['POST'])
    def create_donor_template():
        """
        Create a new custom donor template.

        Input: { template_name: string, template_body: string }
        Returns: { id, template_name, template_body, is_default: false, created_at }

        Validation:
          - template_name not empty, not duplicate
          - template_body contains >= 1 of: {donor_name}, {amount}, {date}, {org_name}
        """
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.json or {}
        template_name = data.get('template_name', '').strip()
        template_body = data.get('template_body', '').strip()

        if not template_name:
            return jsonify({'error': 'template_name required'}), 400
        if not template_body:
            return jsonify({'error': 'template_body required'}), 400

        # Validate that template has at least one variable
        required_vars = ['{donor_name}', '{amount}', '{date}', '{org_name}']
        if not any(var in template_body for var in required_vars):
            return jsonify({
                'error': 'template_body must contain at least one of: {donor_name}, {amount}, {date}, {org_name}'
            }), 400

        try:
            template_id = str(uuid.uuid4())
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO donor_templates (id, nonprofit_ein, template_name, template_body, is_default)
                VALUES (?, ?, ?, ?, 0)
            ''', (template_id, nonprofit_ein, template_name, template_body))

            conn.commit()
            conn.close()

            return jsonify({
                'id': template_id,
                'template_name': template_name,
                'template_body': template_body,
                'is_default': False,
                'created_at': datetime.now().isoformat(),
            }), 201
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Template name already exists for this organization'}), 409
        except Exception as e:
            return jsonify({'error': f'Failed to create template: {str(e)}'}), 500

    @app.route('/api/nonprofit/donor-templates/<template_id>', methods=['PUT'])
    def update_donor_template(template_id):
        """
        Update a custom donor template.

        Input: { template_name?: string, template_body?: string }
        Returns: Updated template object

        Cannot update default templates (is_default=1).
        """
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        # Skip validation for default templates (they're read-only)
        if template_id.startswith('default_'):
            return jsonify({'error': 'Cannot modify default templates'}), 403

        data = request.json or {}
        template_name = data.get('template_name', '').strip() if 'template_name' in data else None
        template_body = data.get('template_body', '').strip() if 'template_body' in data else None

        if template_name == '':
            return jsonify({'error': 'template_name cannot be empty'}), 400
        if template_body == '':
            return jsonify({'error': 'template_body cannot be empty'}), 400

        # Validate template vars if body is provided
        if template_body:
            required_vars = ['{donor_name}', '{amount}', '{date}', '{org_name}']
            if not any(var in template_body for var in required_vars):
                return jsonify({
                    'error': 'template_body must contain at least one of: {donor_name}, {amount}, {date}, {org_name}'
                }), 400

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Verify ownership
            cursor.execute(
                'SELECT id FROM donor_templates WHERE id = ? AND nonprofit_ein = ?',
                (template_id, nonprofit_ein)
            )
            if not cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Template not found'}), 404

            # Build update
            updates = []
            params = []
            if template_name:
                updates.append('template_name = ?')
                params.append(template_name)
            if template_body:
                updates.append('template_body = ?')
                params.append(template_body)

            if not updates:
                conn.close()
                return jsonify({'error': 'No fields to update'}), 400

            updates.append('updated_at = ?')
            params.append(datetime.now().isoformat())
            params.append(template_id)
            params.append(nonprofit_ein)

            cursor.execute(
                f'UPDATE donor_templates SET {", ".join(updates)} WHERE id = ? AND nonprofit_ein = ?',
                params
            )
            conn.commit()

            # Fetch updated template
            cursor.execute(
                'SELECT id, template_name, template_body, is_default, created_at, updated_at FROM donor_templates WHERE id = ?',
                (template_id,)
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                return jsonify({
                    'id': row[0],
                    'template_name': row[1],
                    'template_body': row[2],
                    'is_default': bool(row[3]),
                    'created_at': row[4],
                    'updated_at': row[5],
                }), 200
            else:
                return jsonify({'error': 'Failed to update template'}), 500
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Template name already exists for this organization'}), 409
        except Exception as e:
            return jsonify({'error': f'Failed to update template: {str(e)}'}), 500

    @app.route('/api/nonprofit/donor-templates/<template_id>', methods=['DELETE'])
    def delete_donor_template(template_id):
        """Delete a custom donor template."""
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        # Cannot delete default templates
        if template_id.startswith('default_'):
            return jsonify({'error': 'Cannot delete default templates'}), 403

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute(
                'DELETE FROM donor_templates WHERE id = ? AND nonprofit_ein = ?',
                (template_id, nonprofit_ein)
            )
            conn.commit()
            affected = cursor.rowcount
            conn.close()

            if affected == 0:
                return jsonify({'error': 'Template not found'}), 404

            return jsonify({'status': 'deleted'}), 200
        except Exception as e:
            return jsonify({'error': f'Failed to delete template: {str(e)}'}), 500


def _generate_volunteer_csv_async(job_id, nonprofit_ein):
    """Background job: Generate volunteer hours CSV asynchronously."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Mark job as processing
        cursor.execute(
            'UPDATE background_jobs SET status = ?, started_at = ? WHERE id = ?',
            ('processing', datetime.now().isoformat(), job_id)
        )
        conn.commit()

        # Query volunteer hours (approved only)
        cursor.execute('''
            SELECT volunteer_name, volunteer_email, hours, service_date, activity_description, status, approved_at
            FROM volunteer_hours
            WHERE nonprofit_ein = ? AND status = 'verified'
            ORDER BY service_date DESC
        ''', (nonprofit_ein,))

        rows = cursor.fetchall()
        conn.close()

        # Create export directory if needed
        export_dir = '/tmp/daanaa_exports'
        os.makedirs(export_dir, exist_ok=True)

        # Write CSV file
        csv_path = os.path.join(export_dir, f'{job_id}.csv')
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Volunteer Name',
                'Email',
                'Hours',
                'Service Date',
                'Activity',
                'Status',
                'Approved Date'
            ])
            for row in rows:
                writer.writerow([
                    row[0],  # volunteer_name
                    row[1],  # volunteer_email
                    row[2],  # hours
                    row[3],  # service_date
                    row[4],  # activity_description
                    row[5],  # status
                    row[6] or '',  # approved_at
                ])

        # Update job status
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE background_jobs
            SET status = ?, completed_at = ?, result_path = ?
            WHERE id = ?
        ''', ('complete', datetime.now().isoformat(), csv_path, job_id))
        conn.commit()
        conn.close()
    except Exception as e:
        # Mark job as failed
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE background_jobs
            SET status = ?, error_message = ?, completed_at = ?
            WHERE id = ?
        ''', ('failed', str(e), datetime.now().isoformat(), job_id))
        conn.commit()
        conn.close()


# Register Phase 3 endpoints (called separately in register_nonprofit_endpoints)
# This keeps the main function readable and allows Phase 3 to be toggled independently


def _substitute_template_vars(template, donor_name, amount, date, org_name):
    """Substitute template variables with actual values."""
    result = template
    result = result.replace('{donor_name}', donor_name)
    result = result.replace('{amount}', amount)
    result = result.replace('{date}', date)
    result = result.replace('{org_name}', org_name)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3: Letter Credit Purchasing + Donor Message Tracking + Impact Dashboard
# ─────────────────────────────────────────────────────────────────────────────

def _generate_tracking_pixel(message_id: str) -> tuple:
    """Generate unique tracking pixel ID and encrypted token.

    Returns: (pixel_id, encrypted_token) for use in pixel URL
    """
    pixel_id = f"px_{uuid.uuid4().hex[:12]}"
    # Token: encrypt message_id so we can verify without DB lookup initially
    token = hmac.new(
        os.environ.get("PIXEL_SECRET_KEY", "default_secret").encode(),
        message_id.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    return pixel_id, token


def _verify_stripe_webhook_signature(body: bytes, signature: str) -> bool:
    """Verify Stripe webhook signature."""
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        return False

    timestamp, signed_content = signature.split(',') if ',' in signature else ('', '')
    expected_sig = hmac.new(
        secret.encode(),
        f"{timestamp}.{body.decode()}".encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signed_content.replace('v1=', ''), expected_sig)


def register_phase3_endpoints(app):
    """Register Phase 3 endpoints: letter credits, donor tracking, impact metrics."""

    # ─────────────────────────────────────────────────────────────────────────
    # Letter Credit Purchasing
    # ─────────────────────────────────────────────────────────────────────────

    @app.route('/api/nonprofit/letter-credits/purchase', methods=['POST'])
    def purchase_letter_credits():
        """Purchase letter credits via Stripe payment.

        POST /api/nonprofit/letter-credits/purchase
        Headers: Authorization: Bearer {nonprofit_ein}
        Body: {
            "stripe_payment_method_id": "pm_123...",
            "idempotency_key": "uuid-123",
            "quantity": 1
        }

        Returns 202 Accepted with purchase_id (payment is async)
        """
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.json or {}
        payment_method_id = data.get('stripe_payment_method_id', '').strip()
        idempotency_key = data.get('idempotency_key', '').strip()
        quantity = data.get('quantity', 1)

        # Validation
        if not payment_method_id or not idempotency_key:
            return jsonify({'error': 'stripe_payment_method_id and idempotency_key required'}), 400

        if not payment_method_id.startswith('pm_'):
            return jsonify({'error': 'Invalid payment method ID format'}), 400

        if quantity < 1 or quantity > 1000:
            return jsonify({'error': 'Quantity must be between 1 and 1000'}), 400

        # Check Stripe API key
        stripe_api_key = os.environ.get('STRIPE_API_KEY', '')
        if not stripe_api_key:
            return jsonify({'error': 'Payment processing not configured'}), 503

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Check if idempotency key already used (prevent double-charge)
            cursor.execute('''
                SELECT id, status FROM letter_credit_purchases
                WHERE idempotency_key = ? AND nonprofit_ein = ?
            ''', (idempotency_key, nonprofit_ein))
            existing = cursor.fetchone()

            if existing:
                conn.close()
                return jsonify({
                    'purchase_id': existing[0],
                    'status': existing[1],
                    'message': 'This purchase was already processed'
                }), 200

            # Create purchase record (status=pending, will be updated by webhook)
            purchase_id = f"lcpurch_{uuid.uuid4().hex[:12]}"
            amount_cents = quantity * 1000  # $10 per pack

            cursor.execute('''
                INSERT INTO letter_credit_purchases
                (id, nonprofit_ein, amount_cents, letters_acquired, status,
                 payment_method_type, idempotency_key, created_at)
                VALUES (?, ?, ?, ?, 'pending', 'card', ?, ?)
            ''', (purchase_id, nonprofit_ein, amount_cents, quantity * 100,
                  idempotency_key, datetime.now().isoformat()))

            conn.commit()
            conn.close()

            # TODO: Call Stripe API.PaymentIntent.create() here with payment_method_id
            # For now, return 202 Accepted — Stripe integration is optional

            return jsonify({
                'purchase_id': purchase_id,
                'status': 'pending',
                'stripe_intent_id': None,  # Would be populated after Stripe call
                'created_at': datetime.now().isoformat(),
                'message': 'Purchase pending. Confirmation will be sent via webhook.',
            }), 202

        except sqlite3.IntegrityError:
            return jsonify({'error': 'Duplicate idempotency key'}), 409
        except Exception as e:
            return jsonify({'error': f'Purchase failed: {str(e)}'}), 500


    @app.route('/api/nonprofit/letter-credits/balance', methods=['GET'])
    def get_letter_credits_balance():
        """Get current letter credits balance and usage metrics.

        GET /api/nonprofit/letter-credits/balance
        Headers: Authorization: Bearer {nonprofit_ein}

        Returns: {
            "nonprofit_ein": "12-3456789",
            "letters_remaining": 350,
            "lifetime_purchases": 5,
            "lifetime_spend_cents": 50000,
            "last_purchase": {...},
            "next_renewal_date": null
        }
        """
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get remaining letters
            cursor.execute('''
                SELECT COALESCE(SUM(letters_remaining), 0)
                FROM letter_credits
                WHERE nonprofit_ein = ?
            ''', (nonprofit_ein,))
            letters_remaining = cursor.fetchone()[0]

            # Get lifetime purchase stats
            cursor.execute('''
                SELECT COUNT(*), COALESCE(SUM(amount_cents), 0)
                FROM letter_credit_purchases
                WHERE nonprofit_ein = ? AND status = 'succeeded'
            ''', (nonprofit_ein,))
            lifetime_purchases, lifetime_spend = cursor.fetchone()

            # Get last purchase
            cursor.execute('''
                SELECT id, letters_acquired, completed_at
                FROM letter_credit_purchases
                WHERE nonprofit_ein = ? AND status = 'succeeded'
                ORDER BY completed_at DESC
                LIMIT 1
            ''', (nonprofit_ein,))
            last_purchase_row = cursor.fetchone()

            conn.close()

            last_purchase = None
            if last_purchase_row:
                last_purchase = {
                    'purchase_id': last_purchase_row[0],
                    'letters_acquired': last_purchase_row[1],
                    'completed_at': last_purchase_row[2],
                }

            return jsonify({
                'nonprofit_ein': nonprofit_ein,
                'letters_remaining': int(letters_remaining),
                'lifetime_purchases': int(lifetime_purchases),
                'lifetime_spend_cents': int(lifetime_spend),
                'last_purchase': last_purchase,
                'next_renewal_date': None,
            }), 200

        except Exception as e:
            return jsonify({'error': f'Failed to get balance: {str(e)}'}), 500


    @app.route('/api/webhook/stripe', methods=['POST'])
    def stripe_webhook():
        """Handle Stripe webhook events (payment.success, payment.failed, etc).

        POST /api/webhook/stripe
        Headers: stripe-signature: t=...,v1=...
        Body: Stripe event JSON

        On payment_intent.succeeded:
          - Update letter_credit_purchases status to 'succeeded'
          - INSERT new row in letter_credits with letters_remaining
          - Send confirmation email
        """
        try:
            sig_header = request.headers.get('stripe-signature', '')
            body = request.get_data()

            # Verify signature if secret is configured
            stripe_webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
            if stripe_webhook_secret and not _verify_stripe_webhook_signature(body, sig_header):
                return jsonify({'error': 'Invalid signature'}), 401

            event = request.json or {}
            event_type = event.get('type', '')
            event_data = event.get('data', {}).get('object', {})

            # Only process payment_intent.succeeded
            if event_type != 'payment_intent.succeeded':
                return jsonify({'status': 'ignored'}), 200

            stripe_intent_id = event_data.get('id')
            metadata = event_data.get('metadata', {})
            nonprofit_ein = metadata.get('nonprofit_ein')
            purchase_id = metadata.get('purchase_id')

            if not nonprofit_ein or not purchase_id:
                return jsonify({'error': 'Missing metadata'}), 400

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get purchase details
            cursor.execute('''
                SELECT letters_acquired, amount_cents
                FROM letter_credit_purchases
                WHERE id = ? AND nonprofit_ein = ?
            ''', (purchase_id, nonprofit_ein))
            purchase = cursor.fetchone()

            if not purchase:
                conn.close()
                return jsonify({'error': 'Purchase not found'}), 404

            letters_acquired, amount_cents = purchase

            # Update purchase status to succeeded
            cursor.execute('''
                UPDATE letter_credit_purchases
                SET status = 'succeeded',
                    stripe_payment_intent_id = ?,
                    completed_at = ?,
                    webhook_received_at = ?
                WHERE id = ? AND nonprofit_ein = ?
            ''', (stripe_intent_id, datetime.now().isoformat(),
                  datetime.now().isoformat(), purchase_id, nonprofit_ein))

            # Add letter credits
            credit_id = f"lc_{uuid.uuid4().hex[:12]}"
            expires_at = (datetime.now() + timedelta(days=365)).isoformat()
            cursor.execute('''
                INSERT INTO letter_credits
                (id, nonprofit_ein, letters_remaining, purchased_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (credit_id, nonprofit_ein, letters_acquired,
                  datetime.now().isoformat(), expires_at))

            conn.commit()

            # Get nonprofit details for email
            cursor.execute('''
                SELECT email, name FROM nonprofit_accounts
                WHERE ein = ?
            ''', (nonprofit_ein,))
            nonprofit_row = cursor.fetchone()
            conn.close()

            # Send confirmation email
            if nonprofit_row and get_email_service:
                try:
                    email_addr, org_name = nonprofit_row
                    email_service = get_email_service()
                    email_service.send(
                        to_email=email_addr,
                        subject=f"Letter Credits Purchased: {letters_acquired} letters",
                        plain_text=f"Thank you! Your {letters_acquired} letter credits have been activated and are ready to use.",
                        html=f"<p>Thank you! Your <strong>{letters_acquired} letter credits</strong> have been activated and are ready to use.</p>"
                    )
                except Exception:
                    pass  # Don't fail webhook if email fails

            return jsonify({'status': 'success'}), 200

        except Exception as e:
            return jsonify({'error': f'Webhook processing failed: {str(e)}'}), 500


    # ─────────────────────────────────────────────────────────────────────────
    # Donor Message Tracking
    # ─────────────────────────────────────────────────────────────────────────

    @app.route('/api/nonprofit/donor-messages/send', methods=['POST'])
    def send_donor_message():
        """Send a donor thank-you message with tracking pixel.

        POST /api/nonprofit/donor-messages/send
        Headers: Authorization: Bearer {nonprofit_ein}
        Body: {
            "donor_email": "john@example.com",
            "donor_name": "John Donor",
            "message_subject": "Thank You!",
            "message_body": "Your $500 gift...",
            "template_id": "default_simple",  // Optional
            "track_opens": true
        }

        Returns 201: {
            "message_id": "msg_123",
            "status": "queued",
            "tracking_pixel_url": "https://daanaa.org/pixel/px_456?token=abc123"
        }
        """
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.json or {}
        donor_email = data.get('donor_email', '').strip()
        donor_name = data.get('donor_name', '').strip()
        subject = data.get('message_subject', '').strip()
        body = data.get('message_body', '').strip()
        template_id = data.get('template_id', '').strip()
        track_opens = data.get('track_opens', True)

        # Validation
        if not donor_email or '@' not in donor_email:
            return jsonify({'error': 'Invalid donor email'}), 400
        if not subject:
            return jsonify({'error': 'message_subject required'}), 400
        if not body:
            return jsonify({'error': 'message_body required'}), 400

        try:
            message_id = f"msg_{uuid.uuid4().hex[:12]}"

            # Generate tracking pixel
            pixel_id, token = _generate_tracking_pixel(message_id)
            pixel_url = f"https://daanaa.org/api/nonprofit/pixel/{pixel_id}?token={token}"

            # Inject pixel into message body (if tracking enabled)
            if track_opens:
                body_with_pixel = f"{body}\n\n<img src='{pixel_url}' alt='' width='1' height='1' style='display:none;' />"
            else:
                body_with_pixel = body
                pixel_id = None
                pixel_url = None

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO donor_messages
                (id, nonprofit_ein, donor_email, donor_name, message_subject,
                 message_body, template_id, tracking_pixel_id, tracking_pixel_url,
                 delivery_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?)
            ''', (message_id, nonprofit_ein, donor_email, donor_name, subject,
                  body, template_id or None, pixel_id, pixel_url or None,
                  datetime.now().isoformat(), datetime.now().isoformat()))

            conn.commit()
            conn.close()

            # TODO: Queue email delivery via email_service in background thread

            return jsonify({
                'message_id': message_id,
                'status': 'queued',
                'tracking_pixel_url': pixel_url,
                'created_at': datetime.now().isoformat(),
            }), 201

        except Exception as e:
            return jsonify({'error': f'Failed to send message: {str(e)}'}), 500


    @app.route('/api/nonprofit/donor-messages', methods=['GET'])
    def list_donor_messages():
        """List sent donor messages with engagement metrics.

        GET /api/nonprofit/donor-messages?status=sent&limit=50&offset=0
        Headers: Authorization: Bearer {nonprofit_ein}

        Query params:
          - status: draft|queued|sent|failed (default: all)
          - limit: 50 (max)
          - offset: 0

        Returns: {
            "messages": [
                {
                    "id": "msg_123",
                    "donor_email": "john@example.com",
                    "donor_name": "John Donor",
                    "message_subject": "Thank You!",
                    "status": "sent",
                    "sent_at": "2026-06-21T10:05:00Z",
                    "open_count": 3,
                    "link_clicks": 1,
                    "first_opened_at": "2026-06-21T10:30:00Z"
                }
            ],
            "total": 45,
            "limit": 50,
            "offset": 0
        }
        """
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        status_filter = request.args.get('status', 'all')
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))

        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Build query
            if status_filter == 'all':
                cursor.execute('''
                    SELECT id, donor_email, donor_name, message_subject, delivery_status,
                           sent_at, open_count, link_clicks, first_opened_at
                    FROM donor_messages
                    WHERE nonprofit_ein = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (nonprofit_ein, limit, offset))
            else:
                cursor.execute('''
                    SELECT id, donor_email, donor_name, message_subject, delivery_status,
                           sent_at, open_count, link_clicks, first_opened_at
                    FROM donor_messages
                    WHERE nonprofit_ein = ? AND delivery_status = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (nonprofit_ein, status_filter, limit, offset))

            messages = [dict(row) for row in cursor.fetchall()]

            # Get total count
            if status_filter == 'all':
                cursor.execute('SELECT COUNT(*) FROM donor_messages WHERE nonprofit_ein = ?',
                             (nonprofit_ein,))
            else:
                cursor.execute('''
                    SELECT COUNT(*) FROM donor_messages
                    WHERE nonprofit_ein = ? AND delivery_status = ?
                ''', (nonprofit_ein, status_filter))

            total = cursor.fetchone()[0]
            conn.close()

            return jsonify({
                'messages': messages,
                'total': total,
                'limit': limit,
                'offset': offset,
            }), 200

        except Exception as e:
            return jsonify({'error': f'Failed to list messages: {str(e)}'}), 500


    @app.route('/api/nonprofit/donor-messages/<message_id>/events', methods=['GET'])
    def get_message_events(message_id):
        """Get tracking events for a specific message.

        GET /api/nonprofit/donor-messages/{message_id}/events
        Headers: Authorization: Bearer {nonprofit_ein}

        Returns: {
            "message_id": "msg_123",
            "total_opens": 3,
            "unique_opens": 2,
            "link_clicks": 1,
            "events": [
                {
                    "event_id": "evt_123",
                    "event_type": "open",
                    "event_timestamp": "2026-06-21T10:30:00Z",
                    "ip_address": "203.0.113.x",
                    "user_agent": "Mozilla/5.0..."
                }
            ]
        }
        """
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Verify message ownership
            cursor.execute('''
                SELECT id FROM donor_messages
                WHERE id = ? AND nonprofit_ein = ?
            ''', (message_id, nonprofit_ein))

            if not cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Message not found'}), 404

            # Get events
            cursor.execute('''
                SELECT id, event_type, event_timestamp, ip_address, user_agent
                FROM donor_message_events
                WHERE message_id = ?
                ORDER BY event_timestamp ASC
            ''', (message_id,))

            events = []
            for row in cursor.fetchall():
                events.append({
                    'event_id': row[0],
                    'event_type': row[1],
                    'event_timestamp': row[2],
                    'ip_address': row[3][:10] + 'x' if row[3] else None,  # Redact IP
                    'user_agent': row[4],
                })

            # Count event types
            cursor.execute('''
                SELECT event_type, COUNT(*) FROM donor_message_events
                WHERE message_id = ?
                GROUP BY event_type
            ''', (message_id,))

            event_counts = dict(cursor.fetchall())
            conn.close()

            return jsonify({
                'message_id': message_id,
                'total_opens': event_counts.get('open', 0),
                'unique_opens': len({e['ip_address'] for e in events if e['event_type'] == 'open'}),
                'link_clicks': event_counts.get('link_click', 0),
                'events': events,
            }), 200

        except Exception as e:
            return jsonify({'error': f'Failed to get events: {str(e)}'}), 500


    @app.route('/api/nonprofit/pixel/<pixel_id>', methods=['GET'])
    def track_pixel_open(pixel_id):
        """Track pixel opens (called when email is opened).

        GET /api/nonprofit/pixel/{pixel_id}?token={token}

        Returns: 1x1 transparent GIF (no JavaScript, no redirects)
        """
        try:
            token = request.args.get('token', '')

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Look up message by pixel ID
            cursor.execute('''
                SELECT id FROM donor_messages
                WHERE tracking_pixel_id = ?
            ''', (pixel_id,))

            message_row = cursor.fetchone()
            if not message_row:
                conn.close()
                # Return valid GIF even if pixel not found (don't leak info)
                return _get_tracking_gif()

            message_id = message_row[0]

            # Log open event (in background, don't block response)
            def log_event():
                try:
                    db = sqlite3.connect(DB_PATH)
                    dc = db.cursor()

                    event_id = f"evt_{uuid.uuid4().hex[:12]}"
                    ip_addr = request.remote_addr or 'unknown'
                    user_agent = request.headers.get('User-Agent', '')
                    referer = request.headers.get('Referer', '')

                    dc.execute('''
                        INSERT INTO donor_message_events
                        (id, message_id, event_type, event_timestamp, ip_address, user_agent, referer)
                        VALUES (?, ?, 'open', ?, ?, ?, ?)
                    ''', (event_id, message_id, datetime.now().isoformat(), ip_addr, user_agent, referer))

                    # Update message counters
                    dc.execute('''
                        UPDATE donor_messages
                        SET open_count = open_count + 1,
                            first_opened_at = CASE WHEN first_opened_at IS NULL
                                                THEN ? ELSE first_opened_at END
                        WHERE id = ?
                    ''', (datetime.now().isoformat(), message_id))

                    db.commit()
                    db.close()
                except Exception:
                    pass

            thread = threading.Thread(target=log_event)
            thread.daemon = True
            thread.start()

            conn.close()
            return _get_tracking_gif()

        except Exception:
            # Always return GIF, never error (transparent tracking)
            return _get_tracking_gif()


    # ─────────────────────────────────────────────────────────────────────────
    # ED Impact Dashboard
    # ─────────────────────────────────────────────────────────────────────────

    @app.route('/api/nonprofit/dashboard/impact', methods=['GET'])
    def get_impact_metrics():
        """Disabled: requires verified nonprofit auth, not yet implemented."""
        return jsonify({
            'error': 'Impact metrics require verified account authorization. '
                     'EIN-only access is not supported.'
        }), 401

        period = request.args.get('period', 'last_30_days')

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get time filter
            if period == 'last_30_days':
                days_back = 30
            elif period == 'last_7_days':
                days_back = 7
            elif period == 'all':
                days_back = 36500  # ~100 years
            else:
                days_back = 30

            since_date = (datetime.now() - timedelta(days=days_back)).isoformat()[:10]

            # Credit Utilization
            cursor.execute('''
                SELECT COALESCE(SUM(letters_acquired), 0)
                FROM letter_credit_purchases
                WHERE nonprofit_ein = ? AND status = 'succeeded' AND created_at >= ?
            ''', (nonprofit_ein, since_date))
            letters_purchased = cursor.fetchone()[0]

            cursor.execute('''
                SELECT COALESCE(SUM(hours), 0)
                FROM nonprofit_letter_requests
                WHERE nonprofit_ein = ? AND status = 'generated' AND created_at >= ?
            ''', (nonprofit_ein, since_date))
            letters_used = cursor.fetchone()[0]

            utilization_percent = int((letters_used / letters_purchased * 100) if letters_purchased > 0 else 0)

            # Donor Engagement
            cursor.execute('''
                SELECT COUNT(*), COALESCE(AVG(open_count), 0), COALESCE(AVG(link_clicks), 0)
                FROM donor_messages
                WHERE nonprofit_ein = ? AND delivery_status = 'sent' AND sent_at >= ?
            ''', (nonprofit_ein, since_date))

            donor_row = cursor.fetchone()
            messages_sent = donor_row[0] if donor_row else 0
            avg_opens = donor_row[1] if donor_row else 0
            avg_clicks = donor_row[2] if donor_row else 0

            avg_open_rate = (avg_opens / messages_sent / 1.0) if messages_sent > 0 else 0
            avg_click_rate = (avg_clicks / messages_sent / 1.0) if messages_sent > 0 else 0

            # Volunteer Impact
            cursor.execute('''
                SELECT COUNT(DISTINCT volunteer_name), COALESCE(SUM(hours), 0)
                FROM volunteer_hours
                WHERE nonprofit_ein = ? AND status = 'verified' AND service_date >= ?
            ''', (nonprofit_ein, since_date))

            vol_row = cursor.fetchone()
            volunteer_count = vol_row[0] if vol_row else 0
            volunteer_hours = vol_row[1] if vol_row else 0

            volunteer_value = volunteer_hours * 28.50  # Standard volunteer rate

            # Revenue Equivalent
            letters_value = letters_used * 10  # $10 per letter credit

            # Forecast (simple: trend from last month)
            prev_since = (datetime.now() - timedelta(days=days_back * 2)).isoformat()[:10]

            cursor.execute('''
                SELECT COALESCE(SUM(letters_acquired), 0)
                FROM letter_credit_purchases
                WHERE nonprofit_ein = ? AND status = 'succeeded' AND created_at >= ? AND created_at < ?
            ''', (nonprofit_ein, prev_since, since_date))
            prev_letters_purchased = cursor.fetchone()[0]

            projected_letters = letters_purchased * 2 if prev_letters_purchased > 0 else letters_purchased

            cursor.execute('''
                SELECT COALESCE(SUM(hours), 0)
                FROM volunteer_hours
                WHERE nonprofit_ein = ? AND status = 'verified' AND service_date >= ? AND service_date < ?
            ''', (nonprofit_ein, prev_since, since_date))
            prev_volunteer_hours = cursor.fetchone()[0]

            projected_hours = volunteer_hours * 2 if prev_volunteer_hours > 0 else volunteer_hours

            conn.close()

            return jsonify({
                'nonprofit_ein': nonprofit_ein,
                'period': period,
                'metrics': {
                    'credit_utilization': {
                        'letters_purchased': int(letters_purchased),
                        'letters_used': int(letters_used),
                        'utilization_percent': utilization_percent,
                        'trend': 'up' if utilization_percent > 50 else 'flat',
                        'monthly_spend': int(letters_purchased * 10 * 100),  # cents
                    },
                    'donor_engagement': {
                        'messages_sent': messages_sent,
                        'avg_open_rate': round(avg_open_rate, 3),
                        'avg_click_rate': round(avg_click_rate, 3),
                        'unique_donors_contacted': messages_sent,  # Approximation
                        'trend': 'up',
                    },
                    'volunteer_impact': {
                        'total_hours_verified': int(volunteer_hours),
                        'volunteer_count': volunteer_count,
                        'avg_hours_per_volunteer': round(volunteer_hours / volunteer_count, 1) if volunteer_count > 0 else 0,
                        'value_at_28_50_per_hour': int(volunteer_value),
                        'trend': 'up',
                    },
                    'revenue_equivalent': {
                        'letters_generated_value': int(letters_value),
                        'volunteer_hours_value': int(volunteer_value),
                        'total_impact_value': int(letters_value + volunteer_value),
                        'trend': 'up',
                    },
                    'forecast': {
                        'projected_letters_next_month': int(projected_letters),
                        'projected_volunteer_hours': int(projected_hours),
                        'confidence_percent': 0.65,
                        'calculated_at': datetime.now().isoformat(),
                    },
                }
            }), 200

        except Exception as e:
            return jsonify({'error': f'Failed to get impact metrics: {str(e)}'}), 500

    # ─────────────────────────────────────────────────────────────────────────
    # Nonprofit Data Transparency & Correction (Claiming Flow)
    # ─────────────────────────────────────────────────────────────────────────

    @app.route('/api/nonprofit/update-data', methods=['POST'])
    def nonprofit_update_data():
        """Accept nonprofit-submitted financial data updates during claiming flow.

        POST /api/nonprofit/update-data
        Body: {
            "claim_token": "xyz123",
            "ein": "12-3456789",
            "updates": {
                "total_revenue": 3100000,
                "total_expenses": 2850000,
                "program_expense_pct": 81,
                "months_of_reserve": 3.2
            },
            "explanation": "2024 was stronger year than FY2024 IRS data"
        }

        Returns: {
            "status": "received",
            "update_id": 1,
            "message": "Your update will be included in tomorrow's scoring run"
        }
        """
        try:
            data = request.get_json()
            claim_token = data.get('claim_token', '').strip()
            ein = ''.join(c for c in (data.get('ein') or '') if c.isdigit())[:10]
            updates = data.get('updates', {})
            explanation = data.get('explanation', '').strip()

            # Validate required fields
            if not claim_token or not ein:
                return jsonify({"error": "Missing claim_token or ein"}), 400

            # Validate that claim exists and is active
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT claim_status, firebase_uid FROM org_claims
                WHERE ein = ? AND claim_status IN ('verified', 'pending')
                LIMIT 1
            ''', (ein,))
            claim_row = cursor.fetchone()

            if not claim_row:
                conn.close()
                return jsonify({"error": "Claim not found or not active"}), 404

            # Validate update values
            revenue = updates.get('total_revenue')
            expenses = updates.get('total_expenses')
            program_pct = updates.get('program_expense_pct')
            months_reserve = updates.get('months_of_reserve')

            errors = []
            if revenue is not None and revenue < 0:
                errors.append("Revenue cannot be negative")
            if expenses is not None and expenses < 0:
                errors.append("Expenses cannot be negative")
            if program_pct is not None:
                if program_pct < 0 or program_pct > 100:
                    errors.append("Program % must be 0-100")
            if months_reserve is not None and months_reserve < 0:
                errors.append("Months of reserve cannot be negative")

            # Revenue should be >= expenses (sanity check)
            if revenue is not None and expenses is not None and revenue < expenses:
                errors.append("Revenue should be greater than or equal to expenses")

            if errors:
                conn.close()
                return jsonify({"errors": errors}), 400

            # Get current financial data for comparison
            cursor.execute('''
                SELECT
                    total_revenue, total_expenses,
                    program_expense_pct, months_of_reserve,
                    latest_tax_year
                FROM registry_enriched
                WHERE EIN = ?
                LIMIT 1
            ''', (ein,))
            irs_row = cursor.fetchone()

            if not irs_row:
                conn.close()
                return jsonify({"error": "Organization not found in registry"}), 404

            irs_revenue, irs_expenses, irs_pct, irs_months, irs_tax_year = irs_row

            # Flag if >50% change in any metric (sanity check)
            sanity_check_failed = 0
            if revenue is not None and irs_revenue and abs(revenue - irs_revenue) / irs_revenue > 0.5:
                sanity_check_failed = 1
            if expenses is not None and irs_expenses and abs(expenses - irs_expenses) / irs_expenses > 0.5:
                sanity_check_failed = 1
            if program_pct is not None and irs_pct and abs(program_pct - irs_pct) > 20:
                sanity_check_failed = 1

            # Store in database
            cursor.execute('''
                INSERT INTO org_nonprofit_updates
                (ein, claim_token, irs_total_revenue, irs_total_expenses,
                 irs_program_expense_pct, irs_months_of_reserve, irs_tax_year,
                 submitted_total_revenue, submitted_total_expenses,
                 submitted_program_expense_pct, submitted_months_of_reserve,
                 submitted_explanation, status, sanity_check_failed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending_review', ?)
            ''', (
                ein, claim_token,
                irs_revenue, irs_expenses, irs_pct, irs_months, irs_tax_year,
                revenue, expenses, program_pct, months_reserve,
                explanation, sanity_check_failed
            ))

            conn.commit()
            update_id = cursor.lastrowid
            conn.close()

            return jsonify({
                "status": "received",
                "update_id": update_id,
                "message": "Your update will be reviewed and included in the next scoring run"
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/nonprofit/update-status/<int:update_id>', methods=['GET'])
    def get_nonprofit_update_status(update_id):
        """Get status of a nonprofit data update submission.

        GET /api/nonprofit/update-status/123?claim_token=xyz

        Returns: {
            "update_id": 123,
            "status": "pending_review|validated|pending_scoring|included_in_run|rejected",
            "submitted_at": "2026-06-24T14:30:00",
            "included_in_run_at": null,
            "result_health_signal": "HEALTHY|STABLE|CAUTION|null"
        }
        """
        try:
            claim_token = request.args.get('claim_token', '').strip()
            if not claim_token:
                return jsonify({"error": "Missing claim_token"}), 400

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, status, submitted_at, included_in_run_at,
                       result_health_signal, result_v5_percentile
                FROM org_nonprofit_updates
                WHERE id = ? AND claim_token = ?
                LIMIT 1
            ''', (update_id, claim_token))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return jsonify({"error": "Update not found"}), 404

            return jsonify({
                "update_id": row[0],
                "status": row[1],
                "submitted_at": row[2],
                "included_in_run_at": row[3],
                "result_health_signal": row[4],
                "result_v5_percentile": row[5]
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


def _get_tracking_gif() -> tuple:
    """Return a 1x1 transparent GIF."""
    gif_bytes = bytes([
        0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00,
        0x80, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x21,
        0xF9, 0x04, 0x01, 0x0A, 0x00, 0x01, 0x00, 0x2C, 0x00, 0x00,
        0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
        0x01, 0x00, 0x3B
    ])
    return gif_bytes, 200, {'Content-Type': 'image/gif', 'Cache-Control': 'no-cache'}
