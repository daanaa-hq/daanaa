#!/usr/bin/env python3
"""
MERIT Worker F — IRS 990 XML Downloader
Downloads raw Form 990 XML from IRS AWS S3 for validated EINs.
"""
import os, json, time, sqlite3, requests
from pathlib import Path
from datetime import datetime

BASE = Path.home() / "meritgiving"
DATA = BASE / "data"
XML_DIR = DATA / "990_xml"
LOGS = BASE / "logs"
for d in [XML_DIR, LOGS]:
    d.mkdir(parents=True, exist_ok=True)

STATE_DB = DATA / "merit_state.db"
HEADERS = {"User-Agent": "Daanaa-DataBot/1.0 (contact@daanaa.org)"}
REVENUE_MIN = 50_000
REVENUE_MAX = 100_000_000

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOGS / "worker_f.log", "a") as f:
        f.write(line + "\n")

def download_index(year):
    url = f"https://s3.amazonaws.com/irs-form-990/index_{year}.json"
    fpath = DATA / f"index_{year}.json"
    if fpath.exists():
        log(f"Index {year} cached.")
        return fpath
    log(f"Downloading index {year} ...")
    try:
        r = requests.get(url, headers=HEADERS, timeout=120, stream=True)
        if r.status_code == 200:
            with open(fpath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            log(f"Saved index_{year}.json")
            return fpath
        else:
            log(f"Index {year} returned {r.status_code}")
            return None
    except Exception as e:
        log(f"Index {year} failed: {e}")
        return None

def load_index(year):
    fpath = download_index(year)
    if not fpath:
        return {}
    try:
        with open(fpath, "r") as f:
            data = json.load(f)
        key = f"Filings{year}"
        filings = data.get(key, data.get("Filings", []))
        by_ein = {}
        for filing in filings:
            ein = str(filing.get("EIN", "")).zfill(9)
            if ein:
                by_ein.setdefault(ein, []).append(filing)
        log(f"Index {year}: {len(filings):,} filings, {len(by_ein):,} unique EINs.")
        return by_ein
    except Exception as e:
        log(f"Parse error index {year}: {e}")
        return {}

def get_target_eins():
    conn = sqlite3.connect(STATE_DB)
    c = conn.cursor()
    c.execute("""
        SELECT ein, revenue, name, state FROM orgs 
        WHERE revenue >= ? AND revenue <= ? AND sources LIKE '%propublica%'
    """, (REVENUE_MIN, REVENUE_MAX))
    rows = c.fetchall()
    conn.close()
    log(f"Target EINs (${REVENUE_MIN:,}-${REVENUE_MAX:,}): {len(rows):,}")
    return rows

def fetch_xml(url, ein, year):
    fname = url.split("/")[-1]
    if not fname.endswith(".xml"):
        fname += ".xml"
    fpath = XML_DIR / f"{year}_{fname}"
    if fpath.exists():
        return fpath, "cached"
    try:
        r = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        if r.status_code == 200:
            with open(fpath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return fpath, "downloaded"
        else:
            return None, f"status_{r.status_code}"
    except Exception as e:
        return None, str(e)

def main():
    log("=== Worker F: IRS 990 XML Downloader Started ===")
    indices = {}
    for year in [2024, 2023, 2022, 2021]:
        idx = load_index(year)
        if idx:
            indices[year] = idx
    if not indices:
        log("ERROR: No indices loaded.")
        return
    targets = get_target_eins()
    if not targets:
        log("No target EINs yet.")
        return
    total = len(targets)
    matched = 0
    downloaded = 0
    cached = 0
    failed = 0
    for i, (ein, revenue, name, state) in enumerate(targets, 1):
        found_any = False
        for year, idx in indices.items():
            filings = idx.get(ein, [])
            for filing in filings:
                found_any = True
                url = filing.get("URL", "")
                if not url:
                    continue
                fpath, status = fetch_xml(url, ein, year)
                if status == "downloaded":
                    downloaded += 1
                elif status == "cached":
                    cached += 1
                else:
                    failed += 1
                time.sleep(0.05)
        if found_any:
            matched += 1
        if i % 100 == 0:
            log(f"Progress: {i}/{total} | matched: {matched} | new: {downloaded} | cached: {cached} | fail: {failed}")
    log(f"Finished: {total} targets, {matched} matched, {downloaded} downloaded, {cached} cached, {failed} failed.")

if __name__ == "__main__":
    main()
