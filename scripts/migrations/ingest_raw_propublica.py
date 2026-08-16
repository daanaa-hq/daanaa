#!/usr/bin/env python3
import json, csv
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
RAW_DIR = BASE / "data/raw/propublica"
MASTER_CSV = BASE / "data/csv/master_orgs.csv"
MERIT_JSON = BASE / "data/MERIT_cache.json"

existing = set()
if MASTER_CSV.exists():
    with open(MASTER_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            e = str(row.get("ein") or row.get("EIN","")).strip().lstrip("0")
            if e: existing.add(e)

print(f"[INGEST] Existing: {len(existing)} | Raw files: {len(list(RAW_DIR.glob('*.json')))}")

new_orgs = []
new_MERIT = {}
for path in sorted(RAW_DIR.glob("*.json")):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except: 
        continue
    org = data.get("organization", {})
    ein = str(org.get("ein") or "").strip().lstrip("0")
    if not ein or ein in existing:
        continue
    name = org.get("name", "Unknown")
    city = org.get("city", "")
    state = org.get("state", "")
    ntee = str(org.get("ntee_code") or org.get("ntee") or "").strip()
    mission = org.get("mission", "") or ""
    filings = data.get("filings_with_data", []) or []
    score = 50 + (20 if filings else 0) + (10 if mission else 0) + (10 if ntee else 0)
    new_orgs.append({
        "ein": ein, "name": name, "city": city, "state": state,
        "tax_year": "", "revenue": "", "ntee": ntee, "form_type": "990",
        "record_status": "Active", "source_provenance": "ProPublica",
        "updated_at": datetime.now().isoformat(),
    })
    new_MERIT[ein] = {
        "score": min(score, 100), "badges": "Verified Active|Newly Ingested",
        "foundation_type": "Public Charity", "deductibility": "Tax-Deductible",
        "propub_mission": mission[:500],
    }

if new_orgs:
    with open(MASTER_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(new_orgs[0].keys()))
        w.writerows(new_orgs)
    print(f"[INGEST] Added {len(new_orgs)} new orgs")

old_MERIT = {}
if MERIT_JSON.exists():
    with open(MERIT_JSON, "r") as f:
        old_MERIT = json.load(f)
old_MERIT.update(new_MERIT)
with open(MERIT_JSON, "w") as f:
    json.dump(old_MERIT, f)
print(f"[INGEST] Total MERIT scores: {len(old_MERIT)}")
