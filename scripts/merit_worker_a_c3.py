#!/usr/bin/env python3
"""
MERIT Worker A — C3 Deductible Only Collector
Resumes from filtered state DB. Only hits ProPublica for pending C3 EINs.
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
PP_DELAY = 1.1
HEADERS = {"User-Agent": "MERITGiving-DataBot/1.0 (contact@meritgiving.org)"}

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOGS / "worker_a.log", "a") as f:
        f.write(line + "\n")

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
    
    log(f"C3 Collector: {len(eins):,} pending EINs...")
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
            
            cc.execute("SELECT ntee_code FROM orgs WHERE ein=?", (ein,))
            row = cc.fetchone()
            bmf_ntee = row[0] if row else ""
            pp_ntee = org.get("ntee_code", "")
            final_ntee = pp_ntee if pp_ntee else bmf_ntee
            
            cc.execute("""
                UPDATE orgs SET revenue=?, revenue_year=?, ntee_code=?, sources=COALESCE(sources,'')||',propublica', updated_at=?
                WHERE ein=?
            """, (revenue, year, final_ntee, datetime.now().isoformat(), ein))
            
            cc.execute("UPDATE propublica_queue SET attempts=attempts+1, last_attempt=?, status='done' WHERE ein=?", (datetime.now().isoformat(), ein))
            
            record = {
                "ein": ein, "revenue": revenue, "revenue_year": year,
                "name": org.get("name"), "city": org.get("city"), "state": org.get("state"),
                "ntee_code": final_ntee, "bmf_income_bucket": None,
                "propublica_raw": data, "filing_count": len(filings), "latest_filing_year": year,
            }
            with open(RAW_JSONL, "a") as f:
                f.write(json.dumps(record) + "\n")
        
        conn.commit()
        conn.close()
        
        if processed % 100 == 0:
            log(f"ProPublica C3: {processed:,} done, {found:,} with data.")
        time.sleep(PP_DELAY)
    
    log(f"C3 Collector complete. {processed:,} processed, {found:,} with data.")

def main():
    log("=== Worker A: C3 DEDUCTIBLE ONLY Started ===")
    run_propublica_enrichment(limit=None)
    log("=== Worker A: C3 DEDUCTIBLE ONLY Finished ===")

if __name__ == "__main__":
    main()
