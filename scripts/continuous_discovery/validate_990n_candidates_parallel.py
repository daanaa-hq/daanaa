#!/usr/bin/env python3
"""Bounded 990-N validator: 8 request starts/second, 24 requests in flight."""

from __future__ import annotations

import argparse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from validate_990n_candidates import candidates, validate


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "merit_registry.db"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run(rate: float, workers: int, limit: int | None, dry_run: bool) -> dict[str, int | str]:
    run_id = "irs_990n_live_validation_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    totals: dict[str, int | str] = {"run_id": run_id, "checked": 0, "live": 0, "unavailable": 0, "staged": 0}
    interval = 1 / rate
    with sqlite3.connect(DB_PATH) as conn:
        rows = candidates(conn, limit)

        def record(row: sqlite3.Row, final_url: str | None, status_code: int | None, result: str) -> None:
            totals["checked"] += 1
            live = result == "live"
            totals["live" if live else "unavailable"] += 1
            if dry_run:
                return
            final = final_url or row["final_url"]
            domain = urlparse(final).netloc.lower().removeprefix("www.")
            notes = json.dumps(
                {"source_candidate": "irs_990n_self_reported", "result": result, "http_status": status_code},
                sort_keys=True,
            )
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

        pending = {}
        next_start = time.monotonic()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for row in rows:
                delay = next_start - time.monotonic()
                if delay > 0:
                    time.sleep(delay)
                pending[pool.submit(validate, row["final_url"])] = row
                next_start += interval
                if len(pending) < workers:
                    continue
                done, _ = wait(pending, return_when=FIRST_COMPLETED)
                for future in done:
                    row = pending.pop(future)
                    record(row, *future.result())
            for future, row in pending.items():
                record(row, *future.result())
        if not dry_run:
            conn.commit()
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rate", type=float, default=8.0)
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not 0 < args.rate <= 10:
        parser.error("--rate must be greater than 0 and no more than 10")
    print(json.dumps(run(args.rate, args.workers, args.limit, args.dry_run), sort_keys=True))


if __name__ == "__main__":
    main()
