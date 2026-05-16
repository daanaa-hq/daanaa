import json, random
from pathlib import Path
d = Path.home() / "meritgiving/data/propublica_cache"
files = list(d.glob("*.json"))
f = random.choice(files)
data = json.load(open(f))
print(f"=== EIN: {f.stem} ===")
filings = data.get("filings_with_data", [])
print(f"Filings: {len(filings)}")
if filings:
    print(f"Filing keys: {list(filings[0].keys())}")
    for k,v in filings[0].items(): print(f"  {k}: {str(v)[:100]}")
# Search for URLs anywhere
def find_urls(obj, path=""):
    urls = []
    if isinstance(obj, dict):
        for k,v in obj.items():
            p = f"{path}.{k}" if path else k
            if isinstance(v, str) and ("http" in v or ".org" in v or ".com" in v) and len(v) < 200:
                urls.append((p, v))
            elif isinstance(v, (dict, list)): urls.extend(find_urls(v, p))
    elif isinstance(obj, list):
        for i,item in enumerate(obj): urls.extend(find_urls(item, f"{path}[{i}]"))
    return urls
urls = find_urls(data)
print(f"\nURLs found: {len(urls)}")
for p,v in urls[:10]: print(f"  {p}: {v}")
