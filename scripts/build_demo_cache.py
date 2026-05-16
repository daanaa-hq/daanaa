import json, csv, os
from pathlib import Path

data_dir = Path("data")
cat_dir = data_dir / "categories"
cache_dir = data_dir / "propublica_cache"
csv_path = data_dir / "csv" / "master_orgs.csv"
MERIT_path = data_dir / "MERIT_cache.json"

MERIT = {}

# Load from category JSONs (richest source)
if cat_dir.exists():
    for f in cat_dir.glob("*.json"):
        try:
            with open(f) as fp:
                data = json.load(fp)
                items = data if isinstance(data, list) else data.get("orgs", [])
                for item in items:
                    ein = str(item.get("EIN") or item.get("ein") or "").strip().lstrip("0")
                    if not ein:
                        continue
                    MERIT[ein] = {
                        "score": float(item.get("MERIT_score") or 50),
                        "badges": item.get("badges", "Verified Active"),
                        "foundation_type": item.get("foundation_type", "Public Charity"),
                        "deductibility": item.get("deductibility", "Tax-Deductible"),
                        "propub_mission": item.get("propub_mission", ""),
                    }
        except Exception as e:
            print(f"[SKIP] {f}: {e}")

# Enrich from CSV for orgs not in categories
if csv_path.exists():
    with open(csv_path) as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            ein = str(row.get("ein") or row.get("EIN") or "").strip().lstrip("0")
            if not ein or ein in MERIT:
                continue
            score = 45
            if (row.get("revenue") or row.get("REVENUE")):
                score += 15
            if (row.get("ntee") or row.get("NTEE")):
                score += 10
            if (row.get("name") or row.get("NAME")):
                score += 10
            MERIT[ein] = {
                "score": min(score, 100),
                "badges": "Verified Active",
                "foundation_type": "Public Charity",
                "deductibility": "Tax-Deductible",
                "propub_mission": "",
            }

with open(MERIT_path, "w") as fp:
    json.dump(MERIT, fp)

print(f"[CACHE] {len(MERIT)} orgs enriched with MERIT data")
