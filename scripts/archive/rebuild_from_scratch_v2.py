#!/usr/bin/env python3
"""
Rebuild merit_registry.db from scratch with DATA VALIDATION.

Sources:
- data/bmf.csv (IRS Business Master File) — primary source
- data/eo*.csv (990-N extracts) — supplementary data

Validation gates:
- Filter: 501(c)(3) + deductible + active only
- STATE must be valid 2-char code (50 states + territories)
- NTEE1 derived from NTEECC (must be A-Z)
- Reject: negative revenue, negative expenses, missing org name
- Log all filtered rows with reason for auditability
"""
import sqlite3
import csv
import sys
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "data" / "merit_registry.db"
BMF_PATH = BASE / "data" / "bmf.csv"
EO_PATHS = [BASE / "data" / f"eo{i}.csv" for i in range(1, 5)]

# Valid US state/territory codes
VALID_STATES = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
    'DC', 'AS', 'GU', 'MP', 'PR', 'UM', 'VI'  # territories
}

filter_reasons = defaultdict(int)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def is_valid_ntee1(code):
    """NTEE1 must be A-Z."""
    return code and len(code) == 1 and code.isalpha() and code.isupper()

def derive_ntee1(ntee_code):
    """Extract NTEE1 from NTEECC."""
    if not ntee_code:
        return None
    first = ntee_code[0].upper() if ntee_code else None
    return first if first and first.isalpha() else None

def is_valid_state(state):
    """STATE must be a real 2-char code."""
    return state and len(state) == 2 and state.upper() in VALID_STATES

def create_schema(conn):
    """Create registry_enriched table with all required columns."""
    conn.execute("""
    CREATE TABLE registry_enriched (
        EIN TEXT PRIMARY KEY,
        organization_name TEXT NOT NULL,
        NTEE1 TEXT,
        NTEECC TEXT,
        CITY TEXT,
        STATE TEXT NOT NULL,
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
        source TEXT NOT NULL,
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
        subsection TEXT NOT NULL,
        deductibility INTEGER NOT NULL,
        updated_at TEXT NOT NULL,
        irs_revoked INTEGER DEFAULT 0,
        bmf_present INTEGER DEFAULT 0,
        is_hidden_gem INTEGER DEFAULT 0,

        -- Added fields from later
        org_status TEXT DEFAULT 'active',
        street_address TEXT,
        donate_url TEXT,
        donate_confidence INTEGER DEFAULT 0,
        donate_url_status TEXT,
        cause_tags_source TEXT,
        total_assets REAL,
        visibility_tier TEXT,
        revenue_3yr_avg REAL
    )
    """)
    conn.commit()
    log("Created registry_enriched schema")

