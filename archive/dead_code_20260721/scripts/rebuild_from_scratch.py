#!/usr/bin/env python3
"""
Rebuild merit_registry.db from scratch using:
- data/bmf.csv (IRS Business Master File) — primary source
- data/eo*.csv (990-N extracts) — supplementary data
- v4 scoring via merit_scorer_v4_0.py

Creates a clean, valid registry_enriched with all required columns.
"""
import sqlite3
import csv
import sys
import os
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "data" / "merit_registry.db"
BMF_PATH = BASE / "data" / "bmf.csv"
EO_PATHS = [BASE / "data" / f"eo{i}.csv" for i in range(1, 5)]

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def create_schema(conn):
    """Create registry_enriched table with all required columns."""
    conn.execute("""
    CREATE TABLE registry_enriched (
        EIN TEXT PRIMARY KEY,
        organization_name TEXT,
        NTEE1 TEXT,
        NTEECC TEXT,
        CITY TEXT,
        STATE TEXT,
        zipcode TEXT,
        address TEXT,
        total_revenue REAL,
        total_expenses REAL,
        net_assets REAL,
        total_liabilities REAL,
        months_of_reserve REAL,
        employee_count INTEGER,
        program_expense_pct REAL,
        ruling_date TEXT,
        latest_tax_year INTEGER,
        nccs_year INTEGER,

        -- Peer group info
        ntee1_percentile REAL,
        ntee1_total_orgs INTEGER,
        peer_group TEXT,
        peer_percentile REAL,
        peer_rank INTEGER,
        peer_total INTEGER,
        revenue_band TEXT,

        -- Mission & web
        mission TEXT,
        mission_source TEXT,
        website TEXT,
        website_status TEXT,

        -- Categorization
        cause_tags TEXT,
        activ1 TEXT,
        activ2 TEXT,
        activ3 TEXT,
        source TEXT,
        data_source TEXT,

        -- v4 scoring
        merit_score REAL,
        merit_tier TEXT,
        merit_band TEXT,
        financial_health TEXT,

        -- v5 scoring (populated by scorer if available)
        merit_archetype_v5 TEXT,
        merit_archetype_v5_label TEXT,
        merit_band_v5_label TEXT,
        merit_score_v5 REAL,
        merit_health_signal_v5 TEXT,
        merit_peer_group_v5 TEXT,
        merit_peer_count_v5 INTEGER,

        -- Status tracking
        subsection TEXT,
        deductibility INTEGER,
        updated_at TEXT,
        irs_revoked INTEGER DEFAULT 0,
        bmf_present INTEGER DEFAULT 0,
        is_hidden_gem INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    log("Created registry_enriched schema")

def load_bmf(conn):
    """Load data from BMF CSV."""
    log("Loading BMF CSV...")

    def ntee1(code):
        return code[0].upper() if code and code[0].isalpha() else None

    rows = []
    skipped = 0
    with open(BMF_PATH, newline='', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            # Filter: 501(c)(3) only, deductible, active
            subsection = (row.get("SUBSECTION") or "").strip()
            deductibility = (row.get("DEDUCTIBILITY") or "").strip()
            status = (row.get("STATUS") or "").strip()

            if subsection != "03" or deductibility != "1" or status != "01":
                skipped += 1
                continue

            ein = (row.get("EIN") or "").strip().zfill(9)
            if not ein or len(ein) != 9:
                skipped += 1
                continue

            name = (row.get("NAME") or "").strip()[:200]
            if not name:
                skipped += 1
                continue

            ntee_code = (row.get("NTEE_CD") or "").strip()[:10]

            rows.append((
                ein,                                    # EIN
                name,                                   # organization_name
                ntee1(ntee_code),                      # NTEE1
                ntee_code or None,                     # NTEECC
                (row.get("CITY") or "").strip()[:100], # CITY
                (row.get("STATE") or "").strip()[:2],  # STATE
                (row.get("ZIP") or "").strip()[:10],   # zipcode
                None,                                   # address (backfilled later)
                None,                                   # total_revenue
                None,                                   # total_expenses
                None,                                   # net_assets
                None,                                   # total_liabilities
                None,                                   # months_of_reserve
                None,                                   # employee_count
                None,                                   # program_expense_pct
                (row.get("RULING") or "").strip()[:8],# ruling_date
                None,                                   # latest_tax_year
                None,                                   # nccs_year
                None,                                   # ntee1_percentile
                None,                                   # ntee1_total_orgs
                None,                                   # peer_group
                None,                                   # peer_percentile
                None,                                   # peer_rank
                None,                                   # peer_total
                None,                                   # revenue_band
                None,                                   # mission
                None,                                   # mission_source
                None,                                   # website
                None,                                   # website_status
                None,                                   # cause_tags
                None, None, None,                      # activ1, 2, 3
                'IRS_BMF',                              # source
                None,                                   # data_source
                None, None, None, None,                # merit fields
                None, None, None, None, None, None, None,  # v5 fields
                subsection,                             # subsection
                int(deductibility),                     # deductibility
                datetime.now().isoformat(),             # updated_at
                0, 1, 0                                 # irs_revoked, bmf_present, is_hidden_gem
            ))

            if (i + 1) % 500_000 == 0:
                log(f"  Read {i+1:,} rows, {len(rows):,} valid, {skipped:,} skipped")

    log(f"BMF: loaded {len(rows):,} valid orgs, skipped {skipped:,}")

    conn.executemany("""
    INSERT OR IGNORE INTO registry_enriched VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
    """, rows)
    conn.commit()
    log(f"Inserted {len(rows):,} orgs into registry_enriched")

def load_eo_extracts(conn):
    """Load supplementary data from 990-N extracts."""
    log("Loading 990-N extracts...")
    total_added = 0

    for eo_path in EO_PATHS:
        if not eo_path.exists():
            continue

        log(f"  Loading {eo_path.name}...")
        added = 0
        with open(eo_path, newline='', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ein = (row.get("EIN") or "").strip().zfill(9)
                if not ein or len(ein) != 9:
                    continue

                # Try to update existing or insert if new
                name = (row.get("NAME") or "").strip()[:200]
                ntee_code = (row.get("NTEE_CODE") or row.get("NTEE_CD") or "").strip()[:10]
                state = (row.get("STATE") or "").strip()[:2]
                city = (row.get("CITY") or "").strip()[:100]
                ruling = (row.get("RULING_DATE") or "").strip()[:8]

                if name:
                    conn.execute("""
                    INSERT OR IGNORE INTO registry_enriched
                    (EIN, organization_name, NTEE1, NTEECC, STATE, CITY, ruling_date,
                     source, updated_at, deductibility, irs_revoked, bmf_present, is_hidden_gem)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'EO_990N', ?, 1, 0, 0, 0)
                    """, (ein, name,
                          ntee_code[0].upper() if ntee_code and ntee_code[0].isalpha() else None,
                          ntee_code or None, state, city, ruling,
                          datetime.now().isoformat()))
                    added += 1

        conn.commit()
        log(f"    Added {added:,} new orgs from {eo_path.name}")
        total_added += added

    log(f"990-N extracts: total {total_added:,} new orgs")

def create_indexes(conn):
    """Create performance indexes."""
    log("Creating indexes...")
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_state ON registry_enriched(STATE)",
        "CREATE INDEX IF NOT EXISTS idx_ntee1 ON registry_enriched(NTEE1)",
        "CREATE INDEX IF NOT EXISTS idx_revenue ON registry_enriched(total_revenue)",
        "CREATE INDEX IF NOT EXISTS idx_score ON registry_enriched(merit_score DESC)",
        "CREATE INDEX IF NOT EXISTS idx_hidden ON registry_enriched(is_hidden_gem)",
        "CREATE INDEX IF NOT EXISTS idx_ntee1_rev ON registry_enriched(NTEE1, total_revenue)",
        "CREATE INDEX IF NOT EXISTS idx_deduct ON registry_enriched(deductibility)",
    ]
    for idx_sql in indexes:
        conn.execute(idx_sql)
    conn.commit()
    log("Indexes created")

def main():
    if DB_PATH.exists():
        log(f"Removing existing {DB_PATH}")
        DB_PATH.unlink()

    log("Creating new database...")
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    create_schema(conn)
    load_bmf(conn)
    load_eo_extracts(conn)
    create_indexes(conn)

    # Verify
    count = conn.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    log(f"\n=== REBUILD COMPLETE ===")
    log(f"Total orgs: {count:,}")
    log(f"Database: {DB_PATH}")

    conn.close()

if __name__ == "__main__":
    main()
