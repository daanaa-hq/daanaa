#!/usr/bin/env python3
"""build_search_db.py — assemble the production search.db the droplet API serves.

The running droplet API (droplet_api.py) joins `org_fts s, registry_enriched o`
on `s.ein = o.EIN`. So the deployable search.db must carry BOTH tables:

  - registry_enriched : full registry (org detail fallback + browse/filter)
  - org_fts           : FTS5 index incl. metro + cause_tags (keyword search)

Both are copied from the canonical data/merit_registry.db so the artifact is
reproducible. Output is written to a temp path and integrity-checked before it
is fit to ship; the live file is never touched here (deploy is a separate,
gated step).

Usage:
    python3 scripts/build_search_db.py                 # -> /tmp/search_new.db
    python3 scripts/build_search_db.py --out /path.db
"""
import argparse
import os
import sqlite3
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "data", "merit_registry.db")

# Columns to carry in registry_enriched — exactly the set the LIVE droplet
# search.db ships (41 cols). Keeping parity holds the artifact near the live
# 1.2GB (the disk runs tight) and guarantees identical frontend behaviour; the
# new `metro` lives in org_fts (search), not here, so it is intentionally absent.
LIVE_COLS = [
    "EIN", "organization_name", "NTEE1", "NTEECC", "CITY", "STATE", "zipcode",
    "mission", "mission_source", "merit_score", "merit_tier", "merit_band",
    "ntee1_percentile", "peer_percentile", "peer_rank", "peer_total",
    "total_revenue", "total_expenses", "net_assets", "months_of_reserve",
    "program_expense_pct", "employee_count", "latest_tax_year", "ruling_date",
    "website", "website_status", "donate_url", "donate_platform",
    "donate_url_status", "cause_tags", "is_hidden_gem", "data_source", "source",
    "merit_archetype_v5", "merit_archetype_v5_label", "merit_band_v5",
    "merit_band_v5_label", "merit_score_v5", "merit_health_signal_v5",
    "merit_peer_group_v5", "merit_peer_count_v5",
]

# Indexes the API relies on (browse filters, FTS join, ordering). EIN PK comes
# with the table definition; these mirror the live db's coverage.
INDEXES = [
    "CREATE INDEX idx_orgs_ntee1     ON registry_enriched(NTEE1)",
    "CREATE INDEX idx_orgs_nteecc    ON registry_enriched(NTEECC)",
    "CREATE INDEX idx_orgs_state     ON registry_enriched(STATE)",
    "CREATE INDEX idx_orgs_score     ON registry_enriched(merit_score) WHERE merit_score IS NOT NULL",
    "CREATE INDEX idx_orgs_merit_tier ON registry_enriched(merit_tier)",
    "CREATE INDEX idx_orgs_hidden    ON registry_enriched(is_hidden_gem) WHERE is_hidden_gem = 1",
    "CREATE INDEX idx_orgs_rev       ON registry_enriched(total_revenue DESC)",
    "CREATE INDEX idx_orgs_ntee1_rev ON registry_enriched(NTEE1, total_revenue DESC)",
    "CREATE INDEX idx_orgs_state_city ON registry_enriched(STATE, CITY)",
    "CREATE INDEX idx_orgs_name      ON registry_enriched(organization_name)",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/search_new.db")
    args = ap.parse_args()

    if os.path.exists(args.out):
        os.remove(args.out)
    for ext in ("-wal", "-shm"):
        if os.path.exists(args.out + ext):
            os.remove(args.out + ext)

    t0 = time.time()
    db = sqlite3.connect(args.out, timeout=120)
    db.execute("PRAGMA journal_mode=OFF")
    db.execute("PRAGMA synchronous=OFF")
    db.execute("PRAGMA temp_store=MEMORY")
    db.execute(f"ATTACH DATABASE '{SRC}' AS src")

    # --- registry_enriched: live column set + full rows ---
    src_types = {r[1]: (r[2] or "TEXT")
                 for r in db.execute("PRAGMA src.table_info(registry_enriched)")}
    coldefs = []
    for c in LIVE_COLS:
        t = src_types.get(c, "TEXT")
        coldefs.append(f"{c} {t} PRIMARY KEY" if c == "EIN" else f"{c} {t}")
    db.execute(f"CREATE TABLE registry_enriched ({', '.join(coldefs)})")
    print("copying registry_enriched ...", flush=True)
    collist = ", ".join(LIVE_COLS)
    db.execute(f"INSERT INTO registry_enriched ({collist}) "
               f"SELECT {collist} FROM src.registry_enriched")
    db.commit()
    n_re = db.execute("SELECT count(*) FROM registry_enriched").fetchone()[0]
    print(f"  registry_enriched rows: {n_re:,}  ({time.time()-t0:.0f}s)", flush=True)

    print("building indexes ...", flush=True)
    for stmt in INDEXES:
        db.execute(stmt)
    db.commit()
    print(f"  indexes done ({time.time()-t0:.0f}s)", flush=True)

    # --- org_fts: same FTS5 definition + copied content ---
    create_fts = db.execute(
        "SELECT sql FROM src.sqlite_master WHERE type='table' AND name='org_fts'"
    ).fetchone()[0]
    db.execute(create_fts)
    print("copying org_fts ...", flush=True)
    db.execute(
        "INSERT INTO org_fts (ein, merit_tier, org_name, mission, city, state, "
        "metro, category, cause_tags) "
        "SELECT ein, merit_tier, org_name, mission, city, state, metro, category, "
        "cause_tags FROM src.org_fts"
    )
    db.commit()
    db.execute("INSERT INTO org_fts(org_fts) VALUES('optimize')")
    db.commit()
    n_fts = db.execute("SELECT count(*) FROM org_fts").fetchone()[0]
    print(f"  org_fts rows: {n_fts:,}  ({time.time()-t0:.0f}s)", flush=True)

    # --- verification ---
    print("verifying ...", flush=True)
    ok = db.execute("PRAGMA integrity_check").fetchone()[0]
    print(f"  integrity_check: {ok}")
    # join sanity (mirrors the API's search path)
    joined = db.execute(
        "SELECT COUNT(*) FROM org_fts s, registry_enriched o "
        "WHERE s.ein = o.EIN AND org_fts MATCH ?", ('food bank',)
    ).fetchone()[0]
    print(f"  sample join 'food bank': {joined:,} hits")
    metro_hits = db.execute(
        "SELECT COUNT(*) FROM org_fts WHERE org_fts MATCH ?", ('"Boston, MA"',)
    ).fetchone()[0]
    print(f"  metro 'Boston, MA' matches: {metro_hits:,}")
    db.close()

    size_gb = os.path.getsize(args.out) / 1e9
    print(f"\nDONE -> {args.out}  ({size_gb:.2f} GB, {time.time()-t0:.0f}s)")
    if ok != "ok":
        print("INTEGRITY FAILED — do not deploy", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
