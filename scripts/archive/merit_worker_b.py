#!/usr/bin/env python3
"""
MERIT Worker B — Cleaner & Validator
Reads Worker A raw JSONL, applies $50K–$100M revenue gate,
dedupes, validates NTEE, outputs production SQLite.
"""
import os, json, sqlite3, re
from pathlib import Path
from datetime import datetime

BASE = Path.home() / "meritgiving"
DATA = BASE / "data"
RAW = DATA / "raw"
PROD = DATA / "prod"
LOGS = BASE / "logs"
for d in [DATA, RAW, PROD, LOGS]:
    d.mkdir(parents=True, exist_ok=True)

RAW_JSONL = RAW / "orgs_raw.jsonl"
PROD_DB = PROD / "merit_prod.db"
NTEE_MAP = {
    "A": "Arts, Culture & Humanities",
    "B": "Education",
    "C": "Environment & Animals",
    "D": "Health",
    "E": "Human Services",
    "F": "International, Foreign Affairs",
    "G": "Public, Societal Benefit",
    "H": "Religion Related",
    "I": "Mutual/Membership Benefit",
    "J": "Unknown/Unclassified",
    "K": "Food, Agriculture & Nutrition",
    "L": "Housing & Shelter",
    "M": "Crime & Legal-Related",
    "N": "Employment",
    "O": "Youth Development",
    "P": "Human Services - Multipurpose",
    "Q": "International, Foreign Affairs",
    "R": "Civil Rights, Social Action",
    "S": "Community Improvement",
    "T": "Philanthropy, Voluntarism",
    "U": "Science & Technology",
    "V": "Social Science",
    "W": "Public & Societal Benefit",
    "X": "Religion Related",
    "Y": "Mutual & Membership Benefit",
    "Z": "Unknown",
}

REVENUE_MIN = 50_000
REVENUE_MAX = 100_000_000

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOGS / "worker_b.log", "a") as f:
        f.write(line + "\n")

