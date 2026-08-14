#!/usr/bin/env python3
"""Rate-limited live validation for staged IRS 990-N self-reported websites.

Reads EIN-exact candidates from the staging ledger, checks one URL at a time at
a configurable global rate, and writes a separate validation evidence record.
It never changes registry_enriched or promotes a public website field.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

# Reuse the canonical discovery safeguards rather than maintaining a second
# robots or per-domain-rate-limit implementation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from website_discovery_comprehensive import UA, _can_fetch, _domain_pause


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "merit_registry.db"
USER_AGENT = UA


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def candidates(conn: sqlite3.Connection, limit: int | None) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    sql = """
        SELECT ein, organization_name, city, state, candidate_domain, final_url
        FROM website_discovery_candidates
        WHERE source = 'irs_990n_self_reported'
          AND ein NOT IN (
              SELECT ein FROM website_discovery_candidates
              WHERE source = 'irs_990n_live_validation'
          )
        GROUP BY ein
        ORDER BY ein
    """
    if limit:
        sql += " LIMIT ?"
        return conn.execute(sql, (limit,)).fetchall()
    return conn.execute(sql).fetchall()


def validate(url: str) -> tuple[str | None, int | None, str]:
    if not _can_fetch(url):
        return None, None, "robots_disallowed"
    try:
        _domain_pause(url)
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=12, allow_redirects=True, stream=True)
        response.close()
        return response.url, response.status_code, "live" if response.status_code < 400 else "http_error"
    except requests.RequestException as exc:
        return None, None, f"request_error:{type(exc).__name__}"


def run(rate: float, limit: int | None, dry_run: bool) -> dict[str, int | str]:
    run_id = "irs_990n_live_validation_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    totals: dict[str, int | str] = {"run_id": run_id, "checked": 0, "live": 0, "unavailable": 0, "staged": 0}
    interval = 1 / rate
    with sqlite3.connect(DB_PATH) as conn:
        rows = candidates(conn, limit)
        for row in rows:
            started = time.monotonic()
            final_url, status_code, result = validate(row["final_url"])
            totals["checked"] += 1
            live = result == "live"
            totals["live" if live else "unavailable"] += 1
            if not dry_run:
                notes = json.dumps(
                    {"source_candidate": "irs_990n_self_reported", "result": result, "http_status": status_code},
                    sort_keys=True,
                )
                final = final_url or row["final_url"]
                domain = urlparse(final).netloc.lower().removeprefix("www.")
                conn.execute(
                    """
                    INSERT OR REPLACE INTO website_discovery_candidates (
                        run_id, ein, organization_name, city, state, candidate_domain, final_url,
                        verification_status, confidence, nonprofit_signal_count, identity_match_score,
                        identity_match_level, title, description, content_preview, source, notes, checked_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1.0, 'ein_exact', NULL, NULL, NULL, 'irs_990n_live_validation', ?, ?)
                    """,
                    (
                        run_id, row["ein"], row["organization_name"], row["city"], row["state"], domain, final,
                        "candidate_live" if live else "candidate_unavailable", 99 if live else 80, notes, now_iso(),
                    ),
                )
                totals["staged"] += 1
            remaining = interval - (time.monotonic() - started)
            if remaining > 0:
                time.sleep(remaining)
        if not dry_run:
            conn.commit()
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rate", type=float, default=8.0, help="Global requests per second; default 8")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not 0 < args.rate <= 10:
        parser.error("--rate must be greater than 0 and no more than 10")
    print(json.dumps(run(args.rate, args.limit, args.dry_run), sort_keys=True))


if __name__ == "__main__":
    main()
