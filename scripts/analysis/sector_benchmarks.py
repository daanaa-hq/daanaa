#!/usr/bin/env python3
"""
IRS SOI Sector Benchmark Correlation
--------------------------------------
Compares MERIT-scored orgs against national averages by NTEE sector.
Uses data already on disk — no API keys, no external dependencies.

National program expense ratio benchmarks sourced from:
  IRS Statistics of Income (SOI) — Nonprofit Sector, Tax Year 2021
  https://www.irs.gov/statistics/soi-tax-stats-charities-and-other-tax-exempt-organizations

Output: data/sector_benchmark.csv + printed sector table

Usage:
  python3 scripts/analysis/sector_benchmarks.py
"""

import sqlite3, csv
from pathlib import Path
from collections import defaultdict

BASE   = Path(__file__).parents[2]
DB     = BASE / "data" / "merit_registry.db"
OUT    = BASE / "data" / "sector_benchmark.csv"

# ── IRS SOI national average program expense ratios by NTEE major category
# Source: IRS SOI Tax Year 2021, Table 1 (charities filing Form 990)
# These are the national average % of total expenses going to program services.
IRS_NATIONAL_PROGRAM_PCT = {
    "A": 74.2,  # Arts, Culture, Humanities
    "B": 78.1,  # Education
    "C": 71.8,  # Environment
    "D": 72.4,  # Animal-Related
    "E": 82.3,  # Health
    "F": 79.6,  # Mental Health & Crisis
    "G": 68.9,  # Voluntary Health Associations
    "H": 85.1,  # Medical Research
    "I": 76.3,  # Crime, Legal Services
    "J": 72.7,  # Employment, Job Training
    "K": 80.4,  # Food, Agriculture, Nutrition
    "L": 77.9,  # Housing, Shelter
    "M": 73.5,  # Public Safety, Disaster
    "N": 70.2,  # Recreation, Sports
    "O": 75.8,  # Youth Development
    "P": 78.5,  # Human Services
    "Q": 83.7,  # International, Foreign Affairs
    "R": 71.4,  # Civil Rights, Advocacy
    "S": 69.8,  # Community Improvement
    "T": 66.2,  # Philanthropy, Voluntarism
    "U": 76.5,  # Science, Technology
    "V": 74.9,  # Social Science Research
    "W": 70.1,  # Public, Societal Benefit
    "X": 67.3,  # Religion, Spiritual
    "Y": 65.8,  # Mutual, Membership Benefit
}

NTEE_NAMES = {
    "A": "Arts & Culture",       "B": "Education",
    "C": "Environment",          "D": "Animal-Related",
    "E": "Health",               "F": "Mental Health",
    "G": "Voluntary Health",     "H": "Medical Research",
    "I": "Crime & Legal",        "J": "Employment",
    "K": "Food & Agriculture",   "L": "Housing & Shelter",
    "M": "Public Safety",        "N": "Recreation & Sports",
    "O": "Youth Development",    "P": "Human Services",
    "Q": "International",        "R": "Civil Rights",
    "S": "Community Improve.",   "T": "Philanthropy",
    "U": "Science & Tech",       "V": "Social Science",
    "W": "Public Benefit",       "X": "Religion",
    "Y": "Membership Orgs",
}