def init_prod_db():
    conn = sqlite3.connect(PROD_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS orgs (
            ein TEXT PRIMARY KEY,
            name TEXT,
            city TEXT,
            state TEXT,
            ntee_code TEXT,
            ntee_major_group TEXT,
            ntee_description TEXT,
            revenue INTEGER,
            revenue_year INTEGER,
            bmf_income_bucket TEXT,
            has_990_xml INTEGER,
            latest_990_year INTEGER,
            filing_count INTEGER,
            sources TEXT,
            data_quality_score REAL,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def parse_ntee(ntee_str):
    if not ntee_str:
        return None, None
    ntee_str = ntee_str.strip().upper()
    major = ntee_str[0] if ntee_str else None
    desc = NTEE_MAP.get(major, "Unknown")
    return major, desc

def quality_score(record):
    """0.0–1.0 score based on data completeness."""
    score = 0.0
    if record.get("revenue") is not None:
        score += 0.4
    if record.get("ntee_code"):
        score += 0.2
    if record.get("has_990_xml"):
        score += 0.2
    if record.get("filing_count", 0) > 1:
        score += 0.2
    return round(score, 2)

def process_raw():
    if not RAW_JSONL.exists():
        log(f"ERROR: Raw file not found: {RAW_JSONL}")
        return
    
    log("Reading raw JSONL...")
    records = []
    with open(RAW_JSONL, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    log(f"Loaded {len(records):,} raw records.")
    
    # Deduplicate by EIN (keep latest revenue_year)
    by_ein = {}
    for rec in records:
        ein = rec.get("ein")
        if not ein:
            continue
        existing = by_ein.get(ein)
        if not existing or (rec.get("revenue_year") or 0) > (existing.get("revenue_year") or 0):
            by_ein[ein] = rec
    
    log(f"After dedupe: {len(by_ein):,} unique EINs.")
    
    # Revenue gate
    passed = []
    failed_low = 0
    failed_high = 0
    no_revenue = 0
    
    for ein, rec in by_ein.items():
        rev = rec.get("revenue")
        if rev is None:
            no_revenue += 1
            continue
        if rev < REVENUE_MIN:
            failed_low += 1
            continue
        if rev > REVENUE_MAX:
            failed_high += 1
            continue
        passed.append(rec)
    
    log(f"Revenue filter: {len(passed):,} passed.")
    log(f"  - Below $50K: {failed_low:,}")
    log(f"  - Above $100M: {failed_high:,}")
    log(f"  - No revenue data: {no_revenue:,}")
    
    # Write to production DB
    conn = sqlite3.connect(PROD_DB)
    c = conn.cursor()
    inserted = 0
    
    for rec in passed:
        ein = rec.get("ein")
        ntee = rec.get("ntee_code", "")
        major, desc = parse_ntee(ntee)
        score = quality_score(rec)
        
        try:
            c.execute("""
                INSERT OR REPLACE INTO orgs (
                    ein, name, city, state, ntee_code, ntee_major_group, ntee_description,
                    revenue, revenue_year, bmf_income_bucket, has_990_xml, latest_990_year,
                    filing_count, sources, data_quality_score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ein,
                rec.get("name"),
                rec.get("city"),
                rec.get("state"),
                ntee,
                major,
                desc,
                rec.get("revenue"),
                rec.get("revenue_year"),
                rec.get("bmf_income_bucket"),
                rec.get("has_990_xml", 0),
                rec.get("latest_990_year"),
                rec.get("filing_count", 0),
                "propublica,bmf",
                score,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ))
            inserted += 1
        except Exception as e:
            log(f"Insert error for {ein}: {e}")
    
    # Update stats
    c.execute("""
        INSERT OR REPLACE INTO stats (key, value, updated_at)
        VALUES ('total_orgs', ?, ?)
    """, (str(inserted), datetime.now().isoformat()))
    
    c.execute("""
        INSERT OR REPLACE INTO stats (key, value, updated_at)
        VALUES ('revenue_range', ?, ?)
    """, ("$50K–$100M", datetime.now().isoformat()))
    
    # Revenue distribution buckets
    buckets = [
        ("50K-100K", 50000, 100000),
        ("100K-1M", 100000, 1000000),
        ("1M-5M", 1000000, 5000000),
        ("5M-10M", 5000000, 10000000),
        ("10M-50M", 10000000, 50000000),
        ("50M-100M", 50000000, 100000000),
    ]
    
    for label, lo, hi in buckets:
        c.execute("SELECT COUNT(*) FROM orgs WHERE revenue >= ? AND revenue < ?", (lo, hi))
        count = c.fetchone()[0]
        c.execute("""
            INSERT OR REPLACE INTO stats (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (f"bucket_{label}", str(count), datetime.now().isoformat()))
        log(f"  Bucket {label}: {count:,}")
    
    conn.commit()
    conn.close()
    
    log(f"Production DB updated: {inserted:,} organizations.")
    log(f"Output: {PROD_DB}")

def generate_summary():
    conn = sqlite3.connect(PROD_DB)
    c = conn.cursor()
    
    print("\n" + "="*60)
    print("MERITGIVING PRODUCTION DATABASE SUMMARY")
    print("="*60)
    
    c.execute("SELECT COUNT(*) FROM orgs")
    total = c.fetchone()[0]
    print(f"Total organizations: {total:,}")
    
    c.execute("SELECT AVG(revenue) FROM orgs")
    avg_rev = c.fetchone()[0]
    print(f"Average revenue: ${avg_rev:,.0f}" if avg_rev else "Average revenue: N/A")
    
    c.execute("SELECT ntee_major_group, COUNT(*) FROM orgs GROUP BY ntee_major_group ORDER BY COUNT(*) DESC LIMIT 10")
    print("\nTop NTEE Major Groups:")
    for row in c.fetchall():
        print(f"  {row[0] or 'Unknown'}: {row[1]:,}")
    
    c.execute("SELECT state, COUNT(*) FROM orgs GROUP BY state ORDER BY COUNT(*) DESC LIMIT 10")
    print("\nTop States:")
    for row in c.fetchall():
        print(f"  {row[0] or 'Unknown'}: {row[1]:,}")
    
    print("="*60)
    conn.close()

def main():
    init_prod_db()
    log("=== Worker B: Cleaner Started ===")
    process_raw()
    generate_summary()
    log("=== Worker B: Cleaner Finished ===")

if __name__ == "__main__":
    main()
