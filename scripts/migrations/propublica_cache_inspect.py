import json, random
from pathlib import Path
from collections import Counter

d = Path.home() / "meritgiving/data/propublica_cache"
files = list(d.glob("*.json"))
print(f"Files: {len(files):,}")

sample = random.sample(files, min(5, len(files)))
keys = Counter()

for f in sample:
    data = json.load(open(f))
    print(f"\n--- {f.stem} ---")
    print(f"Top keys: {list(data.keys())}")
    org = data.get("organization", {})
    print(f"Org keys: {list(org.keys())}")
    for k, v in org.items():
        if v: print(f"  {k}: {str(v)[:80]}")

print("\n--- Scanning 1000 files for key frequency ---")
for f in random.sample(files, min(1000, len(files))):
    try: keys.update(json.load(open(f, errors="ignore")).get("organization", {}).keys())
    except: pass

for k, c in keys.most_common(30):
    print(f"  {k}: {c}")
