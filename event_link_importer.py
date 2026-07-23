"""Event link importer — extract event data from public URLs for nonprofit discovery"""

import re
import sqlite3
import json
from datetime import datetime
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse
import hashlib

from flask import Blueprint, request, jsonify
import requests
from bs4 import BeautifulSoup

event_import_bp = Blueprint('event_import', __name__, url_prefix='/api/portal/events')


# URL validation constants
BLOCKED_HOSTS = {
    'localhost', '127.0.0.1', '0.0.0.0',
    '192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.',
    '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.',
    '172.27.', '172.28.', '172.29.', '172.30.', '172.31.',
    '169.254.',  # Link-local
}

ALLOWED_SCHEMES = {'http', 'https'}


def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate that URL is public and safe to fetch.
    Returns (is_valid, error_message)
    """
    if not url:
        return False, "URL is required"

    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"

    # Check scheme
    if parsed.scheme not in ALLOWED_SCHEMES:
        return False, f"URL scheme must be http or https, not {parsed.scheme}"

    # Check hostname
    hostname = parsed.hostname or ''
    if not hostname:
        return False, "URL has no hostname"

    # Block localhost and private IPs
    for blocked in BLOCKED_HOSTS:
        if hostname.startswith(blocked):
            return False, f"Cannot access {hostname} — private or local address"

    # Block IPv6 loopback and link-local
    if hostname.startswith('[') and hostname.endswith(']'):
        ipv6 = hostname[1:-1].lower()
        if ipv6.startswith('::1') or ipv6.startswith('fe80'):
            return False, "Cannot access IPv6 link-local or loopback addresses"

    return True, ""


def extract_event_data(url: str, html: str) -> Dict:
    """
    Extract event information from HTML.
    Returns dict with extracted fields (only facts supported by source).
    """
    soup = BeautifulSoup(html, 'html.parser')
    data = {
        'title': None,
        'date': None,
        'start_time': None,
        'end_time': None,
        'location': None,
        'description': None,
        'registration_url': None,
        'donation_url': None,
        'source_url': url,
        'source_checked_at': datetime.utcnow().isoformat() + 'Z',
        'ai_generated': True,  # Mark as AI-extracted
        'discovery_status': 'unconfirmed',
    }

    # Extract title from <title>, <h1>, or og:title
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        data['title'] = og_title['content'].strip()
    else:
        h1 = soup.find('h1')
        if h1:
            data['title'] = h1.get_text().strip()
        else:
            title_tag = soup.find('title')
            if title_tag:
                data['title'] = title_tag.get_text().strip()

    # Extract date/time from common patterns
    # Look for patterns like "September 21, 2026" or "09/21/2026"
    text = soup.get_text()

    # Common date patterns
    date_patterns = [
        r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
        r'\d{1,2}/\d{1,2}/\d{4}',
        r'\d{4}-\d{2}-\d{2}',
    ]

    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            data['date'] = match.group(0)
            break

    # Extract time patterns (HH:MM AM/PM or HH:MM)
    time_pattern = r'(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)?'
    time_matches = re.findall(time_pattern, text)
    if time_matches:
        data['start_time'] = f"{time_matches[0][0]}:{time_matches[0][1]}"
        if len(time_matches) > 1:
            data['end_time'] = f"{time_matches[1][0]}:{time_matches[1][1]}"

    # Extract location from og:image, address tag, or text patterns
    og_desc = soup.find('meta', property='og:description')
    if og_desc and og_desc.get('content'):
        data['description'] = og_desc['content'].strip()

    # Look for signup/registration links
    for link in soup.find_all('a', href=True):
        href = link.get('href', '').lower()
        text = link.get_text().lower()

        if 'register' in text or 'signup' in text:
            if data['registration_url'] is None:
                data['registration_url'] = link['href']
        elif 'donate' in text or 'support' in text:
            if data['donation_url'] is None:
                data['donation_url'] = link['href']

    # Remove None values
    return {k: v for k, v in data.items() if v is not None}


def fetch_url_with_timeout(url: str, timeout: int = 10) -> Optional[str]:
    """
    Fetch URL with timeout and size limit.
    Returns HTML content or None if fetch failed.
    """
    try:
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={'User-Agent': 'Daanaa EventImporter/1.0'},
            stream=True,
        )

        # Check size before reading (limit to 5MB)
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > 5 * 1024 * 1024:
            return None

        # Read with size limit
        response.raw.read = lambda amt=None: response.raw.read(amt or 8192)
        html = response.text[:1000000]  # Max 1MB of text

        return html if response.status_code == 200 else None
    except Exception:
        return None


@event_import_bp.route('/from-url', methods=['POST'])
def import_event_from_url():
    """
    Import event from public URL.

    Requires:
    - Firebase authentication
    - Active or verified nonprofit claim for the EIN

    Request body:
    {
        "url": "https://example.com/event",
        "ein": "12-3456789"
    }
    """
    # Check authentication
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid authorization header'}), 401

    user_id = auth_header[7:]  # Extract Firebase UID

    # Get request data
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    ein = data.get('ein', '').strip()

    if not url or not ein:
        return jsonify({'error': 'url and ein are required'}), 400

    # Validate URL
    is_valid, error = validate_url(url)
    if not is_valid:
        return jsonify({'error': error}), 400

    # Verify nonprofit claim
    db = sqlite3.connect(':memory:')  # Replace with actual DB path
    try:
        # Check if user has an active claim for this EIN
        claim = db.execute(
            "SELECT id FROM org_claims WHERE ein = ? AND user_id = ? AND status IN ('active', 'verified')",
            (ein, user_id)
        ).fetchone()

        if not claim:
            db.close()
            return jsonify({'error': 'You must have an active claim for this organization'}), 403

        # Check for duplicate imports
        source_hash = hashlib.sha256(f"{ein}:{url}".encode()).hexdigest()
        existing = db.execute(
            "SELECT id FROM volunteer_events WHERE ein = ? AND source_url = ?",
            (ein, url)
        ).fetchone()

        if existing:
            db.close()
            return jsonify({
                'error': 'Event already imported from this URL',
                'event_id': existing[0],
            }), 409

        # Fetch and extract data from URL
        html = fetch_url_with_timeout(url)
        if not html:
            db.close()
            return jsonify({'error': 'Could not fetch or read URL content'}), 422

        extracted = extract_event_data(url, html)

        # Insert into volunteer_events table
        try:
            cursor = db.execute("""
                INSERT INTO volunteer_events (
                    ein,
                    title,
                    description,
                    event_date,
                    start_time,
                    end_time,
                    location_city,
                    status,
                    source_url,
                    source_checked_at,
                    discovery_status,
                    ai_generated,
                    event_type,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, 'unconfirmed', 1, 'volunteer', datetime('now'), datetime('now'))
            """, (
                ein,
                extracted.get('title'),
                extracted.get('description'),
                extracted.get('date'),
                extracted.get('start_time'),
                extracted.get('end_time'),
                extracted.get('location'),
                extracted.get('source_url'),
                extracted.get('source_checked_at'),
            ))

            db.commit()
            event_id = cursor.lastrowid

            return jsonify({
                'id': event_id,
                'ein': ein,
                'title': extracted.get('title'),
                'event_date': extracted.get('date'),
                'source_url': url,
                'discovery_status': 'unconfirmed',
                'ai_generated': True,
                'message': 'Event imported from URL. Please review and confirm before volunteers can register.'
            }), 201

        except Exception as e:
            db.rollback()
            return jsonify({'error': f'Failed to create event: {str(e)}'}), 500

    finally:
        db.close()


def init_event_link_importer(app):
    """Register event link importer blueprint with Flask app"""
    app.register_blueprint(event_import_bp)
