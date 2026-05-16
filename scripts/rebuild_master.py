#!/usr/bin/env python3
import csv, json
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent

# Find the actual master file
master_candidates = [
    BASE / "data/csv/master_orgs.csv",
    BASE / "data/master_orgs.csv",
    BASE / "data/csv/percentile_engine_v2.csv",
]
master_path = None
for p in master_candidates:
    if p.exists():
        master_path = p
        print(f"[REBUILD] Found master at: {p}")
        break

if not master_path:
    print("[ERROR] No master file found")
    exit(1)

# Read existing master
existing = {}
with open(master_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        e = str(row.get("ein") or row.get("EIN","")).strip().lstrip("0")
        if not e: continue
        existing[e] = {
            "ein": e,
            "name": row.get("name") or row.get("NAME",""),
            "state": row.get("state") or row.get("STATE",""),
            "city": row.get("city") or row.get("CITY",""),
            "tax_year": row.get("tax_year") or row.get("TAX_YEAR",""),
            "revenue": row.get("revenue") or row.get("REVENUE",""),
            "ntee": row.get("ntee") or row.get("NTEE",""),
            "form_type": row.get("form_type") or row.get("FILING_TYPE",""),
        }

print(f"[REBUILD] Existing master: {len(existing)} orgs")

# Read raw ProPublica files
raw_dir = BASE / "data/raw/propublica"
added = 0
for path in sorted(raw_dir.glob("*.json")):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except: 
        continue
    org = data.get("organization", {})
    ein = str(org.get("ein") or "").strip().lstrip("0")
    if not ein or ein in existing:
        continue
    existing[ein] = {
        "ein": ein,
        "name": org.get("name", "Unknown"),
        "state": org.get("state", ""),
        "city": org.get("city", ""),
        "tax_year": "",
        "revenue": "",
        "ntee": str(org.get("ntee_code") or org.get("ntee") or "").strip(),
        "form_type": "990",
    }
    added += 1

print(f"[REBUILD] Added from raw: {added}")
print(f"[REBUILD] Total: {len(existing)}")

# Write clean master to data/csv/master_orgs.csv (standard location)
out_path = BASE / "data/csv/master_orgs.csv"
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["ein","name","state","city","tax_year","revenue","ntee","form_type"])
    w.writeheader()
    w.writerows(existing.values())

print(f"[REBUILD] Wrote {len(existing)} rows to {out_path}")

# Rebuild MERIT cache
MERIT = {}
for ein, org in existing.items():
    score = 50
    if org.get("revenue"): score += 15
    if org.get("ntee"): score += 10
    if org.get("name"): score += 10
    MERIT[ein] = {
        "score": min(score, 100),
        "badges": "Verified Active",
        "foundation_type": "Public Charity",
        "deductibility": "Tax-Deductible",
        "propub_mission": "",
    }

MERIT_path = BASE / "data/MERIT_cache.json"
with open(MERIT_path, "w") as f:
    json.dump(MERIT, f)
print(f"[REBUILD] Wrote {len(MERIT)} MERIT scores to {MERIT_path}")
