#!/usr/bin/env python3
"""
scripts/recompute_percentiles.py
Recompute MERIT peer percentiles using a 3-level hierarchy:
  Level 1: NTEECC + revenue_band  (exact subcategory + similar size)
  Level 2: NTEE1 + revenue_band   (broad category + similar size)
  Level 3: NTEE1                  (broad category, any size)

Uses the first level with ≥ MIN_PEER_GROUP orgs.
Also updates: state_ntee1_percentile (regional context).

Safe to re-run at any time — full recompute, not incremental.
"""

import sqlite3, json
from pathlib import Path
from datetime import datetime, timezone

DB_PATH  = Path.home() / "meritgiving" / "data" / "merit_registry.db"
NTEE_MAP = Path.home() / "meritgiving" / "ntee_map.json"

MIN_PEER_GROUP = 30   # minimum peers before we trust a group

REVENUE_BANDS = [
    ("Nano",   0,           25_000),
    ("Micro",  25_000,     100_000),
    ("Small",  100_000,    500_000),
    ("Medium", 500_000,  5_000_000),
    ("Large",  5_000_000, 50_000_000),
    ("Major",  50_000_000, float("inf")),
]

def revenue_band(rev):
    if rev is None or rev <= 0:
        return "Micro"
    for name, lo, hi in REVENUE_BANDS:
        if lo <= rev < hi:
            return name
    return "Major"


