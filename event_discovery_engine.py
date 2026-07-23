"""Local rolling-window event queue builder.

Discovery creates review records only. It does not publish, contact, or open signup.
Enforces robots.txt compliance and rate limiting.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
import time
from datetime import date, timedelta
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen, URLError
from urllib.robotparser import RobotFileParser

WINDOW_START_DAYS = 14
WINDOW_END_DAYS = 60
USER_AGENT = "DaanaaEventDiscovery/1.0 (+https://daanaa.org)"
MAX_BYTES = 2_000_000

# Rate limiting: 2 second delay between requests to same host
REQUEST_DELAY_SECONDS = 2
_last_request_time = {}


class _PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str):
        value = " ".join(data.split())
        if value:
            self.parts.append(value)


def rolling_window(today: date | None = None) -> tuple[str, str]:
    base = today or date.today()
    return ((base + timedelta(days=WINDOW_START_DAYS)).isoformat(),
            (base + timedelta(days=WINDOW_END_DAYS)).isoformat())


def fetch_source(url: str) -> str:
    """Fetch source with robots.txt compliance and rate limiting."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("source URL must be public HTTP(S)")

    hostname = parsed.hostname

    # Check robots.txt compliance
    try:
        robot_parser = RobotFileParser()
        robots_url = f"{parsed.scheme}://{hostname}/robots.txt"
        robot_parser.set_url(robots_url)
        robot_parser.read()

        if not robot_parser.can_fetch(USER_AGENT, url):
            raise ValueError(f"robots.txt disallows fetching {url}")
    except (URLError, Exception) as e:
        # If robots.txt is unavailable, fail closed (don't fetch)
        raise ValueError(f"Cannot verify robots.txt compliance: {e}")

    # Rate limiting: enforce delay between requests to same host
    now = time.time()
    last_time = _last_request_time.get(hostname, 0)
    delay_needed = REQUEST_DELAY_SECONDS - (now - last_time)
    if delay_needed > 0:
        time.sleep(delay_needed)

    # Fetch source
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    try:
        with urlopen(request, timeout=10) as response:
            payload = response.read(MAX_BYTES + 1)
    finally:
        _last_request_time[hostname] = time.time()

    if len(payload) > MAX_BYTES:
        raise ValueError("source exceeds size limit")
    return payload.decode("utf-8", errors="replace")


def extract_candidates(source_url: str, html: str, today: date | None = None) -> list[dict]:
    start, end = rolling_window(today)
    parser = _PageText()
    parser.feed(html)
    text = " ".join(parser.parts)
    candidates = []
    pattern = re.compile(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b")
    for match in pattern.finditer(text):
        try:
            event_date = date(*(int(value) for value in match.groups())).isoformat()
        except ValueError:
            continue
        if not start <= event_date <= end:
            continue
        context = text[max(0, match.start() - 180):match.end() + 180]
        if not re.search(r"\b(event|volunteer|service|cleanup|drive|community)\b", context, re.I):
            continue
        candidates.append({
            "title": context.split(".")[0][:200] or "Source discovered event",
            "event_date": event_date,
            "source_url": source_url,
            "evidence": context[:600],
        })
    return candidates[:25]


def ensure_queue(db: sqlite3.Connection) -> None:
    db.execute("""
        CREATE TABLE IF NOT EXISTS event_discovery_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ein TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_hash TEXT NOT NULL,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            evidence TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending_review',
            last_checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TEXT,
            UNIQUE(ein, source_url, event_date, source_hash)
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_event_queue_review ON event_discovery_queue(status, event_date)")
    db.commit()


def queue_candidates(db: sqlite3.Connection, ein: str, candidates: list[dict]) -> int:
    ensure_queue(db)
    added = 0
    for candidate in candidates:
        digest = hashlib.sha256(candidate["evidence"].encode()).hexdigest()[:16]
        before = db.total_changes
        db.execute(
            "INSERT OR IGNORE INTO event_discovery_queue (ein, source_url, source_hash, title, event_date, evidence) VALUES (?, ?, ?, ?, ?, ?)",
            (ein, candidate["source_url"], digest, candidate["title"], candidate["event_date"], candidate["evidence"]),
        )
        added += int(db.total_changes > before)
    db.commit()
    return added


def search_scope(*, zip_code: str | None = None, city: str | None = None,
                 state: str | None = None, event_type: str | None = None,
                 date_from: str | None = None, date_to: str | None = None) -> tuple[str, list]:
    """Return the shared SQL scope used by the public event search adapter."""
    clauses = ["ve.status='active'", "ve.event_date >= date('now')"]
    params: list = []
    if zip_code:
        clauses.append("ve.location_zip=?")
        params.append(zip_code.strip()[:10])
    elif city and state:
        clauses.append("lower(ve.location_city)=lower(?) AND ve.location_state=?")
        params.extend([city.strip()[:100], state.strip()[:2].upper()])
    elif state:
        clauses.append("ve.location_state=?")
        params.append(state.strip()[:2].upper())
    if event_type:
        clauses.append("ve.event_type=?")
        params.append(event_type.strip()[:20])
    if date_from:
        clauses.append("ve.event_date>=?")
        params.append(date_from[:10])
    if date_to:
        clauses.append("ve.event_date<=?")
        params.append(date_to[:10])
    return " AND ".join(clauses), params
