#!/usr/bin/env python3
"""
scripts/build_fts_index.py

Builds (or rebuilds) the SQLite FTS5 full-text search index over
registry_enriched. The index covers organization name, mission, location,
category, and cause tags — enabling semantic keyword search that surfaces
relevant orgs by mission, not just name substring matches.

Only indexes orgs the API would actually serve: subsection='3', deductibility=1,
not IRS-revoked, org_status != 'revoked' -- matches daanaa_api.py's
_DEDUCTIBILITY_FILTER exactly (corrected 2026-08-21; the prior predicate
under/over-indexed ~24K orgs relative to the live endpoint, see LESSONS.md).

Run after every major data update (IRS sync, re-scoring, enrichment).

Usage:
    source ~/meritgiving/venv/bin/activate
    python3 scripts/build_fts_index.py
    python3 scripts/build_fts_index.py --rebuild    # drop and recreate
"""

import sqlite3
import argparse
import logging
import time
from pathlib import Path

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"
BATCH_SIZE = 50000

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH, timeout=60)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("PRAGMA temp_store=MEMORY")
    return db


def table_exists(db: sqlite3.Connection, name: str) -> bool:
    return db.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()[0] > 0


def build(db: sqlite3.Connection, rebuild: bool) -> None:
    if rebuild and table_exists(db, "org_fts"):
        log.info("Dropping existing org_fts table...")
        db.execute("DROP TABLE IF EXISTS org_fts")
        db.commit()

    if not table_exists(db, "org_fts"):
        log.info("Creating org_fts FTS5 virtual table...")
        db.execute("""
            CREATE VIRTUAL TABLE org_fts USING fts5(
                ein        UNINDEXED,
                merit_tier UNINDEXED,
                org_name,
                mission,
                city,
                state,
                metro,
                category,
                cause_tags,
                tokenize = "unicode61 remove_diacritics 2"
            )
        """)
        db.commit()
        log.info("FTS5 table created.")

        log.info("Counting tax-deductible, active orgs...")
        # Predicate must match daanaa_api.py's _DEDUCTIBILITY_FILTER exactly --
        # the endpoint is the single source of truth for "should this org be
        # findable." Previously this only checked deductibility+org_status,
        # missing subsection='3' and irs_revoked, which let 17,176 orgs the
        # endpoint would never actually serve stay searchable (found 2026-08-21
        # while investigating a search-latency incident; see LESSONS.md).
        total = db.execute("""
            SELECT COUNT(*) FROM registry_enriched
            WHERE organization_name IS NOT NULL
              AND subsection = '3' AND deductibility = 1
              AND COALESCE(irs_revoked, 0) != 1
              AND COALESCE(org_status, '') != 'revoked'
        """).fetchone()[0]
        log.info(f"Indexing {total:,} orgs in batches of {BATCH_SIZE:,}...")

        t0 = time.time()
        offset = 0
        inserted = 0

        while offset < total:
            db.execute("""
                INSERT INTO org_fts (ein, merit_tier, org_name, mission, city, state, metro, category, cause_tags)
                SELECT
                    EIN,
                    COALESCE(merit_tier, 'Spark'),
                    organization_name,
                    COALESCE(mission, ''),
                    COALESCE(CITY, ''),
                    COALESCE(STATE, ''),
                    COALESCE(metro, ''),
                    NTEECC,
                    COALESCE(cause_tags, '{}')
                FROM registry_enriched
                WHERE organization_name IS NOT NULL
                  AND subsection = '3' AND deductibility = 1
                  AND COALESCE(irs_revoked, 0) != 1
                  AND COALESCE(org_status, '') != 'revoked'
                ORDER BY EIN
                LIMIT ? OFFSET ?
            """, (BATCH_SIZE, offset))
            db.commit()

            inserted += BATCH_SIZE
            elapsed = time.time() - t0
            rate = inserted / elapsed if elapsed > 0 else 0
            eta_sec = (total - inserted) / rate if rate > 0 else 0
            pct = 100.0 * inserted / total
            log.info(f"  [{pct:5.1f}%] {inserted:,}/{total:,} — {rate:.0f} orgs/sec, ETA {eta_sec/60:.1f}min")

            offset += BATCH_SIZE

        elapsed = time.time() - t0
        count = db.execute("SELECT COUNT(*) FROM org_fts").fetchone()[0]
        log.info(f"Indexed {count:,} orgs in {elapsed:.0f}s ({elapsed/60:.1f}min)")
    else:
        log.info("org_fts already exists. Use --rebuild to recreate.")

    log.info("Optimising FTS5 index...")
    db.execute("INSERT INTO org_fts(org_fts) VALUES('optimize')")
    db.commit()
    log.info("Done.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true", help="Drop and recreate the index")
    args = ap.parse_args()
    db = connect()
    build(db, args.rebuild)
    db.close()


if __name__ == "__main__":
    main()
