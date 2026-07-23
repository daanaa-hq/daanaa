"""Source grounded event discovery for nonprofit portal users."""

import ipaddress
import re
import socket
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urlparse

from flask import Blueprint, jsonify, request

event_discovery_bp = Blueprint("event_discovery", __name__)


class _PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.text = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        self._in_title = tag.lower() == "title"

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data):
        value = " ".join(data.split())
        if value:
            self.text.append(value)
            if self._in_title:
                self.title += value + " "


def _safe_url(raw):
    parsed = urlparse((raw or "").strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Enter a public http or https event URL")
    host = parsed.hostname.lower().rstrip(".")
    if host in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Private network URLs are not allowed")
    try:
        for item in socket.getaddrinfo(host, None):
            address = ipaddress.ip_address(item[4][0])
            if address.is_private or address.is_loopback or address.is_link_local:
                raise ValueError("Private network URLs are not allowed")
    except socket.gaierror as exc:
        raise ValueError("The event host could not be reached") from exc
    return parsed.geturl()[:1000]


def _extract(url):
    from daanaa_api import _http
    response = _http.get(url, headers={"User-Agent": "DaanaaEventDiscovery/1.0 (+https://daanaa.org)"}, timeout=8, allow_redirects=False)
    if response.status_code >= 400:
        raise ValueError(f"The source page returned HTTP {response.status_code}")
    if len(response.content) > 2_000_000:
        raise ValueError("The source page is too large to process")
    parser = _PageText()
    parser.feed(response.text)
    text = " ".join(parser.text)
    date = None
    for pattern in (r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})", r"\b([A-Z][a-z]+\s+\d{1,2},\s+\d{4})\b"):
        match = re.search(pattern, text)
        if match:
            try:
                date = datetime.strptime(match.group(1), "%B %d, %Y").strftime("%Y-%m-%d")
                break
            except ValueError:
                pass
    if not date:
        raise ValueError("No clear event date was found. Add the date manually.")
    location = re.search(r"\b(Sugar Land|Houston|Austin|Dallas|San Antonio),\s*(Texas|TX)\b", text, re.I)
    return {
        "title": (parser.title.strip() or "Volunteer opportunity from source page")[:200],
        "event_date": date,
        "location": location.group(0) if location else "",
        "description": "AI assisted draft created from the public source page. Volunteer roles and hour verification remain unconfirmed until the nonprofit reviews this listing.",
    }


@event_discovery_bp.route("/api/portal/events/from-url", methods=["POST"])
def portal_event_from_url():
    from daanaa_api import _assert_org_claim, _format_event, get_db, _make_event_short_id, _require_firebase_user
    uid = _require_firebase_user()
    data = request.get_json(silent=True) or {}
    ein = "".join(c for c in str(data.get("ein") or "") if c.isdigit())[:10]
    if not ein:
        return jsonify({"error": "ein required"}), 400
    db = get_db()
    try:
        _assert_org_claim(uid, ein, db)
        source_url = _safe_url(data.get("source_url"))
        extracted = _extract(source_url)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    existing = db.execute("SELECT * FROM volunteer_events WHERE source_url=? AND ein=?", (source_url, ein)).fetchone()
    if existing:
        return jsonify(_format_event(existing)), 200
    location = extracted["location"].split(",") if extracted["location"] else []
    city = (data.get("location_city") or (location[0].strip() if location else ""))[:100] or None
    state = (data.get("location_state") or ("TX" if len(location) > 1 and location[1].strip().lower() in ("texas", "tx") else ""))[:2].upper() or None
    short_id = _make_event_short_id()
    cur = db.execute("""
        INSERT INTO volunteer_events
          (ein, title, description, event_date, location_city, location_state,
           is_virtual, signup_url, status, event_type, short_id, source_url,
           source_checked_at, discovery_status, ai_generated)
        VALUES (?, ?, ?, ?, ?, ?, 0, ?, 'active', 'volunteer', ?, ?, date('now'), 'unconfirmed', 1)
    """, (ein, (data.get("title") or extracted["title"]).strip()[:200], extracted["description"],
           (data.get("event_date") or extracted["event_date"]).strip()[:10], city, state, source_url, short_id, source_url))
    db.commit()
    row = db.execute("SELECT * FROM volunteer_events WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(_format_event(row)), 201


def init_event_discovery(app):
    app.register_blueprint(event_discovery_bp)
