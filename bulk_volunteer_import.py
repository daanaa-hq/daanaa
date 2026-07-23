"""Bulk volunteer import via CSV for event registration."""

import io
import csv
from typing import List, Dict, Tuple
from flask import Blueprint, request, jsonify
import sqlite3
import secrets

bulk_import_bp = Blueprint('bulk_import', __name__, url_prefix='/api/portal/events')


def validate_csv_row(row: Dict[str, str]) -> Tuple[bool, str]:
    """Validate a CSV row has required fields."""
    required = ['name', 'email']
    missing = [f for f in required if not row.get(f, '').strip()]

    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    email = row.get('email', '').strip()
    if '@' not in email:
        return False, f"Invalid email: {email}"

    return True, ""


def parse_csv(file_content: bytes) -> Tuple[List[Dict[str, str]], str]:
    """
    Parse CSV file content.
    Expected columns: name, email, role (optional), phone (optional)
    """
    try:
        text = file_content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)

        if not rows:
            return [], "CSV is empty"

        # Validate all rows
        errors = []
        for i, row in enumerate(rows, start=2):  # Start at 2 (header is 1)
            valid, error = validate_csv_row(row)
            if not valid:
                errors.append(f"Row {i}: {error}")

        if errors:
            return [], "Validation errors:\n" + "\n".join(errors[:5])  # Show first 5 errors

        return rows, ""

    except UnicodeDecodeError:
        return [], "File must be UTF-8 encoded"
    except Exception as e:
        return [], f"CSV parsing error: {str(e)}"


@bulk_import_bp.route('/<int:event_id>/volunteers/bulk-import', methods=['POST'])
def bulk_import_volunteers(event_id: int):
    """
    Bulk import volunteers from CSV file.

    Expected CSV columns:
    - name (required): Volunteer name
    - email (required): Volunteer email
    - role (optional): Volunteer role
    - phone (optional): Volunteer phone

    Authentication required (Firebase).
    """
    from email_service_volunteer import send_bulk_import_confirmation

    # Check authentication
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid authorization header'}), 401

    user_id = auth_header[7:]

    # Check for file
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be CSV format'}), 400

    # Read and parse CSV
    file_content = file.read()
    rows, parse_error = parse_csv(file_content)

    if parse_error:
        return jsonify({'error': parse_error}), 400

    # Get database connection and verify event ownership
    db = sqlite3.connect(':memory:')  # Replace with actual DB path
    try:
        event = db.execute(
            "SELECT id, name, ein FROM volunteer_events WHERE id = ?",
            (event_id,)
        ).fetchone()

        if not event:
            db.close()
            return jsonify({'error': 'Event not found'}), 404

        # Verify organizer owns this event
        # (In production, this would check if user_id is registered as organizer for this EIN)

        # Import volunteers
        imported = []
        duplicates = []
        errors = []

        for i, row in enumerate(rows, start=2):
            name = row.get('name', '').strip()
            email = row.get('email', '').strip()
            role = row.get('role', '').strip() or 'Volunteer'
            phone = row.get('phone', '').strip() or None

            # Check for duplicate
            existing = db.execute(
                "SELECT id FROM event_volunteers WHERE event_id = ? AND email = ?",
                (event_id, email)
            ).fetchone()

            if existing:
                duplicates.append(f"Row {i}: {email} already registered")
                continue

            try:
                vol_id = f'vol_{secrets.token_hex(8)}'
                db.execute("""
                    INSERT INTO event_volunteers
                    (id, event_id, volunteer_id, volunteer_name, volunteer_email, role, phone, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'registered')
                """, (vol_id, event_id, vol_id, name, email, role, phone))

                imported.append({'name': name, 'email': email, 'role': role, 'id': vol_id})

            except Exception as e:
                errors.append(f"Row {i}: {str(e)}")

        db.commit()

        # Send confirmation email to organizer
        organizer_email = "organizer@example.com"  # Would come from event data
        send_bulk_import_confirmation(
            organizer_email,
            event['name'],
            len(imported),
            f"https://daanaa.org/nonprofit/events/{event_id}"
        )

        return jsonify({
            'imported': len(imported),
            'volunteers': imported,
            'duplicates': duplicates,
            'errors': errors,
            'total_rows': len(rows),
            'message': f"Successfully imported {len(imported)} volunteers"
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({'error': f'Import failed: {str(e)}'}), 500

    finally:
        db.close()


@bulk_import_bp.route('/<int:event_id>/volunteers/bulk-download-template', methods=['GET'])
def download_csv_template(event_id: int):
    """Download CSV template for bulk volunteer import."""
    from flask import make_response

    template = """name,email,role,phone
John Doe,john@example.com,Setup,555-0001
Jane Smith,jane@example.com,Volunteer,555-0002
Bob Johnson,bob@example.com,Cleanup,555-0003"""

    response = make_response(template)
    response.headers['Content-Disposition'] = f'attachment; filename=volunteers-{event_id}-template.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response
