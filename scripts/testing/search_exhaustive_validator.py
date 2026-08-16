#!/usr/bin/env python3
"""Exhaustive self-search validation over the ENTIRE eligible corpus.

The finite-corpus advantage (docs/SEARCH_ENGINE_LESSONS.md): Daanaa's search
space is closed — every org, name, and EIN is known. So search quality is not
estimated from samples or user behavior; it is VERIFIED, org by org, offline.

For each eligible org, runs the production query plan (exact name-phrase UNION
bm25, exact-name-first ordering) and records whether the org's typed name puts
it in the top 5. Misses stream to a CSV for pattern analysis.

Runs multiprocess at low priority (nice 15) so the live API, enrichment
daemons, and the website are unaffected.

Usage:
    source ~/meritgiving/venv/bin/activate
    python3 scripts/search_exhaustive_validator.py              # full corpus
    python3 scripts/search_exhaustive_validator.py --limit 50000
    python3 scripts/search_exhaustive_validator.py --workers 8
"""
import argparse
import csv
import multiprocessing as mp
import os
import re
import sqlite3
import time
from pathlib import Path

DB = Path.home() / "meritgiving/data/merit_registry.db"
OUT_DIR = Path.home() / "meritgiving/logs"

# KEEP IN SYNC with daanaa_api.py:_sanitize_fts_query
_APOS = re.compile(r"['’`]")
_CLEAN = re.compile(r'[^\w\s]', re.UNICODE)
_NOISE = frozenset({
    'nonprofit', 'nonprofits', 'charity', 'charities',
    'organization', 'organizations', '501c3', 'ngo',
    'find', 'search', 'best', 'top', 'local', 'near',
    'metro', 'greater', 'region', 'area',
})


def sanitize(text: str) -> str:
    clean = _CLEAN.sub(' ', _APOS.sub('', text))
    words = [w for w in clean.split() if w.lower() not in _NOISE]
    words = words[:12] if len(words) >= 2 else [w for w in words if len(w) >= 2]
    if not words:
        return '""'
    # Single-char tokens match exactly (no star) — see daanaa_api.py comment.
    return ' '.join(f'"{w}"*' if len(w) >= 2 else f'"{w}"' for w in words)


PLAN_SQL = """
    SELECT r.EIN, r.organization_name FROM registry_enriched r
    JOIN (SELECT ein, MIN(rel) AS rel FROM (
        SELECT ein, -1e9 AS rel FROM org_fts WHERE org_fts MATCH ?
        UNION ALL
        SELECT ein, bm25(org_fts, 10, 5, 1, 1) AS rel
        FROM org_fts WHERE org_fts MATCH ? ORDER BY rel LIMIT 2000
    ) GROUP BY ein) fts ON r.EIN = fts.ein
    ORDER BY (UPPER(r.organization_name) = ?) DESC, fts.rel LIMIT 5
"""


def worker(args):
    shard, n_shards, limit = args
    os.nice(15)  # never compete with the live API or daemons
    db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    db.execute("PRAGMA temp_store=MEMORY")
    q = """
        SELECT organization_name, EIN FROM registry_enriched
        WHERE organization_name IS NOT NULL
          AND deductibility = 1 AND org_status = 'active'
          AND (CAST(EIN AS INTEGER) % ?) = ?
    """
    params = [n_shards, shard]
    if limit:
        q += " LIMIT ?"
        params.append(limit)
    checked = hits = 0
    misses = []
    for name, ein in db.execute(q, params):
        expr = sanitize(name)
        toks = _CLEAN.sub(' ', _APOS.sub('', name)).split()[:12]
        phrase = f'org_name : "{" ".join(toks)}"' if toks else '""'
        try:
            rows = db.execute(PLAN_SQL, (phrase, expr, name.upper())).fetchall()
            found = name in {r[1] for r in rows} or ein in {r[0] for r in rows}
        except sqlite3.OperationalError as e:
            found = False
            misses.append((ein, name, f"SQL_ERROR: {e}"))
            checked += 1
            continue
        checked += 1
        if found:
            hits += 1
        else:
            misses.append((ein, name, "not in top 5"))
    db.close()
    return checked, hits, misses


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=max(2, (os.cpu_count() or 4) * 3 // 4))
    ap.add_argument("--limit", type=int, default=0, help="per-shard cap (0 = full corpus)")
    args = ap.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    miss_path = OUT_DIR / f"search_exhaustive_misses_{stamp}.csv"
    report_path = OUT_DIR / f"search_exhaustive_report_{stamp}.txt"

    t0 = time.time()
    shards = [(i, args.workers, args.limit or None) for i in range(args.workers)]
    total = hits = 0
    all_misses = []
    with mp.Pool(args.workers) as pool:
        for checked, ok, misses in pool.imap_unordered(worker, shards):
            total += checked
            hits += ok
            all_misses.extend(misses)
            elapsed = time.time() - t0
            rate = total / elapsed if elapsed else 0
            print(f"progress: {total:,} checked, {hits:,} hits "
                  f"({100*hits/max(1,total):.2f}%), {rate:.0f}/s", flush=True)

    with open(miss_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ein", "organization_name", "reason"])
        w.writerows(all_misses)

    elapsed = time.time() - t0
    summary = (
        f"Exhaustive self-search validation — {time.strftime('%Y-%m-%d %H:%M')}\n"
        f"corpus checked: {total:,}\n"
        f"top-5 hits:     {hits:,} ({100*hits/max(1,total):.3f}%)\n"
        f"misses:         {len(all_misses):,} → {miss_path.name}\n"
        f"wall time:      {elapsed/3600:.2f}h at {total/max(1,elapsed):.0f} q/s "
        f"({args.workers} workers, nice 15)\n"
    )
    report_path.write_text(summary)
    print(summary)


if __name__ == "__main__":
    main()
