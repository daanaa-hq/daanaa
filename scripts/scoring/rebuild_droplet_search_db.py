#!/usr/bin/env python3
"""
Rebuild search.db for the droplet from the local merit_registry.db.

Produces two tables:
  org_search  — FTS5 index (ein, name, mission, ntee1, nteecc, city, state)
  orgs        — Full row store for all 1.8M orgs (used as fallback when
                a precomputed org file doesn't exist, e.g. IRS_BMF orgs)

Run from ~/meritgiving:
    python3 scripts/rebuild_droplet_search_db.py
Output: data/droplet_search.db  (~500MB, gzipped for transfer)
"""

import sqlite3
import json
import gzip
import time
from pathlib import Path

SRC_DB  = Path.home() / "meritgiving/data/merit_registry.db"
OUT_DB  = Path.home() / "meritgiving/data/droplet_search.db"
BATCH   = 50_000

def main():
    OUT_DB.unlink(missing_ok=True)

    src  = sqlite3.connect(SRC_DB, timeout=30)
    src.row_factory = sqlite3.Row
    dest = sqlite3.connect(OUT_DB, timeout=60)

    print("Creating tables…")
    dest.executescript("""
        CREATE TABLE IF NOT EXISTS orgs (
            EIN              TEXT PRIMARY KEY,
            organization_name TEXT,
            NTEE1            TEXT,
            NTEECC           TEXT,
            CITY             TEXT,
            STATE            TEXT,
            zipcode          TEXT,
            mission          TEXT,
            mission_source   TEXT,
            merit_score      REAL,
            merit_tier       TEXT,
            merit_band       TEXT,
            ntee1_percentile REAL,
            peer_percentile  REAL,
            peer_rank        INTEGER,
            peer_total       INTEGER,
            total_revenue    REAL,
            total_expenses   REAL,
            net_assets       REAL,
            months_of_reserve REAL,
            program_expense_pct REAL,
            employee_count   INTEGER,
            latest_tax_year  INTEGER,
            ruling_date      TEXT,
            website          TEXT,
            website_status   TEXT,
            donate_url       TEXT,
            donate_platform  TEXT,
            donate_url_status TEXT,
            cause_tags       TEXT,
            is_hidden_gem    INTEGER DEFAULT 0,
            data_source      TEXT,
            source           TEXT,
            merit_archetype_v5       TEXT,
            merit_archetype_v5_label TEXT,
            merit_band_v5            TEXT,
            merit_band_v5_label      TEXT,
            merit_score_v5           REAL,
            merit_health_signal_v5   TEXT,
            merit_peer_group_v5      TEXT,
            merit_peer_count_v5      INTEGER
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS org_search USING fts5(
            ein,
            organization_name,
            mission,
            NTEE1,
            NTEECC,
            CITY,
            STATE,
            content=orgs,
            content_rowid=rowid
        );
    """)
    dest.commit()

    total_src = src.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    print(f"Source rows: {total_src:,}")

    inserted = 0
    start = time.time()

    query = """
        SELECT
            EIN, organization_name, NTEE1, NTEECC, CITY, STATE, zipcode,
            mission, mission_source,
            merit_score, merit_tier, merit_band,
            ntee1_percentile, peer_percentile, peer_rank, peer_total,
            total_revenue, total_expenses, net_assets,
            CASE WHEN months_of_reserve BETWEEN -120 AND 120
                 THEN months_of_reserve ELSE NULL END as months_of_reserve,
            program_expense_pct, employee_count, latest_tax_year,
            ruling_date, website, website_status,
            donate_url, donate_platform, donate_url_status,
            cause_tags, is_hidden_gem,
            data_source, source,
            merit_archetype_v5, merit_archetype_v5_label, merit_band_v5,
            merit_band_v5_label, merit_score_v5, merit_health_signal_v5,
            merit_peer_group_v5, merit_peer_count_v5
        FROM registry_enriched
        ORDER BY merit_score DESC NULLS LAST
    """

    batch_orgs = []
    batch_fts  = []

    for row in src.execute(query):
        r = dict(row)
        batch_orgs.append((
            r["EIN"], r["organization_name"], r["NTEE1"], r["NTEECC"],
            r["CITY"], r["STATE"], r["zipcode"],
            r["mission"], r["mission_source"],
            r["merit_score"], r["merit_tier"], r["merit_band"],
            r["ntee1_percentile"], r["peer_percentile"], r["peer_rank"], r["peer_total"],
            r["total_revenue"], r["total_expenses"], r["net_assets"],
            r["months_of_reserve"], r["program_expense_pct"], r["employee_count"],
            r["latest_tax_year"], r["ruling_date"],
            r["website"], r["website_status"],
            r["donate_url"], r["donate_platform"], r["donate_url_status"],
            r["cause_tags"], 1 if r["is_hidden_gem"] else 0,
            r["data_source"], r["source"],
            r["merit_archetype_v5"], r["merit_archetype_v5_label"], r["merit_band_v5"],
            r["merit_band_v5_label"], r["merit_score_v5"], r["merit_health_signal_v5"],
            r["merit_peer_group_v5"], r["merit_peer_count_v5"],
        ))
        batch_fts.append((r["EIN"], r["organization_name"] or "", r["mission"] or "",
                          r["NTEE1"] or "", r["NTEECC"] or "",
                          r["CITY"] or "", r["STATE"] or ""))

        if len(batch_orgs) >= BATCH:
            dest.executemany("""
                INSERT OR REPLACE INTO orgs VALUES (
                    ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                )
            """, batch_orgs)
            dest.executemany("""
                INSERT INTO org_search(ein, organization_name, mission, NTEE1, NTEECC, CITY, STATE)
                VALUES (?,?,?,?,?,?,?)
            """, batch_fts)
            dest.commit()
            inserted += len(batch_orgs)
            elapsed = time.time() - start
            rate = inserted / elapsed
            eta = (total_src - inserted) / rate / 60 if rate > 0 else 0
            print(f"  {inserted:,} / {total_src:,}  ({rate:.0f}/s  ETA {eta:.1f}m)", end="\r")
            batch_orgs.clear()
            batch_fts.clear()

    if batch_orgs:
        dest.executemany("""
            INSERT OR REPLACE INTO orgs VALUES (
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
            )
        """, batch_orgs)
        dest.executemany("""
            INSERT INTO org_search(ein, organization_name, mission, NTEE1, NTEECC, CITY, STATE)
            VALUES (?,?,?,?,?,?,?)
        """, batch_fts)
        dest.commit()
        inserted += len(batch_orgs)

    print(f"\nOptimizing FTS index…")
    dest.execute("INSERT INTO org_search(org_search) VALUES('optimize')")
    dest.commit()

    print(f"\nCreating indexes…")
    dest.executescript("""
        CREATE INDEX IF NOT EXISTS idx_orgs_ntee1 ON orgs(NTEE1);
        CREATE INDEX IF NOT EXISTS idx_orgs_state ON orgs(STATE);
        CREATE INDEX IF NOT EXISTS idx_orgs_score ON orgs(merit_score DESC);
        CREATE INDEX IF NOT EXISTS idx_orgs_hidden ON orgs(is_hidden_gem);
        CREATE INDEX IF NOT EXISTS idx_orgs_merit_tier ON orgs(merit_tier);
        -- Multi-category + revenue-band filters (directory UI); without these
        -- the filter browse path full-scans 1.8M rows (~7s, 2026-06-09 fix)
        CREATE INDEX IF NOT EXISTS idx_orgs_ntee1_rev ON orgs(NTEE1, total_revenue);
        CREATE INDEX IF NOT EXISTS idx_orgs_rev ON orgs(total_revenue);
        CREATE INDEX IF NOT EXISTS idx_orgs_nteecc ON orgs(NTEECC);
    """)
    dest.execute("ANALYZE orgs")
    dest.commit()

    elapsed = time.time() - start
    size_mb = OUT_DB.stat().st_size / 1024 / 1024
    print(f"\nDone in {elapsed/60:.1f}m — {inserted:,} rows — {size_mb:.0f}MB → {OUT_DB}")

    src.close()
    dest.close()


if __name__ == "__main__":
    main()
