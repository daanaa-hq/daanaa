#!/usr/bin/env python3
"""
MERIT Filter: Keep only 501(c)(3) tax-deductible orgs.
Rebuilds queue from BMF + preserves already-collected C3 data.
"""
import csv, sqlite3, json
from pathlib import Path
from datetime import datetime

BASE = Path.home() / "meritgiving"
DATA = BASE / "data"
LOGS = BASE / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

STATE_DB = DATA / "merit_state.db"
RAW_JSONL = DATA / "raw" / "orgs_raw.jsonl"

BMF_FILES = [
    DATA / "eo1.csv", DATA / "eo2.csv",
    DATA / "eo3.csv", DATA / "eo4.csv",
]

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOGS / "filter_c3.log", "a") as f:
        f.write(line + "\n")

def load_c3_eins():
    """Scan BMF for SUBSECTION=03 AND DEDUCTIBILITY=1."""
    c3_set = set()
    total = 0
    for fpath in BMF_FILES:
        if not fpath.exists():
            continue
        log(f"Scanning {fpath.name} for 501(c)(3) deductible...")
        with open(fpath, "r", encoding="latin-1") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total += 1
                sub = row.get("SUBSECTION", "").strip()
                ded = row.get("DEDUCTIBILITY", "").strip()
                if sub == "03" and ded == "1":
                    ein = row.get("EIN", "").strip().zfill(9)
                    if ein:
                        c3_set.add(ein)
        log(f"  Rows scanned: {total:,} | C3 deductible so far: {len(c3_set):,}")
    log(f"TOTAL C3 deductible EINs in BMF: {len(c3_set):,}")
    return c3_set

def filter_state_db(c3_set):
    conn = sqlite3.connect(STATE_DB)
    c = conn.cursor()
    
    # Count current state
    c.execute("SELECT COUNT(*) FROM propublica_queue WHERE status='done'")
    done_total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM propublica_queue WHERE status='pending'")
    pending_total = c.fetchone()[0]
    log(f"Before filter: {done_total:,} done, {pending_total:,} pending.")
    
    # Remove non-C3 from queue
    c.execute("SELECT ein FROM propublica_queue")
    removed_queue = 0
    for (ein,) in c.fetchall():
        if ein not in c3_set:
            c.execute("DELETE FROM propublica_queue WHERE ein=?", (ein,))
            removed_queue += 1
    
    # Remove non-C3 from orgs table (but keep BMF-only rows for C3 pending)
    c.execute("SELECT ein FROM orgs WHERE sources LIKE '%propublica%'")
    removed_orgs = 0
    kept_orgs = 0
    for (ein,) in c.fetchall():
        if ein not in c3_set:
            c.execute("DELETE FROM orgs WHERE ein=?", (ein,))
            removed_orgs += 1
        else:
            kept_orgs += 1
    
    conn.commit()
    
    # Count after
    c.execute("SELECT COUNT(*) FROM propublica_queue WHERE status='done'")
    done_after = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM propublica_queue WHERE status='pending'")
    pending_after = c.fetchone()[0]
    
    log(f"Removed from queue: {removed_queue:,}")
    log(f"Removed ProPublica orgs: {removed_orgs:,}")
    log(f"Kept ProPublica orgs: {kept_orgs:,}")
    log(f"After filter: {done_after:,} done, {pending_after:,} pending.")
    
    conn.close()
    return done_after, pending_after

def filter_raw_jsonl(c3_set):
    if not RAW_JSONL.exists():
        log("No raw JSONL to filter.")
        return 0, 0
    
    log("Filtering raw JSONL to C3 only...")
    kept = 0
    removed = 0
    temp_path = RAW_JSONL.with_suffix(".jsonl.tmp")
    
    with open(RAW_JSONL, "r") as fin, open(temp_path, "w") as fout:
        for line in fin:
            try:
                rec = json.loads(line)
                if rec.get("ein") in c3_set:
                    fout.write(line)
                    kept += 1
                else:
                    removed += 1
            except json.JSONDecodeError:
                fout.write(line)  # keep bad lines just in case
    
    RAW_JSONL.unlink()
    temp_path.rename(RAW_JSONL)
    log(f"Raw JSONL: kept {kept:,}, removed {removed:,}")
    return kept, removed

def add_missing_c3_to_queue(c3_set):
    """Ensure all C3 EINs from BMF are in the queue (some may not have been added)."""
    conn = sqlite3.connect(STATE_DB)
    c = conn.cursor()
    
    c.execute("SELECT ein FROM propublica_queue")
    queued = {r[0] for r in c.fetchall()}
    
    missing = c3_set - queued
    added = 0
    for ein in missing:
        c.execute("INSERT OR IGNORE INTO propublica_queue (ein, status) VALUES (?, 'pending')", (ein,))
        added += 1
        if added % 10000 == 0:
            conn.commit()
    
    conn.commit()
    conn.close()
    log(f"Added {added:,} missing C3 EINs to queue.")
    return added

def main():
    log("=== FILTER: 501(c)(3) Deductible Only ===")
    c3_set = load_c3_eins()
    done, pending = filter_state_db(c3_set)
    filter_raw_jsonl(c3_set)
    added = add_missing_c3_to_queue(c3_set)
    
    log("=== FILTER COMPLETE ===")
    log(f"Final queue: {done:,} done + {pending + added:,} pending = {done + pending + added:,} total C3 EINs.")

if __name__ == "__main__":
    main()
