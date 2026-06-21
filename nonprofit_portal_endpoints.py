"""Nonprofit portal endpoints for letter generation, volunteer hours, and donor templates."""

import uuid
import sqlite3
import os
import threading
import csv
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

    @app.route('/api/nonprofit/volunteer-hours', methods=['GET'])
    def get_volunteer_hours():
        """List volunteer hour submissions for ED review."""
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

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
        """Submit volunteer hours for approval."""
        auth = request.headers.get('Authorization', '')
        nonprofit_ein = auth.split(' ')[-1] if auth else None

        if not nonprofit_ein:
            return jsonify({'error': 'Unauthorized'}), 401

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


def _substitute_template_vars(template, donor_name, amount, date, org_name):
    """Substitute template variables with actual values."""
    result = template
    result = result.replace('{donor_name}', donor_name)
    result = result.replace('{amount}', amount)
    result = result.replace('{date}', date)
    result = result.replace('{org_name}', org_name)
    return result
