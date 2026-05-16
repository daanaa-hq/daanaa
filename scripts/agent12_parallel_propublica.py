#!/usr/bin/env python3
import os, json, requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

PROPUBLICA_DIR = "data/propublica_cache"
os.makedirs(PROPUBLICA_DIR, exist_ok=True)

df = pd.read_csv("data/csv/final_profiles.csv", dtype=str)
df['EIN'] = df['EIN'].astype(str).str.replace('.0', '').str.strip()

cached = set()
if os.path.exists(PROPUBLICA_DIR):
    for f in os.listdir(PROPUBLICA_DIR):
        if f.endswith('.json'):
            cached.add(f.replace('.json', ''))

needed = [ein for ein in df['EIN'].tolist() if ein not in cached]
print(f"[AGENT 12] Need: {len(needed)} | Cached: {len(cached)}")

if len(needed) == 0:
    print("[AGENT 12] All done.")
    exit(0)

BASE_URL = "https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"

def fetch_org(ein):
    try:
        url = BASE_URL.format(ein=ein)
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            org = data.get('organization', {})
            payload = {
                'mission': org.get('mission', ''),
                'website': org.get('website', ''),
                'address': org.get('address', ''),
                'city': org.get('city', ''),
                'state': org.get('state', ''),
                'phone': org.get('phone', ''),
                'name': org.get('name', '')
            }
            with open(f"{PROPUBLICA_DIR}/{ein}.json", 'w', encoding='utf-8') as f:
                json.dump(payload, f)
            return (ein, True, "OK")
        elif r.status_code == 429:
            return (ein, False, "RATE_LIMITED")
        else:
            return (ein, False, f"HTTP_{r.status_code}")
    except Exception as e:
        return (ein, False, str(e)[:50])

MAX_WORKERS = 10
success = 0
failed = 0
rate_limited = 0

print(f"[AGENT 12] Starting {MAX_WORKERS} threads...")
start_time = time.time()

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    future_to_ein = {executor.submit(fetch_org, ein): ein for ein in needed}
    for future in as_completed(future_to_ein):
        ein, ok, msg = future.result()
        if ok:
            success += 1
        elif msg == "RATE_LIMITED":
            rate_limited += 1
        else:
            failed += 1
        
        total = success + failed + rate_limited
        if total % 100 == 0:
            elapsed = time.time() - start_time
            rate = total / elapsed if elapsed > 0 else 0
            print(f"[AGENT 12] {total}/{len(needed)} | OK:{success} Fail:{failed} RL:{rate_limited} | {rate:.1f}/s")

elapsed = time.time() - start_time
print(f"[AGENT 12] Done in {elapsed:.1f}s | OK:{success} Fail:{failed} RL:{rate_limited}")
