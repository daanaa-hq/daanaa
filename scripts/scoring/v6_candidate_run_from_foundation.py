#!/usr/bin/env python3
"""Generate a local, versioned five-tier v6 candidate ledger.

This writes only a new candidate run. It never updates registry_enriched and
never changes the active API/frontend output.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REGIONS = {
    **dict.fromkeys(("CT", "ME", "MA", "NH", "RI", "VT", "NJ", "NY", "PA"), "Northeast"),
    **dict.fromkeys(("IL", "IN", "MI", "OH", "WI", "IA", "KS", "MN", "MO", "NE", "ND", "SD"), "Midwest"),
    **dict.fromkeys(("DE", "FL", "GA", "MD", "NC", "SC", "VA", "WV", "AL", "KY", "MS", "TN", "AR", "LA", "OK", "TX"), "South"),
    **dict.fromkeys(("AZ", "CO", "ID", "MT", "NV", "NM", "UT", "WY", "AK", "CA", "HI", "OR", "WA"), "West"),
}
NATIONAL_CODES = {"DC", "AA", "AE", "AP", "AS", "FM", "GU", "MH", "MP", "PW", "PR", "VI"}


def geography(state):
    state = (state or "").strip().upper()
    if state in REGIONS:
        return "regional", REGIONS[state]
    if state in NATIONAL_CODES:
        return "national", state
    return "national", "Unknown"


def revenue_band(value):
    if value is None:
        return None
    value = float(value)
    if value <= 0:
        return None
    if value < 50_000:
        return "grassroots"
    if value < 200_000:
        return "small"
    if value < 500_000:
        return "mid"
    if value < 5_000_000:
        return "established"
    return "major"


def reserve(value):
    if value is None:
        return None
    value = float(value)
    return value if math.isfinite(value) and -120 <= value <= 120 else None


def add(groups, key, metric):
    item = groups[key]
    item[0] += 1
    if metric is not None:
        item[1] += 1
        item[2].append(metric)


def stats(item):
    values = sorted(item[2])
    if not values:
        return None, None, None
    return (
        statistics.median(values),
        values[max(0, int(len(values) * 0.25) - 1)],
        values[max(0, int(len(values) * 0.75) - 1)],
    )


def confidence(scoreable):
    if scoreable >= 30:
        return "high"
    if scoreable >= 10:
        return "limited"
    if scoreable >= 5:
        return "minimal"
    return "unavailable"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/merit_registry.db")
    parser.add_argument("--run-id", default="v6_foundation_candidate_20260727")
    args = parser.parse_args()

    db_path = Path(args.db).resolve()
    conn = sqlite3.connect(f"file:{db_path}?mode=rw", uri=True)
    conn.row_factory = sqlite3.Row
    if conn.execute("SELECT 1 FROM v6_scoring_runs WHERE run_id=?", (args.run_id,)).fetchone():
        raise SystemExit(f"run already exists: {args.run_id}")

    query = """
        SELECT EIN, NTEECC, STATE, merit_archetype_v5, total_revenue,
               months_of_reserve, latest_tax_year, nccs_data_year
        FROM registry_enriched
        WHERE deductibility='1'
          AND NOT (irs_revoked=1 OR org_status='revoked')
        ORDER BY EIN
    """
    groups = defaultdict(lambda: [0, 0, []])
    broad = defaultdict(lambda: [0, 0, []])
    ntee2_groups = defaultdict(lambda: [0, 0, []])
    national_groups = defaultdict(lambda: [0, 0, []])
    population = 0

    for row in conn.execute(query):
        population += 1
        ntee = (row["NTEECC"] or "").strip().upper()
        archetype = (row["merit_archetype_v5"] or "").strip().lower()
        scope, geo = geography(row["STATE"])
        band = revenue_band(row["total_revenue"])
        metric = reserve(row["months_of_reserve"])
        if not ntee or not archetype:
            continue
        add(broad, (ntee, scope, geo, archetype), metric)
        add(ntee2_groups, (ntee[:2], scope, geo, archetype), metric)
        add(national_groups, (ntee, "national", "US", archetype), metric)
        if band is not None:
            add(groups, (ntee, scope, geo, archetype, band), metric)

    criteria = {
        "methodology_version": "v6.1-foundation-candidate",
        "tiers": [
            "NTEECC+region+archetype+revenue_band",
            "NTEECC+region+archetype+conditional_bands",
            "NTEE2+region+archetype",
            "NTEECC+national+archetype",
            "archetype_only",
        ],
        "minimum_scoreable_peers": 5,
        "preferred_scoreable_peers": 30,
        "revenue_zero_is_unknown": True,
        "revoked_excluded": True,
        "source": "registry_enriched snapshot after normalized foundation backfill",
    }
    started = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO v6_scoring_runs
            (run_id, scorer_version, git_commit, input_snapshot, criteria_json,
             source_years, started_at, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            args.run_id,
            "v6.1-foundation-candidate",
            "local-uncommitted",
            datetime.now(timezone.utc).date().isoformat(),
            json.dumps(criteria, sort_keys=True),
            "latest_available",
            started,
            "in_progress",
            "Candidate only; not active API/frontend output.",
        ),
    )

    tiers = Counter()
    rows_to_insert = []
    for row in conn.execute(query):
        ntee = (row["NTEECC"] or "").strip().upper()
        archetype = (row["merit_archetype_v5"] or "").strip().lower()
        scope, geo = geography(row["STATE"])
        band = revenue_band(row["total_revenue"])
        metric = reserve(row["months_of_reserve"])
        year = row["latest_tax_year"] or row["nccs_data_year"]
        tier = "5_archetype_only"
        key = (archetype or "unknown",)
        item = None

        if ntee and archetype and band is not None:
            key = (ntee, scope, geo, archetype, band)
            candidate = groups[key]
            if candidate[1] - int(metric is not None) >= 5:
                tier = "1_direct"
                item = candidate

        if item is None and ntee and archetype and scope == "regional":
            key = (ntee, scope, geo, archetype)
            candidate = broad[key]
            if candidate[1] - int(metric is not None) >= 5:
                tier = "2_regional_conditional"
                item = candidate

        if item is None and ntee and archetype and scope == "regional":
            key = (ntee[:2], scope, geo, archetype)
            candidate = ntee2_groups[key]
            if candidate[1] - int(metric is not None) >= 5:
                tier = "3_broader_regional"
                item = candidate

        if item is None and ntee and archetype:
            key = (ntee, "national", "US", archetype)
            candidate = national_groups[key]
            if candidate[1] - int(metric is not None) >= 5:
                tier = "4_national"
                item = candidate

        if item is not None:
            peer_count = item[0] - int(tier == "1_direct")
            scoreable = item[1] - int(metric is not None and tier == "1_direct")
            median, p25, p75 = stats(item)
            group_key = "|".join(map(str, key))
            level = "nteecc" if ntee and tier != "3_broader_regional" else "ntee2"
        else:
            peer_count = 0
            scoreable = 0
            median = p25 = p75 = None
            group_key = f"archetype|{archetype or 'unknown'}"
            level = None

        tiers[tier] += 1
        rows_to_insert.append((
            args.run_id, row["EIN"], tier, "reported" if tier == "1_direct" else "inferred",
            int(tier != "1_direct"), group_key, group_key, peer_count, scoreable,
            median, p25, p75, (scoreable / peer_count if peer_count else 0),
            row["latest_tax_year"] or row["nccs_data_year"],
            row["latest_tax_year"] or row["nccs_data_year"],
            confidence(scoreable), "±10%" if scoreable >= 10 else "±15%",
            criteria["methodology_version"], level, ntee, scope, geo, band,
            "reported" if band is not None else None, tier, "months_of_reserve",
            metric, median, p25, p75,
        ))
        if len(rows_to_insert) >= 10000:
            conn.executemany(
                """
                INSERT INTO v6_peer_context_assignments (
                    run_id,EIN,tier,data_status,is_inferred,peer_group_key,
                    peer_group_description,peer_count,scoreable_peer_count,
                    median_reserves,p25_reserves,p75_reserves,metric_availability,
                    source_year_min,source_year_max,confidence,confidence_margin,
                    methodology_version,ntee_level,ntee_code,geography_scope,
                    geography_value,revenue_band,revenue_band_source,selected_tier,
                    metric_name,metric_value,peer_median,peer_p25,peer_p75
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                rows_to_insert,
            )
            rows_to_insert.clear()

    if rows_to_insert:
        conn.executemany(
            """
            INSERT INTO v6_peer_context_assignments (
                run_id,EIN,tier,data_status,is_inferred,peer_group_key,
                peer_group_description,peer_count,scoreable_peer_count,
                median_reserves,p25_reserves,p75_reserves,metric_availability,
                source_year_min,source_year_max,confidence,confidence_margin,
                methodology_version,ntee_level,ntee_code,geography_scope,
                geography_value,revenue_band,revenue_band_source,selected_tier,
                metric_name,metric_value,peer_median,peer_p25,peer_p75
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            rows_to_insert,
        )

    completed = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        UPDATE v6_scoring_runs
        SET completed_at=?, row_counts=?, status='candidate'
        WHERE run_id=?
        """,
        (completed, json.dumps(dict(tiers), sort_keys=True), args.run_id),
    )
    conn.commit()
    print(json.dumps({
        "run_id": args.run_id,
        "population": population,
        "tiers": dict(tiers),
        "status": "candidate",
    }, indent=2))
    conn.close()


if __name__ == "__main__":
    main()