def run():
    ntee_map = json.loads(NTEE_MAP.read_text()) if NTEE_MAP.exists() else {}

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    now = datetime.now(timezone.utc).isoformat()

    print(f"[{now}] Recomputing MERIT percentiles with NTEECC + revenue bands...\n")

    # --- Ensure new columns exist ---
    existing_cols = {r[1] for r in db.execute("PRAGMA table_info(registry_enriched)").fetchall()}
    new_cols = {
        "revenue_band":    "TEXT",
        "peer_percentile": "REAL",
        "peer_rank":       "INTEGER",
        "peer_total":      "INTEGER",
        "peer_group":      "TEXT",
    }
    for col, typ in new_cols.items():
        if col not in existing_cols:
            db.execute(f"ALTER TABLE registry_enriched ADD COLUMN {col} {typ}")
            print(f"  Added column: {col}")
    db.commit()

    # --- Step 1: Assign revenue_band ---
    print("Step 1: computing revenue bands...")
    rows = db.execute("SELECT EIN, total_revenue FROM registry_enriched").fetchall()
    band_updates = [(revenue_band(r["total_revenue"]), r["EIN"]) for r in rows]
    db.executemany("UPDATE registry_enriched SET revenue_band = ? WHERE EIN = ?", band_updates)
    db.commit()

    from collections import Counter
    band_counts = Counter(b for b, _ in band_updates)
    for name, *_ in REVENUE_BANDS:
        print(f"  {name:<8}: {band_counts.get(name, 0):>8,}")
    print()

    # --- Step 2: Load all orgs into memory for peer-group computation ---
    print("Step 2: loading orgs for peer-group percentile computation...")
    orgs = db.execute("""
        SELECT EIN, NTEE1, NTEECC, total_revenue, revenue_band
        FROM registry_enriched
    """).fetchall()
    orgs = [dict(r) for r in orgs]
    total = len(orgs)
    print(f"  Loaded {total:,} orgs\n")

    # Build revenue index per peer group candidate
    # group_orgs[key] = sorted list of revenues for that group
    from collections import defaultdict
    import bisect

    def ntee1_of(code):
        if code and len(code) >= 1:
            return code[0].upper()
        return None

    # Collect revenues per group
    g_nteecc_band  = defaultdict(list)   # (NTEECC, band) → [revenues]
    g_ntee1_band   = defaultdict(list)   # (NTEE1,  band) → [revenues]
    g_ntee1        = defaultdict(list)   # (NTEE1,)       → [revenues]

    for o in orgs:
        rev   = o["total_revenue"] or 0
        band  = o["revenue_band"] or "Micro"
        ntee1 = o["NTEE1"] or "Z"
        nteecc = (o["NTEECC"] or "").strip()
        # normalise NTEECC to major-letter + 2-digit suffix (e.g. "B24", "A033"→"A03")
        if nteecc and len(nteecc) >= 2:
            letter = nteecc[0].upper()
            suffix = nteecc[1:]
            # pad/truncate suffix to 2 digits
            try:
                suffix = f"{int(suffix[:2]):02d}"
            except ValueError:
                suffix = suffix[:2]
            nteecc_norm = letter + suffix
        else:
            nteecc_norm = ""

        g_nteecc_band[(nteecc_norm, band)].append(rev)
        g_ntee1_band[(ntee1, band)].append(rev)
        g_ntee1[ntee1].append(rev)

    # Sort each group's revenue list for percentile lookup
    for d in (g_nteecc_band, g_ntee1_band, g_ntee1):
        for k in d:
            d[k].sort()

    def pct_rank(sorted_list, value):
        """PERCENT_RANK: fraction of peers with revenue ≤ value, scaled 0–100."""
        n = len(sorted_list)
        if n <= 1:
            return 50.0
        # index of first value > target → count of values ≤ target
        pos = bisect.bisect_right(sorted_list, value)
        return round(pos / n * 100, 1)

    def peer_rank_in(sorted_list, value):
        """1-based rank from top (higher revenue = rank 1)."""
        pos = bisect.bisect_right(sorted_list, value)
        return len(sorted_list) - pos + 1

    print("Step 3: assigning peer percentiles (3-level fallback)...")
    updates = []
    level_counts = [0, 0, 0, 0]   # L1, L2, L3, fallback

    for o in orgs:
        rev    = o["total_revenue"] or 0
        band   = o["revenue_band"] or "Micro"
        ntee1  = o["NTEE1"] or "Z"
        nteecc = (o["NTEECC"] or "").strip()

        if nteecc and len(nteecc) >= 2:
            letter = nteecc[0].upper()
            suffix = nteecc[1:]
            try:
                suffix = f"{int(suffix[:2]):02d}"
            except ValueError:
                suffix = suffix[:2]
            nteecc_norm = letter + suffix
        else:
            nteecc_norm = ""

        # Try L1: NTEECC + band
        key1 = (nteecc_norm, band)
        if nteecc_norm and len(g_nteecc_band.get(key1, [])) >= MIN_PEER_GROUP:
            sl = g_nteecc_band[key1]
            pct = pct_rank(sl, rev)
            rnk = peer_rank_in(sl, rev)
            grp = f"{nteecc_norm}:{band}"
            level_counts[0] += 1

        # Try L2: NTEE1 + band
        elif len(g_ntee1_band.get((ntee1, band), [])) >= MIN_PEER_GROUP:
            sl = g_ntee1_band[(ntee1, band)]
            pct = pct_rank(sl, rev)
            rnk = peer_rank_in(sl, rev)
            grp = f"{ntee1}:{band}"
            level_counts[1] += 1

        # Fallback L3: NTEE1 only
        elif len(g_ntee1.get(ntee1, [])) >= MIN_PEER_GROUP:
            sl = g_ntee1[ntee1]
            pct = pct_rank(sl, rev)
            rnk = peer_rank_in(sl, rev)
            grp = ntee1
            level_counts[2] += 1

        else:
            pct = None
            rnk = None
            grp = None
            level_counts[3] += 1

        updates.append((
            pct, rnk, len(sl) if grp else None, grp,
            o["EIN"]
        ))

    db.executemany("""
        UPDATE registry_enriched
        SET peer_percentile = ?,
            peer_rank       = ?,
            peer_total      = ?,
            peer_group      = ?
        WHERE EIN = ?
    """, updates)
    db.commit()

    print(f"  L1 (NTEECC+band):  {level_counts[0]:>8,}")
    print(f"  L2 (NTEE1+band):   {level_counts[1]:>8,}")
    print(f"  L3 (NTEE1):        {level_counts[2]:>8,}")
    print(f"  No group (<30):    {level_counts[3]:>8,}")
    print()

    # --- Step 4: Keep ntee1_percentile in sync (L3 value, broad compatibility) ---
    print("Step 4: updating ntee1_percentile (broad NTEE1 rank for API compat)...")
    db.execute("""
        UPDATE registry_enriched
        SET
            ntee1_percentile = pct.pct,
            ntee1_rank       = pct.rnk,
            ntee1_total_orgs = pct.total
        FROM (
            SELECT
                EIN,
                ROUND(PERCENT_RANK() OVER (
                    PARTITION BY COALESCE(NTEE1, 'Z')
                    ORDER BY COALESCE(total_revenue, 0)
                ) * 100, 1) AS pct,
                RANK() OVER (
                    PARTITION BY COALESCE(NTEE1, 'Z')
                    ORDER BY COALESCE(total_revenue, 0) DESC
                ) AS rnk,
                COUNT(*) OVER (
                    PARTITION BY COALESCE(NTEE1, 'Z')
                ) AS total
            FROM registry_enriched
        ) AS pct
        WHERE registry_enriched.EIN = pct.EIN
    """)
    db.commit()
    updated = db.execute(
        "SELECT COUNT(*) FROM registry_enriched WHERE ntee1_percentile IS NOT NULL"
    ).fetchone()[0]
    print(f"  {updated:,} rows with ntee1_percentile\n")

    # --- Step 5: State-level percentile within NTEE1 ---
    print("Step 5: updating state_ntee1_percentile...")
    db.execute("""
        UPDATE registry_enriched
        SET state_ntee1_percentile = pct.pct
        FROM (
            SELECT
                EIN,
                ROUND(PERCENT_RANK() OVER (
                    PARTITION BY COALESCE(STATE, 'ZZ'), COALESCE(NTEE1, 'Z')
                    ORDER BY COALESCE(total_revenue, 0)
                ) * 100, 1) AS pct
            FROM registry_enriched
        ) AS pct
        WHERE registry_enriched.EIN = pct.EIN
    """)
    db.commit()
    state_updated = db.execute(
        "SELECT COUNT(*) FROM registry_enriched WHERE state_ntee1_percentile IS NOT NULL"
    ).fetchone()[0]
    print(f"  {state_updated:,} rows with state percentile\n")

    # --- Step 6: Rebuild revenue_percentiles table ---
    print("Step 6: rebuilding revenue_percentiles table...")
    db.execute("DELETE FROM revenue_percentiles")
    db.execute("""
        INSERT INTO revenue_percentiles
            (EIN, NAME, NTEE1, STATE, CITY,
             total_revenue, ntee1_percentile, ntee1_rank, ntee1_total_orgs)
        SELECT
            EIN, organization_name, NTEE1, STATE, CITY,
            total_revenue, ntee1_percentile, ntee1_rank, ntee1_total_orgs
        FROM registry_enriched
        WHERE total_revenue > 0
    """)
    db.commit()
    rows = db.execute("SELECT COUNT(*) FROM revenue_percentiles").fetchone()[0]
    print(f"  {rows:,} rows in revenue_percentiles\n")

    # --- Step 7: Sanity check ---
    print("Step 7: sanity check — top orgs by peer_percentile...")
    top5 = db.execute("""
        SELECT organization_name, NTEECC, revenue_band, peer_group,
               ROUND(total_revenue,0) as rev, peer_percentile, peer_rank, peer_total
        FROM registry_enriched
        WHERE peer_percentile >= 99
        ORDER BY total_revenue DESC
        LIMIT 5
    """).fetchall()
    for r in top5:
        print(f"  {r[0][:40]:<40} | {r[1]:<6} {r[2]:<8} | grp={r[3]:<12} | ${r[4]:>12,.0f} | pct={r[5]} #{r[6]}/{r[7]}")

    # Peer group distribution
    dist = db.execute("""
        SELECT peer_group, COUNT(*) as cnt
        FROM registry_enriched
        WHERE peer_group IS NOT NULL
        GROUP BY peer_group
        ORDER BY cnt DESC
        LIMIT 10
    """).fetchall()
    print("\n  Largest peer groups:")
    for grp, cnt in dist:
        print(f"    {grp:<20} {cnt:>7,}")

    db.close()
    print(f"\nDone. Percentiles up to date as of {now}\n")


if __name__ == "__main__":
    run()
