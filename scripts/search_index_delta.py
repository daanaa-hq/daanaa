#!/usr/bin/env python3
"""Delta search-index sync + findability proof for newly added orgs.

Process rule (founder-approved 2026-07-19): every org that enters the registry
must become searchable AND be proven findable — automatically, at ingestion
time, not whenever the next full FTS rebuild happens to run.

Three phases:
  1. DETECT  — eligible orgs (deductible + active, same filter as
               build_fts_index.py) present in registry_enriched but absent
               from org_fts.
  2. INDEX   — plain FTS5 INSERTs for just those orgs (no full rebuild;
               small batches with retry so concurrent daemons keep writing).
  3. VERIFY  — each newly indexed org self-searches through the production
               query plan; misses are logged, never silently dropped.

Called from refresh_irs_data.sh (weekly new-org load) and
overnight_pipeline.py (nightly safety net — no-op when nothing is missing).

Usage:
    source ~/meritgiving/venv/bin/activate
    python3 scripts/search_index_delta.py            # detect+index+verify
    python3 scripts/search_index_delta.py --dry-run  # detect only
"""
import argparse
import re
import sqlite3
import time
from pathlib import Path

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"
LOG_PATH = Path.home() / "meritgiving/logs/search_index_delta.log"
BATCH = 5000

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
    return ' '.join(f'"{w}"*' if len(w) >= 2 else f'"{w}"' for w in words)


def log(msg: str):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        LOG_PATH.parent.mkdir(exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def find_unindexed(db: sqlite3.Connection) -> list:
    """Eligible orgs missing from org_fts (the searchability gap).

    ein is UNINDEXED inside FTS5, so a SQL join against it cannot use an
    index — pull the indexed EIN set into memory (1.7M strings, seconds)
    and set-difference in Python instead.
    """
    indexed = {r[0] for r in db.execute("SELECT ein FROM org_fts")}
    # Column order MUST mirror index_orgs' INSERT slot order — the verify
    # phase caught this exact class of bug once already (org_name receiving
    # merit_tier): if you touch one list, touch both.
    rows = db.execute("""
        SELECT EIN, merit_tier, organization_name, mission,
               CITY, STATE, metro, NTEECC, cause_tags
        FROM registry_enriched
        WHERE organization_name IS NOT NULL
          AND deductibility IN (1, '1') AND org_status = 'active'
    """).fetchall()
    return [r for r in rows if r[0] not in indexed]


def index_orgs(db: sqlite3.Connection, rows: list) -> int:
    """Incrementally insert rows into org_fts. Returns count inserted."""
    inserted = 0
    for i in range(0, len(rows), BATCH):
        chunk = rows[i:i + BATCH]
        for attempt in range(5):
            try:
                db.executemany(
                    "INSERT INTO org_fts (ein, merit_tier, org_name, mission, "
                    "city, state, metro, category, cause_tags) "
                    "VALUES (?, COALESCE(?, 'Spark'), ?, COALESCE(?, ''), "
                    "COALESCE(?, ''), COALESCE(?, ''), COALESCE(?, ''), ?, "
                    "COALESCE(?, '{}'))",
                    chunk,
                )
                db.commit()
                inserted += len(chunk)
                break
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < 4:
                    time.sleep(2 ** attempt)
                    continue
                raise
    return inserted


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


def verify(db: sqlite3.Connection, rows: list) -> list:
    """Self-search each org through the production plan. Returns misses."""
    misses = []
    for row in rows:
        ein, name = row[0], row[2]
        expr = sanitize(name)
        toks = _CLEAN.sub(' ', _APOS.sub('', name)).split()[:12]
        phrase = f'org_name : "{" ".join(toks)}"' if toks else '""'
        try:
            found = db.execute(PLAN_SQL, (phrase, expr, name.upper())).fetchall()
            if not (name in {r[1] for r in found} or ein in {r[0] for r in found}):
                misses.append((ein, name, "not in top 5"))
        except sqlite3.OperationalError as e:
            misses.append((ein, name, f"SQL_ERROR: {e}"))
    return misses


def run(db_path=DB_PATH, dry_run=False) -> dict:
    db = sqlite3.connect(db_path, timeout=60)
    db.execute("PRAGMA journal_mode=WAL")
    try:
        rows = find_unindexed(db)
        result = {"unindexed": len(rows), "indexed": 0, "verified_ok": 0, "misses": []}
        if not rows:
            log("delta: index complete — no unindexed eligible orgs")
            return result
        log(f"delta: {len(rows):,} eligible orgs missing from search index")
        if dry_run:
            return result
        result["indexed"] = index_orgs(db, rows)
        log(f"delta: indexed {result['indexed']:,} orgs incrementally")
        misses = verify(db, rows)
        result["verified_ok"] = len(rows) - len(misses)
        result["misses"] = misses
        log(f"delta: findability verified {result['verified_ok']:,}/{len(rows):,}")
        for ein, name, reason in misses[:20]:
            log(f"delta: MISS {ein} {name!r} — {reason}")
        return result
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="detect only, no writes")
    args = ap.parse_args()
    run(dry_run=args.dry_run)
