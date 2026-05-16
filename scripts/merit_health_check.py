#!/usr/bin/env python3
import sqlite3, json, statistics
from pathlib import Path

DB = Path.home() / "meritgiving/data/merit_state.db"
RAW = Path.home() / "meritgiving/data/raw/orgs_raw.jsonl"

def audit_db():
    if not DB.exists():
        print("No state DB found.")
        return

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    print("=" * 60)
    print("MERITGIVING DATA HEALTH AUDIT")
    print("=" * 60)

    c.execute("SELECT COUNT(*) FROM orgs WHERE sources LIKE '%propublica%'")
    total_pp = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orgs WHERE revenue IS NOT NULL")
    with_revenue = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orgs WHERE revenue IS NULL AND sources LIKE '%propublica%'")
    missing_rev = c.fetchone()[0]

    print(f"\n[COLLECTION COVERAGE]")
    print(f"  ProPublica enriched: {total_pp:,}")
    print(f"  With revenue data:   {with_revenue:,} ({with_revenue/total_pp*100:.1f}%)")
    print(f"  Missing revenue:     {missing_rev:,}")

    c.execute("SELECT revenue FROM orgs WHERE revenue IS NOT NULL")
    revs = [r[0] for r in c.fetchall()]
    if revs:
        print(f"\n[REVENUE DISTRIBUTION]")
        print(f"  Count:    {len(revs):,}")
        print(f"  Min:      ${min(revs):,}")
        print(f"  Max:      ${max(revs):,}")
        print(f"  Mean:     ${statistics.mean(revs):,.0f}")
        print(f"  Median:   ${statistics.median(revs):,.0f}")

        in_range = sum(1 for r in revs if 50000 <= r <= 100000000)
        below = sum(1 for r in revs if r < 50000)
        above = sum(1 for r in revs if r > 100000000)
        print(f"\n[TARGET FILTER ($50K-$100M)]")
        print(f"  In range:  {in_range:,} ({in_range/len(revs)*100:.1f}%)")
        print(f"  Below $50K: {below:,} ({below/len(revs)*100:.1f}%)")
        print(f"  Above $100M: {above:,} ({above/len(revs)*100:.1f}%)")

    c.execute("SELECT ntee_code FROM orgs WHERE sources LIKE '%propublica%'")
    ntees = [r[0] for r in c.fetchall()]
    has_ntee = sum(1 for n in ntees if n)
    print(f"\n[NTEE COVERAGE]")
    print(f"  Has NTEE:  {has_ntee:,} ({has_ntee/len(ntees)*100:.1f}%)")
    print(f"  Missing:   {len(ntees)-has_ntee:,}")

    c.execute("SELECT state, COUNT(*) FROM orgs WHERE sources LIKE '%propublica%' GROUP BY state ORDER BY COUNT(*) DESC LIMIT 10")
    print(f"\n[TOP 10 STATES]")
    for row in c.fetchall():
        print(f"  {row[0] or '??'}: {row[1]:,}")

    c.execute("SELECT revenue_year, COUNT(*) FROM orgs WHERE revenue_year IS NOT NULL GROUP BY revenue_year ORDER BY revenue_year DESC LIMIT 5")
    print(f"\n[TOP FILING YEARS]")
    for row in c.fetchall():
        print(f"  {row[0]}: {row[1]:,}")

    conn.close()

    if RAW.exists():
        print(f"\n[RAW JSONL]")
        print(f"  File size: {RAW.stat().st_size / 1_048_576:.1f} MB")
        with open(RAW) as f:
            lines = f.readlines()
        print(f"  Records:   {len(lines):,}")
        bad = 0
        for line in lines:
            try:
                json.loads(line)
            except:
                bad += 1
        print(f"  Parse OK:  {len(lines)-bad:,}")
        print(f"  Bad lines: {bad}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    audit_db()
