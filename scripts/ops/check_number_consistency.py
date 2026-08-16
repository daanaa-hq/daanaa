#!/usr/bin/env python3
"""
Consistency gate for public-facing numbers.

Asserts that the canonical org count agrees across every artifact that reaches
users, BEFORE anything is deployed:

  1. the live DB   (registry_filters.canonical_active_count)
  2. homepage.json.gz  (what /api/stats serves)
  3. research-snapshot.json  (what /research serves)

Exit 0 = all agree (safe to deploy). Exit 1 = drift detected (DO NOT deploy).

This is the safety that lets the nightly pipeline auto-deploy: numbers only
ship when they match. If they ever disagree, the deploy aborts and the old
(correct) files stay live.

Usage:
  python3 scripts/check_number_consistency.py \
      --homepage precompute_output/content/homepage.json.gz \
      --snapshot frontend/public/research-snapshot.json
"""
import argparse
import gzip
import json
import sqlite3
import sys
from pathlib import Path

from scripts.registry_filters import canonical_active_count

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"


def _homepage_count(path: Path) -> int:
    with gzip.open(path) as f:
        return json.load(f)["stats"]["total_organizations"]


def _snapshot_count(path: Path) -> int:
    with open(path) as f:
        return json.load(f)["metadata"]["total_organizations"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--homepage", required=True, type=Path)
    ap.add_argument("--snapshot", required=True, type=Path)
    ap.add_argument("--db", default=DB_PATH, type=Path)
    args = ap.parse_args()

    conn = sqlite3.connect(str(args.db))
    db_count = canonical_active_count(conn)
    conn.close()

    try:
        home_count = _homepage_count(args.homepage)
        snap_count = _snapshot_count(args.snapshot)
    except (OSError, KeyError, json.JSONDecodeError) as e:
        print(f"FAIL: could not read an artifact: {e}", file=sys.stderr)
        return 1

    print(f"  DB canonical:      {db_count:,}")
    print(f"  homepage.json.gz:  {home_count:,}")
    print(f"  research snapshot: {snap_count:,}")

    if db_count == home_count == snap_count:
        print("OK: all public counts agree — safe to deploy.")
        return 0

    print("FAIL: public counts disagree — refusing to deploy drifted numbers.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
