#!/usr/bin/env python3
"""
MERIT Worker A — Full Collector (623K EINs)
Targets: Nonprofits with revenue $50K–$100M
"""
import os, json, time, sqlite3, csv, requests
from pathlib import Path
from datetime import datetime

BASE = Path.home() / "meritgiving"
DATA = BASE / "data"
RAW = DATA / "raw"
LOGS = BASE / "logs"
for d in [DATA, RAW, LOGS]:
    d.mkdir(parents=True, exist_ok=True)

STATE_DB = DATA / "merit_state.db"
RAW_JSONL = RAW / "orgs_raw.jsonl"

CANDIDATE_BUCKETS = {"3", "4", "5", "6", "7", "8", "9"}
PP_DELAY = 1.1
HEADERS = {"User-Agent": "Daanaa-DataBot/1.0 (contact@daanaa.org)"}

IRS_BMF_URLS = [
    "https://www.irs.gov/pub/irs-soi/eo1.csv",
    "https://www.irs.gov/pub/irs-soi/eo2.csv",
    "https://www.irs.gov/pub/irs-soi/eo3.csv",
    "https://www.irs.gov/pub/irs-soi/eo4.csv",
]

def init_db():
    conn = sqlite3.connect(STATE_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS orgs (
            ein TEXT PRIMARY KEY,
            name TEXT,
            city TEXT,
            state TEXT,
            ntee_code TEXT,
            bmf_income_bucket TEXT,
            revenue INTEGER,
            revenue_year INTEGER,
            sources TEXT,
            raw_json TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS propublica_queue (
            ein TEXT PRIMARY KEY,
            attempts INTEGER DEFAULT 0,
            last_attempt TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOGS / "worker_a.log", "a") as f:
        f.write(line + "\n")

def download_bmf():
    for url in IRS_BMF_URLS:
        fname = url.split("/")[-1]
        fpath = DATA / fname
        if fpath.exists():
            log(f"BMF {fname} cached.")
        else:
            log(f"Downloading {fname} ...")
            r = requests.get(url, headers=HEADERS, stream=True, timeout=120)
            r.raise_for_status()
            with open(fpath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            log(f"Saved {fname} ({fpath.stat().st_size:,} bytes)")
        with open(fpath, "r", encoding="latin-1") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row

def filter_candidates():
    count = 0
    for row in download_bmf():
        bucket = row.get("INCOME_CD", "").strip()
        if bucket in CANDIDATE_BUCKETS:
            count += 1
            yield {
                "ein": row.get("EIN", "").strip().zfill(9),
                "name": row.get("NAME", "").strip(),
                "city": row.get("CITY", "").strip(),
                "state": row.get("STATE", "").strip(),
                "ntee_code": row.get("NTEE_CD", "").strip(),
                "bmf_income_bucket": bucket,
            }
    log(f"BMF candidates (INCOME_CD 3-9): {count:,}")

def queue_for_propublica(candidates):
    conn = sqlite3.connect(STATE_DB)
    c = conn.cursor()
    queued = 0
    for org in candidates:
        try:
            c.execute("INSERT OR IGNORE INTO propublica_queue (ein, status) VALUES (?, 'pending')", (org["ein"],))
            c.execute("""
                INSERT OR IGNORE INTO orgs (ein, name, city, state, ntee_code, bmf_income_bucket, sources, raw_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'bmf', ?, ?, ?)
            """, (org["ein"], org["name"], org["city"], org["state"], org["ntee_code"], org["bmf_income_bucket"], json.dumps(org), datetime.now().isoformat(), datetime.now().isoformat()))
            queued += 1
        except Exception as e:
            log(f"DB error for {org['ein']}: {e}")
    conn.commit()
    conn.close()
    log(f"Queued {queued:,} EINs.")

def fetch_propublica(ein):
    url = f"https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 404:
            return {"_error": "not_found"}
        else:
            return {"_error": f"status_{r.status_code}"}
    except Exception as e:
        return {"_error": str(e)}

def run_propublica_enrichment(limit=None):
    conn = sqlite3.connect(STATE_DB)
    c = conn.cursor()
    c.execute("SELECT ein FROM propublica_queue WHERE status='pending' LIMIT ?", (limit or 999999999,))
    eins = [r[0] for r in c.fetchall()]
    conn.close()
    
    log(f"ProPublica enrichment: {len(eins):,} EINs...")
    processed = 0
    found = 0
    
    for ein in eins:
        data = fetch_propublica(ein)
        processed += 1
        conn = sqlite3.connect(STATE_DB)
        cc = conn.cursor()
        
        if "_error" in data:
            cc.execute("UPDATE propublica_queue SET attempts=attempts+1, last_attempt=?, status='failed' WHERE ein=?", (datetime.now().isoformat(), ein))
        else:
            found += 1
            org = data.get("organization", {})
            filings = data.get("filings_with_data", [])
            latest = filings[0] if filings else {}
            revenue = latest.get("totrevenue", None)
            
            tax_pd = latest.get("tax_prd", None)
            year = None
            if tax_pd is not None:
                try:
                    year = int(str(tax_pd)[:4])
                except:
                    pass
            
            # Get BMF NTEE as fallback
            cc.execute("SELECT ntee_code FROM orgs WHERE ein=?", (ein,))
            row = cc.fetchone()
            bmf_ntee = row[0] if row else ""
            pp_ntee = org.get("ntee_code", "")
            final_ntee = pp_ntee if pp_ntee else bmf_ntee
            
            cc.execute("""
                UPDATE orgs SET revenue=?, revenue_year=?, ntee_code=?, sources=sources||',propublica', updated_at=?
                WHERE ein=?
            """, (revenue, year, final_ntee, datetime.now().isoformat(), ein))
            
            cc.execute("UPDATE propublica_queue SET attempts=attempts+1, last_attempt=?, status='done' WHERE ein=?", (datetime.now().isoformat(), ein))
            
            record = {
                "ein": ein,
                "revenue": revenue,
                "revenue_year": year,
                "name": org.get("name"),
                "city": org.get("city"),
                "state": org.get("state"),
                "ntee_code": final_ntee,
                "bmf_income_bucket": None,
                "propublica_raw": data,
                "filing_count": len(filings),
                "latest_filing_year": year,
            }
            with open(RAW_JSONL, "a") as f:
                f.write(json.dumps(record) + "\n")
        
        conn.commit()
        conn.close()
        
        if processed % 100 == 0:
            log(f"ProPublica: {processed:,} done, {found:,} with data.")
        time.sleep(PP_DELAY)
    
    log(f"ProPublica complete. {processed:,} processed, {found:,} with data.")

def main():
    init_db()
    log("=== Worker A: FULL RUN Started ===")
    candidates = list(filter_candidates())
    queue_for_propublica(candidates)
    run_propublica_enrichment(limit=None)  # ALL 623K
    log("=== Worker A: FULL RUN Finished ===")
    log(f"Raw: {RAW_JSONL}")
    log(f"State: {STATE_DB}")

if __name__ == "__main__":
    main()
