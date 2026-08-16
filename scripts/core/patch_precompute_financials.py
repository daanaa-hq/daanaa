#!/usr/bin/env python3
"""
scripts/patch_precompute_financials.py

Patches existing precomputed org JSON files to include multi-year
financial history from propublica_financials.

Only touches files for EINs that have financial history rows.
Reads each file, injects the `financials` array, rewrites in-place.
Safe to re-run — idempotent.

Usage:
    python3 scripts/patch_precompute_financials.py
    python3 scripts/patch_precompute_financials.py --limit 1000  # test run
"""

import gzip, json, sqlite3, sys, argparse
from pathlib import Path
from datetime import datetime

DB_PATH     = Path("data/merit_registry.db")
PRECOMPUTE  = Path(sys.argv[0]).parent.parent / "precompute_output" / "orgs"


def load_financials(db):
    print("Loading financial history from DB...", flush=True)
    rows = db.execute("""
        SELECT EIN, tax_prd_yr, totrevenue, totfuncexpns, totassetsend,
               totliabend, totnetassetend, totcntrbgfts, totprgmrevnue,
               compnsatncurrofcr, pdf_url
        FROM propublica_financials
        ORDER BY EIN, tax_prd_yr DESC
    """).fetchall()
    index = {}
    for r in rows:
        ein = r[0]
        if ein not in index:
            index[ein] = []
        index[ein].append({
            'tax_prd_yr':        r[1],
            'totrevenue':        r[2],
            'totfuncexpns':      r[3],
            'totassetsend':      r[4],
            'totliabend':        r[5],
            'totnetassetend':    r[6],
            'totcntrbgfts':      r[7],
            'totprgmrevnue':     r[8],
            'compnsatncurrofcr': r[9],
            'pdf_url':           r[10],
        })
    print(f"  {len(index):,} EINs with financial history", flush=True)
    return index


def patch_file(path, financials):
    try:
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        data['financials'] = financials
        with gzip.open(path, 'wt', encoding='utf-8', compresslevel=1) as f:
            json.dump(data, f, separators=(',', ':'))
        return True
    except Exception as e:
        print(f"  ERROR {path}: {e}", flush=True)
        return False


def main(limit=None):
    db = sqlite3.connect(str(DB_PATH))
    index = load_financials(db)
    db.close()

    precompute_dir = Path("precompute_output/orgs")
    print(f"Patching files in {precompute_dir}...", flush=True)

    patched = skipped = errors = 0
    start = datetime.now()

    eins_to_patch = list(index.keys())
    if limit:
        eins_to_patch = eins_to_patch[:limit]

    total = len(eins_to_patch)
    for i, ein in enumerate(eins_to_patch):
        prefix = ein[:3]
        path = precompute_dir / prefix / f"{ein}.json.gz"
        if not path.exists():
            skipped += 1
            continue
        if patch_file(path, index[ein]):
            patched += 1
        else:
            errors += 1

        if (i + 1) % 50000 == 0:
            elapsed = (datetime.now() - start).total_seconds()
            rate = (i + 1) / elapsed
            eta = (total - i - 1) / rate
            print(f"  {i+1:,}/{total:,} — patched={patched:,} skipped={skipped:,} "
                  f"errors={errors} rate={rate:.0f}/s eta={eta:.0f}s", flush=True)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nDone in {elapsed:.0f}s — patched={patched:,} skipped={skipped:,} errors={errors}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Only patch this many EINs (test mode)")
    args = parser.parse_args()
    main(limit=args.limit)
