#!/usr/bin/env python3
import os, csv, json, time, sys, glob
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from socket import timeout as TimeoutError

CACHE_DIR = "data/propublica_cache"
LOG_FILE = "logs/backfill.log"
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)

all_eins = set()
for f in ['data/csv/percentile_engine_v2.csv', 'data/csv/percentile_engine_v1.csv']:
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
            for r in csv.DictReader(fh):
                e = str(r.get('ein','')).strip().zfill(9)
                if e and e != '000000000': all_eins.add(e)

for yf in glob.glob('data/csv/*/sample_*.csv'):
    with open(yf, 'r', encoding='utf-8', errors='ignore') as fh:
        for r in csv.DictReader(fh):
            e = str(r.get('ein','')).strip().zfill(9)
            if e and e != '000000000': all_eins.add(e)

cached = set(f.replace('.json','') for f in os.listdir(CACHE_DIR) if f.endswith('.json'))
missing = sorted(all_eins - cached)
total_missing = len(missing)

print(f"[BACKFILL] Total: {len(all_eins)} | Cached: {len(cached)} | Missing: {total_missing}")
if total_missing == 0:
    print("[BACKFILL] Complete. Exiting.")
    sys.exit(0)

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

success = failed = skipped = 0
start_time = time.time()

for i, ein in enumerate(missing, 1):
    if i % 100 == 0:
        elapsed = time.time() - start_time
        rate = i / elapsed if elapsed > 0 else 0
        eta = (total_missing - i) / rate if rate > 0 else 0
        log(f"Progress: {i}/{total_missing} | Success: {success} | Failed: {failed} | Rate: {rate:.1f}/s | ETA: {eta/3600:.1f}h")

    url = f"https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"
    try:
        req = Request(url, headers={"User-Agent": "MeritGiving-Backfill/1.0"})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data and data.get("organization"):
                with open(os.path.join(CACHE_DIR, f"{ein}.json"), "w", encoding="utf-8") as f:
                    json.dump(data, f)
                success += 1
            else:
                with open(os.path.join(CACHE_DIR, f"{ein}.json"), "w", encoding="utf-8") as f:
                    json.dump({"__empty": True}, f)
                skipped += 1
    except HTTPError as e:
        if e.code == 404:
            with open(os.path.join(CACHE_DIR, f"{ein}.json"), "w", encoding="utf-8") as f:
                json.dump({"__not_found": True}, f)
            skipped += 1
        else:
            log(f"HTTP {e.code} for {ein}")
            failed += 1
    except (URLError, TimeoutError) as e:
        log(f"Network error for {ein}: {e}")
        failed += 1
    except Exception as e:
        log(f"Exception for {ein}: {e}")
        failed += 1

    time.sleep(0.6)

elapsed = time.time() - start_time
log(f"DONE. Total: {total_missing} | Success: {success} | Failed: {failed} | Skipped: {skipped} | Time: {elapsed/3600:.1f}h")
