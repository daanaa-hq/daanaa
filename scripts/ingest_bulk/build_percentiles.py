import sqlite3, os, math
from datetime import datetime

DB = os.path.expanduser("~/meritgiving/data/meritgiving.db")
print(f"[{datetime.now()}] Building revenue percentiles...")

conn = sqlite3.connect(DB)
c = conn.cursor()

# Ensure revenue table exists
c.execute("""
CREATE TABLE IF NOT EXISTS org_revenue (
    ein TEXT PRIMARY KEY,
    name TEXT,
    totrev REAL,
    totexp REAL,
    totass REAL,
    ntee TEXT,
    state TEXT,
    category TEXT
)
""")

# Create percentiles table
c.execute("""
CREATE TABLE IF NOT EXISTS revenue_percentiles (
    ntee_prefix TEXT,
    state TEXT,
    p10 REAL, p25 REAL, p50 REAL, p75 REAL, p90 REAL,
    count INTEGER,
    updated TEXT
)
""")
c.execute("DELETE FROM revenue_percentiles")

# Get all NTEE prefixes
c.execute("SELECT DISTINCT substr(ntee,1,1) FROM org_revenue WHERE ntee IS NOT NULL AND ntee != ''")
ntee_prefixes = [r[0] for r in c.fetchall()]
print(f"Found {len(ntee_prefixes)} NTEE prefixes")

for prefix in ntee_prefixes:
    c.execute("""
        SELECT totrev FROM org_revenue 
        WHERE ntee LIKE ? AND totrev > 0 AND totrev IS NOT NULL
    """, (prefix + '%',))
    revs = sorted([r[0] for r in c.fetchall()])
    if len(revs) < 10:
        continue
    
    n = len(revs)
    p10 = revs[int(n*0.10)]
    p25 = revs[int(n*0.25)]
    p50 = revs[int(n*0.50)]
    p75 = revs[int(n*0.75)]
    p90 = revs[int(n*0.90)]
    
    c.execute("""
        INSERT INTO revenue_percentiles VALUES (?, 'ALL', ?, ?, ?, ?, ?, ?, ?)
    """, (prefix, p10, p25, p50, p75, p90, n, str(datetime.now())))
    
    if len(revs) % 1000 == 0:
        print(f"  {prefix}: {n} orgs")

conn.commit()

# Also do state-level percentiles for top 10 states by org count
c.execute("""
    SELECT state, COUNT(*) as cnt FROM org_revenue 
    WHERE state IS NOT NULL AND state != '' 
    GROUP BY state ORDER BY cnt DESC LIMIT 10
""")
top_states = [r[0] for r in c.fetchall()]

for state in top_states:
    for prefix in ntee_prefixes:
        c.execute("""
            SELECT totrev FROM org_revenue 
            WHERE state = ? AND ntee LIKE ? AND totrev > 0 AND totrev IS NOT NULL
        """, (state, prefix + '%'))
        revs = sorted([r[0] for r in c.fetchall()])
        if len(revs) < 5:
            continue
        n = len(revs)
        p50 = revs[int(n*0.50)]
        p75 = revs[int(n*0.75)]
        c.execute("""
            INSERT INTO revenue_percentiles VALUES (?, ?, 0, 0, ?, ?, 0, ?, ?)
        """, (prefix, state, p50, p75, n, str(datetime.now())))

conn.commit()
conn.close()
print(f"[{datetime.now()}] Percentiles DONE.")
