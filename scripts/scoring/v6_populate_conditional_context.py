#!/usr/bin/env python3
"""Populate conditional revenue-band context for a candidate v6 run."""

from __future__ import annotations

import argparse
import sqlite3
from collections import defaultdict
from pathlib import Path

from v6_candidate_run_from_foundation import (
    add,
    confidence,
    geography,
    revenue_band,
    reserve,
    stats,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/merit_registry.db")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    db_path = Path(args.db).resolve()
    conn = sqlite3.connect(f"file:{db_path}?mode=rw", uri=True)
    conn.executescript(
        (Path(__file__).parents[1] / "migrations/011_v6_conditional_band_context.sql").read_text()
    )
    groups = defaultdict(lambda: [0, 0, []])
    years = defaultdict(list)
    query = """
        SELECT NTEECC, STATE, merit_archetype_v5, total_revenue,
               months_of_reserve, latest_tax_year, nccs_data_year
        FROM registry_enriched
        WHERE deductibility='1'
          AND NOT (irs_revoked=1 OR org_status='revoked')
    """
    for row in conn.execute(query):
        ntee = (row[0] or "").strip().upper()
        archetype = (row[2] or "").strip().lower()
        band = revenue_band(row[3])
        if not ntee or not archetype or band is None:
            continue
        scope, geo = geography(row[1])
        key = (ntee, scope, geo, archetype, band)
        add(groups, key, reserve(row[4]))
        if row[5] or row[6]:
            years[key].append(row[5] or row[6])

    rows = []
    for (ntee, scope, geo, archetype, band), item in groups.items():
        median, p25, p75 = stats(item)
        rows.append((
            args.run_id,
            "|".join((ntee, scope, geo, archetype)),
            ntee,
            scope,
            geo,
            archetype,
            band,
            item[0],
            item[1],
            median,
            p25,
            p75,
            min(years[(ntee, scope, geo, archetype, band)]) if years[(ntee, scope, geo, archetype, band)] else None,
            max(years[(ntee, scope, geo, archetype, band)]) if years[(ntee, scope, geo, archetype, band)] else None,
            confidence(item[1]),
            "v6.1-foundation-candidate",
        ))
    conn.executemany(
        """
        INSERT OR REPLACE INTO v6_conditional_band_context (
            run_id, peer_group_key, ntee_code, geography_scope, geography_value,
            archetype, revenue_band, peer_count, scoreable_peer_count,
            median_reserves, p25_reserves, p75_reserves, source_year_min,
            source_year_max, confidence, methodology_version
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )
    conn.commit()
    print(f"conditional_rows={len(rows)}")
    conn.close()


if __name__ == "__main__":
    main()
