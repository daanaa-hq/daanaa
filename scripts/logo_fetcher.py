#!/usr/bin/env python3
import os, sys, json, time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import HTTPError

BASE = Path.home() / "meritgiving"
WEBSITE_FILE = BASE / "data" / "website_urls.json"
OUTPUT_FILE = BASE / "data" / "logo_urls.json"
SIZE = "medium"

def domain(url):
    if not url: return None
    try:
        p = urlparse(url if url.startswith("http") else f"http://{url}")
        d = p.netloc or p.path
        return d[4:].lower().strip("/") if d.startswith("www.") else d.lower().strip("/")
    except: return None

def check_logo(dom):
    if not dom: return None
    logo_url = f"https://logo.clearbit.com/{dom}?size={SIZE}"
    try:
        req = Request(logo_url, method="HEAD", headers={"User-Agent":"MeritGiving/1.0"})
        resp = urlopen(req, timeout=10)
        if resp.status == 200 and "image" in resp.headers.get("Content-Type",""):
            return logo_url
    except HTTPError as e:
        if e.code == 404:
            parts = dom.split(".")
            if len(parts) > 2:
                parent = ".".join(parts[-2:])
                if parent != dom: return check_logo(parent)
    except: pass
    return None

def main():
    print("MERIT Logo Fetcher")
    if not WEBSITE_FILE.exists():
        print(f"ERROR: {WEBSITE_FILE} not found. Run enrich_v2.py first."); sys.exit(1)
    with open(WEBSITE_FILE) as f: websites = json.load(f)
    print(f"Websites: {len(websites):,}")
    existing = {}
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f: existing = json.load(f)
        print(f"Existing: {len(existing):,}")
    logo_urls = dict(existing)
    fetched = failed = 0; t0 = time.time()
    items = [(e,u) for e,u in websites.items() if e not in existing]
    print(f"To do: {len(items):,}\n")
    for i, (ein, url) in enumerate(items):
        if i % 100 == 0 and i > 0:
            el = time.time()-t0; rate=i/el if el>0 else 0
            print(f"  {i:,}/{len(items):,} | Found:{fetched} | Fail:{failed} | {rate:.1f}/s")
        dom = domain(url)
        if not dom: failed += 1; continue
        time.sleep(0.1)
        lu = check_logo(dom)
        if lu: logo_urls[ein] = lu; fetched += 1
        else: failed += 1
    with open(OUTPUT_FILE, "w") as f: json.dump(logo_urls, f, indent=2)
    el = time.time()-t0
    print(f"\nDone | Found:{fetched} | Fail:{failed} | Time:{el/60:.1f}m")
    print(f"Saved: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