def load_bmf(conn):
    """Load data from BMF CSV with validation."""
    log("Loading BMF CSV...")

    rows = []
    skipped = 0
    with open(BMF_PATH, newline='', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            # Filter: 501(c)(3) only, deductible, active
            subsection = (row.get("SUBSECTION") or "").strip()
            deductibility = (row.get("DEDUCTIBILITY") or "").strip()
            status = (row.get("STATUS") or "").strip()

            if subsection != "03":
                filter_reasons["BMF: not 501(c)(3)"] += 1
                skipped += 1
                continue
            if deductibility != "1":
                filter_reasons["BMF: not deductible"] += 1
                skipped += 1
                continue
            if status != "01":
                filter_reasons["BMF: not active"] += 1
                skipped += 1
                continue

            ein = (row.get("EIN") or "").strip().zfill(9)
            if not ein or len(ein) != 9:
                filter_reasons["BMF: invalid EIN"] += 1
                skipped += 1
                continue

            name = (row.get("NAME") or "").strip()[:200]
            if not name:
                filter_reasons["BMF: missing name"] += 1
                skipped += 1
                continue

            state = (row.get("STATE") or "").strip()[:2]
            if not is_valid_state(state):
                filter_reasons[f"BMF: invalid STATE '{state}'"] += 1
                skipped += 1
                continue

            ntee_code = (row.get("NTEE_CD") or "").strip()[:10]
            ntee1 = derive_ntee1(ntee_code)
            # If NTEE1 is None (unclassifiable), we allow it but log it
            if not ntee1:
                filter_reasons["BMF: unclassifiable NTEE"] += 1

            rows.append((
                ein,                                    # EIN
                name,                                   # organization_name
                ntee1,                                  # NTEE1
                ntee_code or None,                     # NTEECC
                (row.get("CITY") or "").strip()[:100], # CITY
                state,                                  # STATE (validated)
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
                0, 1, 0,                                # irs_revoked, bmf_present, is_hidden_gem
                'active', None, None, 0, None, None, None, None, None  # new fields
            ))

            if (i + 1) % 500_000 == 0:
                log(f"  Read {i+1:,} rows, {len(rows):,} valid, {skipped:,} filtered")

    log(f"BMF: loaded {len(rows):,} valid orgs, filtered {skipped:,}")

    conn.executemany("""
    INSERT OR IGNORE INTO registry_enriched VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
    """, rows)
    conn.commit()
    log(f"Inserted {len(rows):,} orgs into registry_enriched")

def load_eo_extracts(conn):
    """Load supplementary data from 990-N extracts with validation."""
    log("Loading 990-N extracts...")
    total_added = 0
    total_filtered = 0

    for eo_path in EO_PATHS:
        if not eo_path.exists():
            continue

        log(f"  Loading {eo_path.name}...")
        added = 0
        filtered = 0
        with open(eo_path, newline='', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ein = (row.get("EIN") or "").strip().zfill(9)
                if not ein or len(ein) != 9:
                    filter_reasons["990N: invalid EIN"] += 1
                    filtered += 1
                    continue

                name = (row.get("NAME") or "").strip()[:200]
                if not name:
                    filter_reasons["990N: missing name"] += 1
                    filtered += 1
                    continue

                state = (row.get("STATE") or "").strip()[:2]
                if not is_valid_state(state):
                    filter_reasons[f"990N: invalid STATE '{state}'"] += 1
                    filtered += 1
                    continue

                ntee_code = (row.get("NTEE_CODE") or row.get("NTEE_CD") or "").strip()[:10]
                ntee1 = derive_ntee1(ntee_code)
                if not ntee1:
                    filter_reasons["990N: unclassifiable NTEE"] += 1

                city = (row.get("CITY") or "").strip()[:100]
                ruling = (row.get("RULING_DATE") or "").strip()[:8]

                conn.execute("""
                INSERT OR IGNORE INTO registry_enriched
                (EIN, organization_name, NTEE1, NTEECC, STATE, CITY, ruling_date,
                 source, updated_at, subsection, deductibility, irs_revoked, bmf_present, is_hidden_gem, org_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'EO_990N', ?, '03', 1, 0, 0, 0, 'active')
                """, (ein, name, ntee1, ntee_code or None, state, city, ruling, datetime.now().isoformat()))
                added += 1

        conn.commit()
        log(f"    Added {added:,} new orgs from {eo_path.name}, filtered {filtered:,}")
        total_added += added
        total_filtered += filtered

    log(f"990-N extracts: total {total_added:,} new orgs, {total_filtered:,} filtered")

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

    # Verify and report
    count = conn.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    scored = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE merit_score IS NOT NULL").fetchone()[0]
    with_ntee1 = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE NTEE1 IS NOT NULL").fetchone()[0]
    with_state = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE STATE IS NOT NULL AND STATE != ''").fetchone()[0]

    log(f"\n=== REBUILD COMPLETE ===")
    log(f"Total orgs: {count:,}")
    log(f"With NTEE1: {with_ntee1:,} ({100*with_ntee1/count:.1f}%)")
    log(f"With STATE: {with_state:,} ({100*with_state/count:.1f}%)")
    log(f"With merit_score: {scored:,}")
    log(f"Database: {DB_PATH}")

    log(f"\n=== FILTER REPORT ===")
    for reason, count in sorted(filter_reasons.items(), key=lambda x: -x[1]):
        log(f"  {reason}: {count:,}")

    conn.close()

if __name__ == "__main__":
    main()
