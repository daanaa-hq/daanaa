#!/usr/bin/env python3
"""
MERIT Worker C — Analytics & NTEE Enrichment (CPU-bound)
Processes existing collected data while Worker A runs.
"""
import sqlite3, json, statistics
from pathlib import Path
from datetime import datetime

BASE = Path.home() / "meritgiving"
DATA = BASE / "data"
PROD = DATA / "prod"
LOGS = BASE / "logs"
for d in [PROD, LOGS]:
    d.mkdir(parents=True, exist_ok=True)

STATE_DB = DATA / "merit_state.db"
ANALYTICS_DB = PROD / "merit_analytics.db"

NTEE_MAP = {
    "A": "Arts, Culture & Humanities", "B": "Education", "C": "Environment & Animals",
    "D": "Health", "E": "Human Services", "F": "International, Foreign Affairs",
    "G": "Public, Societal Benefit", "H": "Religion Related", "I": "Mutual/Membership Benefit",
    "J": "Unknown/Unclassified", "K": "Food, Agriculture & Nutrition", "L": "Housing & Shelter",
    "M": "Crime & Legal-Related", "N": "Employment", "O": "Youth Development",
    "P": "Human Services - Multipurpose", "Q": "International, Foreign Affairs",
    "R": "Civil Rights, Social Action", "S": "Community Improvement",
    "T": "Philanthropy, Voluntarism", "U": "Science & Technology", "V": "Social Science",
    "W": "Public & Societal Benefit", "X": "Religion Related", "Y": "Mutual & Membership Benefit",
    "Z": "Unknown",
}

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOGS / "worker_c.log", "a") as f:
        f.write(line + "\n")

def init_analytics_db():
    conn = sqlite3.connect(ANALYTICS_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS revenue_percentiles (
            ntee_major_group TEXT, percentile INTEGER,
            revenue_threshold INTEGER, org_count INTEGER, updated_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS state_summary (
            state TEXT PRIMARY KEY, org_count INTEGER, avg_revenue INTEGER,
            median_revenue INTEGER, total_revenue INTEGER, updated_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS ntee_summary (
            ntee_major_group TEXT PRIMARY KEY, org_count INTEGER,
            avg_revenue INTEGER, median_revenue INTEGER, updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def backfill_ntee_from_bmf():
    log("Backfilling NTEE from BMF...")
    conn = sqlite3.connect(STATE_DB)
    c = conn.cursor()
    c.execute("""
        SELECT ein, raw_json FROM orgs 
        WHERE (ntee_code IS NULL OR ntee_code = '') AND sources LIKE '%bmf%'
    """)
    fixed = 0
    for ein, raw_json in c.fetchall():
        try:
            bmf_ntee = json.loads(raw_json).get("ntee_code", "")
            if bmf_ntee:
                c.execute("UPDATE orgs SET ntee_code = ? WHERE ein = ?", (bmf_ntee, ein))
                fixed += 1
        except:
            pass
    conn.commit()
    log(f"Backfilled {fixed:,} NTEE codes from BMF.")
    conn.close()
    return fixed

def build_analytics():
    conn = sqlite3.connect(STATE_DB)
    c = conn.cursor()
    c.execute("""
        SELECT ein, state, ntee_code, revenue FROM orgs 
        WHERE sources LIKE '%propublica%' AND revenue IS NOT NULL
    """)
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        log("No data to analyze yet.")
        return
    
    log(f"Analyzing {len(rows):,} organizations...")
    
    orgs = []
    for ein, state, ntee, rev in rows:
        major = ntee[0].upper() if ntee else "?"
        orgs.append({"state": state or "??", "ntee_major": major, "revenue": rev})
    
    conn = sqlite3.connect(ANALYTICS_DB)
    c = conn.cursor()
    
    # Revenue percentiles by NTEE
    by_ntee = {}
    for o in orgs:
        by_ntee.setdefault(o["ntee_major"], []).append(o["revenue"])
    
    c.execute("DELETE FROM revenue_percentiles")
    for group, revs in by_ntee.items():
        revs_sorted = sorted(revs)
        n = len(revs_sorted)
        for p in [10, 25, 50, 75, 90]:
            idx = min(int(n * p / 100), n - 1)
            c.execute("""
                INSERT INTO revenue_percentiles VALUES (?, ?, ?, ?, ?)
            """, (group, p, revs_sorted[idx], n, datetime.now().isoformat()))
        desc = NTEE_MAP.get(group, "Unknown")
        log(f"  NTEE {group} ({desc}): {n:,} orgs, median ${statistics.median(revs_sorted):,.0f}")
    
    # State summaries
    by_state = {}
    for o in orgs:
        by_state.setdefault(o["state"], []).append(o["revenue"])
    
    c.execute("DELETE FROM state_summary")
    for state, revs in by_state.items():
        c.execute("""
            INSERT OR REPLACE INTO state_summary VALUES (?, ?, ?, ?, ?, ?)
        """, (state, len(revs), int(statistics.mean(revs)), int(statistics.median(revs)), sum(revs), datetime.now().isoformat()))
    
    # NTEE summaries
    c.execute("DELETE FROM ntee_summary")
    for group, revs in by_ntee.items():
        c.execute("""
            INSERT OR REPLACE INTO ntee_summary VALUES (?, ?, ?, ?, ?)
        """, (group, len(revs), int(statistics.mean(revs)), int(statistics.median(revs)), datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    log(f"Analytics DB: {ANALYTICS_DB}")

def main():
    init_analytics_db()
    log("=== Worker C: Analytics Started ===")
    backfill_ntee_from_bmf()
    build_analytics()
    log("=== Worker C: Analytics Finished ===")

if __name__ == "__main__":
    main()
