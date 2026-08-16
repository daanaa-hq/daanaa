#!/usr/bin/env python3
"""
scripts/patch_precompute_v5_context.py

Refresh the `v5_context` block in existing precomputed org JSON files from
the CURRENT database. Precompute files are generated once and skipped on
re-runs, so when a re-score changes an org's archetype/band/score the static
files go stale (e.g. an org showing "Endowment-Funded Grantmakers" when the
DB now says "Fee-for-Service").

Rebuilds v5_context via build_v5_context — the SAME pure builder used by
precompute_orgs.py and the live API — so the two surfaces can never drift.

Only rewrites a file when the rebuilt v5_context actually differs (idempotent,
safe to re-run). Files for orgs with no v5 score are left untouched.

Usage:
    python3 scripts/patch_precompute_v5_context.py --limit 2000   # test run
    python3 scripts/patch_precompute_v5_context.py                # full run
    python3 scripts/patch_precompute_v5_context.py --dry-run      # report only
"""

import argparse
import gzip
import json
import os
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from enrich_api_responses import build_v5_context  # noqa: E402

DB_PATH    = Path(os.environ.get("MERIT_DB_PATH", "data/merit_registry.db"))
PRECOMPUTE = Path(__file__).resolve().parent.parent / "precompute_output" / "orgs"


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def load_v5_fields(db):
    """Pull every org that has a v5 archetype, keyed by EIN."""
    log("Loading current v5 fields from DB (orgs with an archetype)...")
    rows = db.execute("""
        SELECT EIN,
               merit_archetype_v5, merit_archetype_v5_label,
               merit_band_v5, merit_band_v5_label,
               merit_score_v5, merit_health_signal_v5,
               merit_peer_group_v5, merit_peer_count_v5,
               months_of_reserve
        FROM registry_enriched
        WHERE merit_archetype_v5 IS NOT NULL
    """).fetchall()
    index = {r[0]: r[1:] for r in rows}
    log(f"  {len(index):,} orgs with a v5 archetype")
    return index


def file_for_ein(ein: str) -> Path:
    # Precompute layout: orgs/<first-3-of-ein>/<ein>.json.gz
    return PRECOMPUTE / ein[:3] / f"{ein}.json.gz"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="cap orgs processed (test)")
    ap.add_argument("--dry-run", action="store_true", help="report changes, write nothing")
    args = ap.parse_args()

    if not DB_PATH.exists():
        sys.exit(f"DB not found: {DB_PATH}")
    if not PRECOMPUTE.exists():
        sys.exit(f"Precompute dir not found: {PRECOMPUTE}")

    db = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    fields = load_v5_fields(db)
    db.close()

    seen = updated = missing_file = no_change = errors = 0
    changed_paths = []

    for ein, vals in fields.items():
        if args.limit and seen >= args.limit:
            break
        seen += 1

        path = file_for_ein(ein)
        if not path.exists():
            missing_file += 1
            continue

        try:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            errors += 1
            log(f"  read error {ein}: {e}")
            continue

        (arch_key, arch_label, band_key, band_label,
         score, health, peer_group, peer_count, reserves_mo) = vals

        new_v5 = build_v5_context(
            arch_key, arch_label, band_key, band_label,
            score, health, peer_group, peer_count, reserves_mo,
        )

        if data.get("v5_context") == new_v5:
            no_change += 1
            continue

        if args.dry_run:
            updated += 1
            if len(changed_paths) < 5:
                old = (data.get("v5_context") or {}).get("archetype", {}).get("label")
                new = (new_v5 or {}).get("archetype", {}).get("label")
                log(f"  WOULD update {ein}: archetype {old!r} -> {new!r}")
            continue

        data["v5_context"] = new_v5
        tmp = path.with_suffix(".tmp.gz")
        try:
            with gzip.open(tmp, "wt", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(tmp, path)   # atomic swap — never a half-written file
            updated += 1
            changed_paths.append(str(path))
        except Exception as e:
            errors += 1
            if tmp.exists():
                tmp.unlink()
            log(f"  write error {ein}: {e}")

        if seen % 50_000 == 0:
            log(f"  {seen:,} seen / {updated:,} updated / {no_change:,} unchanged")

    log("=" * 60)
    log(f"Done. seen={seen:,} updated={updated:,} unchanged={no_change:,} "
        f"missing_file={missing_file:,} errors={errors:,}")
    if args.dry_run:
        log("DRY RUN — no files written")

    # Emit changed-file list so deploy can rsync only what moved
    if changed_paths and not args.dry_run:
        manifest = PRECOMPUTE.parent / "v5_patch_changed.txt"
        manifest.write_text("\n".join(changed_paths))
        log(f"Changed-file manifest: {manifest} ({len(changed_paths):,} files)")


if __name__ == "__main__":
    main()
