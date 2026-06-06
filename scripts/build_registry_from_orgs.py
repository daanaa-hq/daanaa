#!/usr/bin/env python3
"""
Rebuild merit_registry.db from 1M+ precomputed org JSON.gz files.
Source: precompute_output/orgs/EIN_prefix/EIN.json.gz
Output: data/merit_registry.db (registry_enriched table)

Run time: ~20-30 min for 1M orgs.
"""
import gzip, json, sqlite3, sys
from pathlib import Path
from datetime import datetime

ORGS_DIR = Path("precompute_output/orgs")
DB_PATH   = Path("data/merit_registry.db")
BATCH     = 5000

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS registry_enriched (
    EIN TEXT PRIMARY KEY,
    organization_name TEXT,
    NTEE1 TEXT,
    NTEECC TEXT,
    CITY TEXT,
    STATE TEXT,
    total_revenue REAL,
    ntee1_percentile REAL,
    ntee1_total_orgs INTEGER,
    source TEXT,
    revenue_band TEXT,
    peer_percentile REAL,
    peer_rank INTEGER,
    peer_total INTEGER,
    peer_group TEXT,
    latest_tax_year INTEGER,
    data_source TEXT,
    updated_at TEXT,
    merit_tier TEXT,
    merit_score REAL,
    merit_band TEXT,
    financial_health TEXT,
    months_of_reserve REAL,
    net_assets REAL,
    total_expenses REAL,
    employee_count INTEGER,
    program_expense_pct REAL,
    mission TEXT,
    mission_source TEXT,
    website TEXT,
    website_status TEXT,
    cause_tags TEXT,
    donate_url TEXT,
    donate_platform TEXT,
    donate_url_status TEXT,
    subsection TEXT DEFAULT '3',
    deductibility TEXT DEFAULT '1',
    is_hidden_gem INTEGER DEFAULT 0,
    ruling_date TEXT,
    zipcode TEXT,
    data_badges TEXT
);
"""

UPSERT_SQL = """
INSERT OR REPLACE INTO registry_enriched (
    EIN, organization_name, NTEE1, NTEECC, CITY, STATE,
    total_revenue, ntee1_percentile, ntee1_total_orgs, source,
    revenue_band, peer_percentile, peer_rank, peer_total, peer_group,
    latest_tax_year, data_source, updated_at,
    merit_tier, merit_score, merit_band, financial_health,
    months_of_reserve, net_assets, total_expenses, employee_count,
    program_expense_pct, mission, mission_source, website, website_status,
    cause_tags, donate_url, donate_platform, donate_url_status,
    subsection, deductibility, is_hidden_gem
) VALUES (
    :EIN, :organization_name, :NTEE1, :NTEECC, :CITY, :STATE,
    :total_revenue, :ntee1_percentile, :ntee1_total_orgs, :source,
    :revenue_band, :peer_percentile, :peer_rank, :peer_total, :peer_group,
    :latest_tax_year, :data_source, :updated_at,
    :merit_tier, :merit_score, :merit_band, :financial_health,
    :months_of_reserve, :net_assets, :total_expenses, :employee_count,
    :program_expense_pct, :mission, :mission_source, :website, :website_status,
    :cause_tags, :donate_url, :donate_platform, :donate_url_status,
    '3', '1', :is_hidden_gem
)
"""

def org_to_row(d: dict) -> dict:
    cause = d.get("cause_tags")
    if isinstance(cause, list):
        cause = json.dumps(cause)
    return {
        "EIN": d.get("EIN"),
        "organization_name": d.get("organization_name"),
        "NTEE1": d.get("NTEE1"),
        "NTEECC": d.get("NTEECC"),
        "CITY": d.get("CITY"),
        "STATE": d.get("STATE"),
        "total_revenue": d.get("total_revenue"),
        "ntee1_percentile": d.get("ntee1_percentile"),
        "ntee1_total_orgs": d.get("ntee1_total_orgs"),
        "source": d.get("source"),
        "revenue_band": d.get("revenue_band"),
        "peer_percentile": d.get("peer_percentile"),
        "peer_rank": d.get("peer_rank"),
        "peer_total": d.get("peer_total"),
        "peer_group": d.get("peer_group"),
        "latest_tax_year": d.get("latest_tax_year"),
        "data_source": d.get("data_source"),
        "updated_at": d.get("updated_at"),
        "merit_tier": d.get("merit_tier"),
        "merit_score": d.get("merit_score"),
        "merit_band": d.get("merit_band"),
        "financial_health": d.get("financial_health"),
        "months_of_reserve": d.get("months_of_reserve"),
        "net_assets": d.get("net_assets"),
        "total_expenses": d.get("total_expenses"),
        "employee_count": d.get("employee_count"),
        "program_expense_pct": d.get("program_expense_pct"),
        "mission": d.get("mission"),
        "mission_source": d.get("mission_source"),
        "website": d.get("website"),
        "website_status": d.get("website_status"),
        "cause_tags": cause,
        "donate_url": d.get("donate_url"),
        "donate_platform": d.get("donate_platform"),
        "donate_url_status": d.get("donate_url_status"),
        "is_hidden_gem": 1 if d.get("is_hidden_gem") else 0,
    }


def main():
    print(f"[{datetime.now():%H:%M:%S}] Rebuilding merit_registry.db from org files...")
    print(f"  Source: {ORGS_DIR}")
    print(f"  Target: {DB_PATH}")

    # Count files upfront for progress
    all_files = list(ORGS_DIR.rglob("*.json.gz"))
    total_files = len(all_files)
    print(f"  Files found: {total_files:,}")

    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("PRAGMA cache_size=-64000")   # 64MB cache
    con.execute(CREATE_SQL)

    # Preserve existing support tables if rebuilding
    con.execute("""CREATE TABLE IF NOT EXISTS score_snapshots
        (id INTEGER PRIMARY KEY, run_id TEXT, created_at TEXT, stats_json TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS scoring_runs
        (id INTEGER PRIMARY KEY, run_id TEXT, created_at TEXT, status TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS org_claims
        (id INTEGER PRIMARY KEY, EIN TEXT, claimed_at TEXT, status TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS waitlist
        (id INTEGER PRIMARY KEY, email TEXT, created_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS revoked_eins (EIN TEXT PRIMARY KEY)""")
    con.commit()

    inserted = 0
    errors = 0
    batch = []

    for i, path in enumerate(all_files):
        try:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                d = json.load(f)
            batch.append(org_to_row(d))
        except Exception as e:
            errors += 1
            continue

        if len(batch) >= BATCH:
            con.executemany(UPSERT_SQL, batch)
            con.commit()
            inserted += len(batch)
            batch = []

        if (i + 1) % 100_000 == 0:
            print(f"  [{datetime.now():%H:%M:%S}] {i+1:,}/{total_files:,} ({(i+1)/total_files*100:.1f}%) | inserted: {inserted:,}", flush=True)

    if batch:
        con.executemany(UPSERT_SQL, batch)
        con.commit()
        inserted += len(batch)

    print(f"\n[{datetime.now():%H:%M:%S}] Import complete!")
    count = con.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    print(f"  Rows in registry_enriched: {count:,}")
    print(f"  Errors skipped: {errors:,}")
    con.close()

    print(f"\nNext step: python3 scripts/build_fts_index.py")


if __name__ == "__main__":
    main()
