#!/usr/bin/env python3
"""Read-only candidate audit for the agreed v6 regional peer model.

This script does not alter the catalog or v6 ledger. It excludes revoked records,
maps state addresses to four regions, places DC/territories/military/unknown
geographies in a national fallback, and reports candidate Tier 1/Tier 2/Tier 4
coverage. A future ledger writer should use the same grouping functions after
founder review.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


STATE_TO_REGION = {
    **dict.fromkeys(("CT", "ME", "MA", "NH", "RI", "VT", "NJ", "NY", "PA"), "Northeast"),
    **dict.fromkeys(("IL", "IN", "MI", "OH", "WI", "IA", "KS", "MN", "MO", "NE", "ND", "SD"), "Midwest"),
    **dict.fromkeys(("DE", "FL", "GA", "MD", "NC", "SC", "VA", "WV", "AL", "KY", "MS", "TN", "AR", "LA", "OK", "TX", "DC"), "South"),
    **dict.fromkeys(("AZ", "CO", "ID", "MT", "NV", "NM", "UT", "AK", "CA", "HI", "OR", "WA"), "West"),
}
MILITARY_CODES = {"AA", "AE", "AP"}
TERRITORY_CODES = {"AS", "FM", "GU", "MH", "MP", "PW", "PR", "VI"}


def geography_scope(state: str | None) -> tuple[str, str]:
    state = (state or "").strip().upper()
    if state in STATE_TO_REGION and state != "DC":
        return "regional", STATE_TO_REGION[state]
    if state == "DC":
        return "national", "District of Columbia"
    if state in MILITARY_CODES:
        return "national", "Military/Overseas"
    if state in TERRITORY_CODES:
        return "national", "Territory/Freely Associated"
    return "national", "Unknown geography"


def revenue_band(value: object) -> str | None:
    if value is None:
        return None
    amount = float(value)
    if amount < 0:
        return None
    # Treat a raw zero as unavailable until its provenance is confirmed.
    if amount == 0:
        return None
    if amount < 50_000:
        return "grassroots"
    if amount < 200_000:
        return "small"
    if amount < 500_000:
        return "mid"
    if amount < 5_000_000:
        return "established"
    return "major"


def valid_reserve(value: object) -> bool:
    return value is not None and -120 <= float(value) <= 120


@dataclass
class Group:
    count: int = 0
    scoreable: int = 0
    reserves: list[float] = field(default_factory=list)


def add_group(groups: dict[tuple[str, ...], Group], key: tuple[str, ...], reserve: object) -> None:
    group = groups[key]
    group.count += 1
    if valid_reserve(reserve):
        group.scoreable += 1
        group.reserves.append(float(reserve))


def load_rows(conn: sqlite3.Connection):
    return conn.execute(
        """
        SELECT EIN, NTEECC, STATE, merit_archetype_v5, total_revenue, months_of_reserve
        FROM registry_enriched
        WHERE deductibility = '1'
          AND NOT (irs_revoked = 1 OR org_status = 'revoked')
        ORDER BY EIN
        """
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/merit_registry.db")
    parser.add_argument("--report", default="/tmp/v6_regional_candidate_20260727.md")
    args = parser.parse_args()

    db_path = Path(args.db).resolve()
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    band_groups: dict[tuple[str, ...], Group] = defaultdict(Group)
    broad_groups: dict[tuple[str, ...], Group] = defaultdict(Group)
    population = 0
    dimensions = Counter()
    region_scopes = Counter()

    for row in load_rows(conn):
        population += 1
        ntee = (row["NTEECC"] or "").strip().upper()
        archetype = (row["merit_archetype_v5"] or "").strip().lower()
        scope, geography = geography_scope(row["STATE"])
        band = revenue_band(row["total_revenue"])
        dimensions["missing_nteecc"] += not bool(ntee)
        dimensions["missing_archetype"] += not bool(archetype)
        dimensions["known_revenue"] += band is not None
        dimensions["unknown_revenue"] += band is None
        region_scopes[f"{scope}:{geography}"] += 1
        if not ntee or not archetype or band is None:
            continue
        band_key = (ntee, scope, geography, archetype, band)
        broad_key = (ntee, scope, geography, archetype)
        add_group(band_groups, band_key, row["months_of_reserve"])
        add_group(broad_groups, broad_key, row["months_of_reserve"])

    tiers = Counter()
    statuses = Counter()
    scopes_by_tier: dict[str, Counter] = defaultdict(Counter)
    threshold_issues = Counter()

    for row in load_rows(conn):
        ntee = (row["NTEECC"] or "").strip().upper()
        archetype = (row["merit_archetype_v5"] or "").strip().lower()
        scope, geography = geography_scope(row["STATE"])
        band = revenue_band(row["total_revenue"])

        # No verified NTEE subcategory or archetype means no defensible peer cell.
        if not ntee or not archetype:
            tier = "4_Archetype_Only"
            status = "unavailable"
            threshold_issues["missing_peer_dimension"] += 1
        elif band is not None:
            group = band_groups[(ntee, scope, geography, archetype, band)]
            peer_count = group.count - 1
            scoreable = group.scoreable - int(valid_reserve(row["months_of_reserve"]))
            tier = "1_Direct_Regional" if scope == "regional" else "1_Direct_National"
            status = "direct"
            if peer_count < 5:
                threshold_issues["direct_limited_peers"] += 1
            if scoreable < 5:
                threshold_issues["direct_limited_metric_peers"] += 1
        else:
            # No revenue band is assigned. This is a broad peer cohort; the
            # eventual UI should show conditional band rows, not one invented band.
            group = broad_groups[(ntee, scope, geography, archetype)]
            peer_count = group.count
            scoreable = group.scoreable
            if peer_count >= 5 and scoreable >= 1:
                tier = "2_Regional_Inferred" if scope == "regional" else "2_National_Inferred"
                status = "inferred"
                if peer_count < 5:
                    threshold_issues["inferred_under5_peers"] += 1
                if scoreable < 5:
                    threshold_issues["inferred_limited_metric_peers"] += 1
            else:
                tier = "4_Archetype_Only"
                status = "unavailable"
                threshold_issues["insufficient_inferred_peers"] += 1

        tiers[tier] += 1
        statuses[status] += 1
        scopes_by_tier[tier][f"{scope}:{geography}"] += 1

    total = sum(tiers.values())
    lines = [
        "# v6 Regional Candidate Audit",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Source: `{db_path}` (read-only)",
        "",
        "This is a local candidate simulation. It does not write the catalog or v6 ledger.",
        "",
        "## Population",
        "",
        f"Active deductible organizations: **{population:,}**",
        f"Known revenue band: **{dimensions['known_revenue']:,}**",
        f"Revenue band unknown: **{dimensions['unknown_revenue']:,}**",
        f"Missing NTEECC: **{dimensions['missing_nteecc']:,}**",
        f"Missing archetype: **{dimensions['missing_archetype']:,}**",
        "",
        "## Candidate coverage",
        "",
        "| Tier | Count | Share |",
        "|---|---:|---:|",
    ]
    for tier, count in sorted(tiers.items()):
        lines.append(f"| `{tier}` | {count:,} | {100 * count / total:.2f}% |" if total else f"| `{tier}` | {count:,} | 0.00% |")
    lines.extend([
        f"| **Total** | **{total:,}** | **100.00%** |",
        "",
        "## Threshold review",
        "",
    ])
    for key, count in sorted(threshold_issues.items()):
        lines.append(f"- {key}: **{count:,}**")
    lines.extend([
        "",
        "## Rules used",
        "",
        "- 50 states map to Northeast, Midwest, South, or West.",
        "- DC, territories, military/overseas, and unknown geography use national fallback.",
        "- Revoked organizations are excluded from the population and peer groups.",
        "- Direct revenue records use a revenue band and a band-specific peer group.",
        "- Missing revenue records are not assigned a revenue band; their eventual display should be conditional by band.",
        "- Missing NTEECC or archetype receives no numeric peer context.",
        "- Tier 2 requires at least five peers and at least one scoreable reserve metric for candidate coverage; fewer than five scoreable metrics is marked limited for review.",
        "",
        "## Scope by tier",
        "",
    ])
    for tier in sorted(scopes_by_tier):
        lines.append(f"### `{tier}`")
        for scope, count in sorted(scopes_by_tier[tier].items()):
            lines.append(f"- {scope}: {count:,}")
    lines.append("")

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "population": population,
        "tiers": dict(tiers),
        "statuses": dict(statuses),
        "threshold_issues": dict(threshold_issues),
        "report": str(report_path),
    }, indent=2))
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
