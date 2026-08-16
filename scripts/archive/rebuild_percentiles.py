#!/usr/bin/env python3
"""
MERIT Percentile Engine Rebuilder
Recalculates peer percentiles after data enrichment.
"""

import csv, math
from collections import defaultdict
from pathlib import Path

BASE = Path.home() / "meritgiving"
MASTER_CSV = BASE / "data" / "csv" / "master_orgs.csv"
OUTPUT_CSV = BASE / "data" / "csv" / "percentile_engine_v3.csv"

def safe_float(val):
    if val is None: return 0.0
    try:
        v = float(val)
        return 0.0 if math.isnan(v) or math.isinf(v) else v
    except:
        return 0.0

def load_orgs():
    orgs = []
    with open(MASTER_CSV, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            orgs.append(row)
    return orgs

def calculate_percentiles(orgs):
    """Calculate percentiles within each NTEE major + state cohort."""

    # Group by NTEE major category
    cohorts = defaultdict(list)
    for org in orgs:
        ntee = str(org.get("NTEE", "")).strip()
        major = ntee[0].upper() if ntee else "Z"
        cohorts[major].append(org)

    # Calculate percentiles for revenue and assets within each cohort
    for major, group in cohorts.items():
        # Revenue percentiles
        revenues = [(i, safe_float(org.get("REVENUE"))) for i, org in enumerate(group)]
        revenues_sorted = sorted(revenues, key=lambda x: x[1])
        n = len(revenues_sorted)
        for rank, (orig_idx, rev) in enumerate(revenues_sorted):
            pct = (rank / (n - 1)) * 100 if n > 1 else 50.0
            group[orig_idx]["REVENUE_PERCENTILE"] = round(pct, 1)

        # Asset percentiles
        assets = [(i, safe_float(org.get("TOTAL_ASSETS"))) for i, org in enumerate(group)]
        assets_sorted = sorted(assets, key=lambda x: x[1])
        n = len(assets_sorted)
        for rank, (orig_idx, ast) in enumerate(assets_sorted):
            pct = (rank / (n - 1)) * 100 if n > 1 else 50.0
            group[orig_idx]["ASSETS_PERCENTILE"] = round(pct, 1)

    # Flatten back
    result = []
    for group in cohorts.values():
        result.extend(group)
    return result

def write_percentile_csv(orgs):
    fieldnames = ["EIN", "NAME", "STATE", "CITY", "NTEE", "YEAR", "REVENUE", 
                  "TOTAL_EXPENSES", "PROGRAM_EXPENSES", "ADMIN_EXPENSES",
                  "NET_ASSETS", "TOTAL_ASSETS", "EMPLOYEES", "VOLUNTEERS",
                  "REVENUE_PERCENTILE", "ASSETS_PERCENTILE"]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for org in orgs:
            row = {k: org.get(k, "") for k in fieldnames}
            writer.writerow(row)

    print(f"Wrote {len(orgs)} orgs to {OUTPUT_CSV}")

if __name__ == "__main__":
    print("Loading orgs...")
    orgs = load_orgs()
    print(f"Loaded {len(orgs)} rows")

    print("Calculating percentiles...")
    orgs = calculate_percentiles(orgs)

    print("Writing output...")
    write_percentile_csv(orgs)

    print("Done!")