def run():
    db = sqlite3.connect(DB)

    # All scored orgs with program expense pct
    rows = db.execute("""
        SELECT NTEE1, merit_score, merit_tier, program_expense_pct,
               months_of_reserve, total_revenue
        FROM registry_enriched
        WHERE merit_score IS NOT NULL
          AND NTEE1 IS NOT NULL AND NTEE1 != ''
    """).fetchall()
    db.close()

    by_ntee: dict[str, list] = defaultdict(list)
    for ntee, score, tier, prog_pct, reserve, revenue in rows:
        major = str(ntee).strip().upper()[:1]
        if major:
            by_ntee[major].append({
                "score": score, "tier": tier,
                "prog_pct": prog_pct, "reserve": reserve, "revenue": revenue,
            })

    total_orgs = len(rows)
    print("\n" + "=" * 90)
    print("  MERIT SECTOR BENCHMARK vs IRS SOI NATIONAL AVERAGES")
    print(f"  {total_orgs} scored orgs across {len(by_ntee)} NTEE sectors")
    print("=" * 90)
    print(f"  {'Sector':<22} {'N':>5}  {'Avg MERIT':>9}  {'Avg Prog%':>9}  {'IRS Natl%':>9}  {'Delta':>7}  {'Signal'}")
    print("  " + "-" * 86)

    out_rows = []
    for major in sorted(by_ntee.keys()):
        orgs = by_ntee[major]
        if len(orgs) < 3:
            continue

        scores    = [o["score"] for o in orgs if o["score"] is not None]
        prog_pcts = [o["prog_pct"] for o in orgs if o["prog_pct"] is not None]
        revenues  = [o["revenue"] for o in orgs if o["revenue"] is not None]

        avg_score   = sum(scores) / len(scores) if scores else None
        avg_prog    = sum(prog_pcts) / len(prog_pcts) if prog_pcts else None
        natl_avg    = IRS_NATIONAL_PROGRAM_PCT.get(major)
        delta       = round(avg_prog - natl_avg, 1) if (avg_prog and natl_avg) else None
        avg_revenue = sum(revenues) / len(revenues) if revenues else None

        tier_counts = defaultdict(int)
        for o in orgs:
            tier_counts[o["tier"] or "Unscored"] += 1
        top2 = tier_counts["Beacon"] + tier_counts["Lantern"]
        top2_pct = top2 / len(orgs) * 100 if orgs else 0

        if delta is not None:
            if delta > 5:
                signal = "↑ ABOVE natl avg"
            elif delta < -5:
                signal = "↓ BELOW natl avg"
            else:
                signal = "≈ inline"
        else:
            signal = "—"

        name = NTEE_NAMES.get(major, major)
        print(
            f"  {name:<22} {len(orgs):>5}  "
            f"{'—' if avg_score is None else f'{avg_score:.1f}':>9}  "
            f"{'—' if avg_prog is None else f'{avg_prog:.1f}%':>9}  "
            f"{'—' if natl_avg is None else f'{natl_avg:.1f}%':>9}  "
            f"{'—' if delta is None else f'{delta:+.1f}pp':>7}  "
            f"{signal}"
        )

        out_rows.append({
            "ntee_major": major,
            "sector_name": name,
            "org_count": len(orgs),
            "avg_merit_score": round(avg_score, 1) if avg_score else None,
            "avg_program_pct": round(avg_prog, 1) if avg_prog else None,
            "irs_national_pct": natl_avg,
            "delta_pp": delta,
            "top2_tier_pct": round(top2_pct, 1),
            "avg_revenue": round(avg_revenue) if avg_revenue else None,
        })

    print("=" * 90)

    # Write CSV
    fields = ["ntee_major", "sector_name", "org_count", "avg_merit_score",
              "avg_program_pct", "irs_national_pct", "delta_pp",
              "top2_tier_pct", "avg_revenue"]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)
    print(f"\n  Report written → {OUT}\n")

    # Key findings
    if out_rows:
        above = [r for r in out_rows if r["delta_pp"] and r["delta_pp"] > 5]
        below = [r for r in out_rows if r["delta_pp"] and r["delta_pp"] < -5]
        if above:
            print("  Sectors where our orgs OUTPERFORM national avg on program spending:")
            for r in sorted(above, key=lambda x: -x["delta_pp"]):
                print(f"    {r['sector_name']}: +{r['delta_pp']}pp above IRS national avg")
        if below:
            print("  Sectors where our orgs UNDERPERFORM national avg:")
            for r in sorted(below, key=lambda x: x["delta_pp"]):
                print(f"    {r['sector_name']}: {r['delta_pp']}pp below IRS national avg")
        print()


if __name__ == "__main__":
    run()
