#!/usr/bin/env python3
"""Upgrade staged website candidates only when the site discloses its own EIN.

This bounded verifier reads the homepages of existing candidates.  It does not
guess domains or alter canonical website fields.  A result is staged only when
the candidate page contains the exact nine-digit EIN already assigned to it.
"""

from __future__ import annotations
import argparse

import json
import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "merit_registry.db"
USER_AGENT = "DaanaaEvidenceVerifier/2026-08-13 (+https://daanaa.org)"
TIMEOUT_SECONDS = 12
EIN_PATTERN = re.compile(r"(?<!\d)(\d{2})[-\s]?(\d{7})(?!\d)")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def has_ein_disclosure(ein: str, url: str) -> tuple[str, str | None, bool, str]:
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS)
        if response.status_code >= 400:
            return ein, None, False, f"http_{response.status_code}"
        disclosed = {first + second for first, second in EIN_PATTERN.findall(response.text)}
        return ein, response.url, ein in disclosed, "homepage_ein_disclosed" if ein in disclosed else "ein_not_on_homepage"
    except requests.RequestException as exc:
        return ein, None, False, f"request_error:{type(exc).__name__}"


def candidates(conn: sqlite3.Connection, limit: int | None) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    sql = """
        SELECT ein, organization_name, city, state, candidate_domain, final_url
        FROM website_discovery_candidates
        WHERE source = 'domain_guess'
          AND verification_status = 'candidate_verified'
          AND final_url IS NOT NULL
          AND ein NOT IN (
              SELECT ein FROM website_discovery_candidates
              WHERE source = 'website_ein_disclosure'
          )
        GROUP BY ein
        ORDER BY confidence DESC, id DESC
    """
    if limit:
        sql += " LIMIT ?"
        return conn.execute(sql, (limit,)).fetchall()
    return conn.execute(sql).fetchall()


def run(workers: int, limit: int | None, dry_run: bool) -> dict[str, int | str]:
    run_id = "website_ein_disclosure_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    totals: dict[str, int | str] = {"run_id": run_id, "checked": 0, "ein_disclosed": 0, "staged": 0, "errors": 0}
    with sqlite3.connect(DB_PATH) as conn:
        rows = candidates(conn, limit)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(has_ein_disclosure, str(row["ein"]).zfill(9), row["final_url"]): row for row in rows}
            for future in as_completed(futures):
                row = futures[future]
                ein, final_url, disclosed, note = future.result()
                totals["checked"] += 1
                if note.startswith("request_error") or note.startswith("http_"):
                    totals["errors"] += 1
                if not disclosed:
                    continue
                totals["ein_disclosed"] += 1
                if dry_run:
                    continue
                domain = urlparse(final_url or row["final_url"]).netloc.lower().removeprefix("www.")
                notes = json.dumps(
                    {"source_candidate": "domain_guess", "evidence": note, "evidence_url": final_url or row["final_url"], "match_rule": "website_discloses_exact_ein"},
                    sort_keys=True,
                )
                conn.execute(
                    """
                    INSERT OR REPLACE INTO website_discovery_candidates (
                        run_id, ein, organization_name, city, state, candidate_domain, final_url,
                        verification_status, confidence, nonprofit_signal_count, identity_match_score,
                        identity_match_level, title, description, content_preview, source, notes, checked_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'candidate_verified', 99, 2, 1.0, 'ein_exact', NULL, 'Website self-discloses EIN', NULL, 'website_ein_disclosure', ?, ?)
                    """,
                    (run_id, ein, row["organization_name"], row["city"], row["state"], domain, final_url or row["final_url"], notes, now_iso()),
                )
                totals["staged"] += 1
        if not dry_run:
            conn.commit()
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.workers, args.limit, args.dry_run), sort_keys=True))


if __name__ == "__main__":
    main()
