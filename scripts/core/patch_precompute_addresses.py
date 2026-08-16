#!/usr/bin/env python3
"""
Patch street_address into existing precompute org JSON files.

Background: precompute_orgs.py was updated to include street_address but all
~1.97M existing files were written before the fix and have street_address=null.
This script patches only that field in-place without re-running the full precompute.

Uses 4 worker processes. Each worker reads files, checks if street_address is null,
updates from the DB lookup dict, rewrites. Skips files that already have an address.

Resume-safe: files with non-null address are skipped on re-run.
"""

import gzip
import json
import os
import sqlite3
import sys
from multiprocessing import Pool, cpu_count
from pathlib import Path

DB_PATH = os.environ.get("MERIT_DB_PATH", "data/merit_registry.db")
OUT = os.environ.get("PRECOMPUTE_OUT", "precompute_output")
ORG_DIR = Path(OUT) / "orgs"
WORKERS = min(4, cpu_count())

_addr_map: dict[str, str] = {}


def _load_address_map() -> dict[str, str]:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    rows = conn.execute(
        "SELECT EIN, street_address FROM registry_enriched "
        "WHERE street_address IS NOT NULL AND street_address != ''"
    ).fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}


def _patch_file(path: Path, addr_map: dict[str, str]) -> int:
    """Return 1 if patched, 0 if skipped."""
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return 0

    if d.get("street_address") is not None:
        return 0

    ein = d.get("EIN") or path.stem
    addr = addr_map.get(ein)
    if not addr:
        return 0

    d["street_address"] = addr
    try:
        with gzip.open(path, "wt", encoding="utf-8", compresslevel=1) as f:
            json.dump(d, f, separators=(",", ":"))
    except Exception:
        return 0
    return 1


def _worker(args):
    path_str, addr_map = args
    return _patch_file(Path(path_str), addr_map)


def main():
    print("Loading address map from DB...")
    addr_map = _load_address_map()
    print(f"  {len(addr_map):,} orgs with street address")

    print("Scanning precompute files...")
    all_files = list(ORG_DIR.rglob("*.json.gz"))
    total = len(all_files)
    print(f"  {total:,} total files")

    args = [(str(p), addr_map) for p in all_files]

    print(f"Patching with {WORKERS} workers...")
    patched = 0
    done = 0
    with Pool(WORKERS) as pool:
        for result in pool.imap_unordered(_worker, args, chunksize=500):
            patched += result
            done += 1
            if done % 100_000 == 0:
                pct = done / total * 100
                print(f"  {done:,}/{total:,} ({pct:.1f}%) — {patched:,} patched")

    print(f"\nDone. {patched:,} files updated out of {total:,} scanned.")


if __name__ == "__main__":
    main()
