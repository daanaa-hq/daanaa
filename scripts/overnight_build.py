import sqlite3
import pandas as pd
import os
import json
from datetime import datetime

DB = "data/merit_registry.db"
OUT_DIR = "data/exports"
API_DIR = "api"
LOG = "data/overnight_build.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(API_DIR, exist_ok=True)
open(LOG, "w").close()

log("=== MERITGIVING OVERNIGHT BUILD STARTED ===")

# ============================================================
# PHASE 1: CROSSWALK — Enrich registry with percentiles
# ============================================================
log("PHASE 1: Crosswalking registry + percentiles...")

with sqlite3.connect(DB) as conn:
    c = conn.cursor()
    
    # Check if registry table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='registry'")
    has_registry = c.fetchone() is not None
    
    if has_registry:
        c.execute("SELECT COUNT(*) FROM registry_enriched")
        reg_count = c.fetchone()[0]
        log(f"  Found registry table: {reg_count:,} rows")
        
        # Create enriched registry
        c.execute("DROP TABLE IF EXISTS registry_enriched")
        c.execute("""
            CREATE TABLE registry_enriched AS
            SELECT 
                r.*,
                p.total_revenue,
                p.ntee1_percentile,
                p.state_ntee1_percentile,
                p.ntee1_rank,
                p.ntee1_total_orgs,
                CASE 
                    WHEN p.total_revenue > (SELECT AVG(total_revenue) FROM revenue_percentiles WHERE NTEE1 = p.NTEE1)
                    THEN 'ABOVE_AVG'
                    ELSE 'BELOW_AVG'
                END as peer_status
            FROM registry_enriched r
            LEFT JOIN revenue_percentiles p ON r.EIN = p.EIN
        """)
        conn.commit()
        
        c.execute("SELECT COUNT(*) FROM registry_enriched WHERE total_revenue IS NOT NULL")
        matched = c.fetchone()[0]
        log(f"  registry_enriched created: {reg_count:,} rows, {matched:,} matched to NCCS revenue data")
    else:
        log("  No registry table found — skipping crosswalk (will build from percentiles only)")
        # Create a lightweight registry from percentiles as fallback
        c.execute("DROP TABLE IF EXISTS registry_enriched")
        c.execute("""
            CREATE TABLE registry_enriched AS
            SELECT 
                EIN,
                NAME as organization_name,
                NTEE1,
                NTEECC,
                STATE,
                CITY,
                total_revenue,
                ntee1_percentile,
                state_ntee1_percentile,
                ntee1_rank,
                ntee1_total_orgs,
                'NCCS_ONLY' as source
            FROM revenue_percentiles
        """)
        conn.commit()
        c.execute("SELECT COUNT(*) FROM registry_enriched")
        log(f"  Created fallback registry_enriched from percentiles: {c.fetchone()[0]:,} rows")

# ============================================================
# PHASE 2: CSV EXPORTS
# ============================================================
log("PHASE 2: Exporting CSVs...")

with sqlite3.connect(DB) as conn:
    # Full percentiles
    df_full = pd.read_sql_query("SELECT * FROM revenue_percentiles", conn)
    f1 = f"{OUT_DIR}/merit_percentiles_full.csv"
    df_full.to_csv(f1, index=False)
    log(f"  Exported {f1}: {len(df_full):,} rows, {os.path.getsize(f1)/1024/1024:.1f} MB")
    
    # Top 100 per NTEE1
    df_top = pd.read_sql_query("""
        SELECT * FROM revenue_percentiles
        WHERE ntee1_rank <= 100
        ORDER BY NTEE1, ntee1_rank
    """, conn)
    f2 = f"{OUT_DIR}/merit_percentiles_top100_per_ntee.csv"
    df_top.to_csv(f2, index=False)
    log(f"  Exported {f2}: {len(df_top):,} rows")
    
    # NTEE1 summary stats
    df_summary = pd.read_sql_query("""
        SELECT 
            NTEE1,
            COUNT(*) as org_count,
            ROUND(AVG(total_revenue),0) as avg_revenue,
            MAX(total_revenue) as max_revenue,
            MIN(total_revenue) as min_revenue,
            ROUND(AVG(CASE WHEN ntee1_percentile >= 90 THEN total_revenue END),0) as p90_threshold,
            ROUND(AVG(CASE WHEN ntee1_percentile >= 75 THEN total_revenue END),0) as p75_threshold,
            ROUND(AVG(CASE WHEN ntee1_percentile >= 50 THEN total_revenue END),0) as p50_threshold,
            ROUND(AVG(CASE WHEN ntee1_percentile >= 25 THEN total_revenue END),0) as p25_threshold
        FROM revenue_percentiles
        GROUP BY NTEE1
        ORDER BY org_count DESC
    """, conn)
    f3 = f"{OUT_DIR}/merit_ntee_summary.csv"
    df_summary.to_csv(f3, index=False)
    log(f"  Exported {f3}: {len(df_summary)} NTEE categories")

# ============================================================
# PHASE 3: FASTAPI ENDPOINT GENERATOR
# ============================================================
log("PHASE 3: Generating FastAPI endpoint...")

api_code = '''
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "merit_registry.db")

app = FastAPI(title="MeritGiving API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    return sqlite3.connect(DB_PATH)

@app.get("/")
def root():
    return {"status": "MeritGiving API is running", "version": "0.1.0"}

@app.get("/percentile/{ein}")
def get_percentile(ein: str):
    """Get revenue percentile and peer ranking for a nonprofit by EIN."""
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT 
                EIN, NAME, NTEE1, NTEECC, STATE, CITY,
                total_revenue, ntee1_percentile, state_ntee1_percentile,
                ntee1_rank, ntee1_total_orgs
            FROM revenue_percentiles
            WHERE EIN = ?
        """, (ein,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="EIN not found in revenue percentiles")
        
        # Get peer average for context
        c.execute("""
            SELECT AVG(total_revenue) as peer_avg
            FROM revenue_percentiles
            WHERE NTEE1 = ?
        """, (row["NTEE1"],))
        peer_avg = c.fetchone()["peer_avg"]
        
        return {
            "ein": row["EIN"],
            "name": row["NAME"],
            "ntee1": row["NTEE1"],
            "nteecc": row["NTEECC"],
            "state": row["STATE"],
            "city": row["CITY"],
            "total_revenue": row["total_revenue"],
            "national_percentile": row["ntee1_percentile"],
            "state_percentile": row["state_ntee1_percentile"],
            "peer_rank": f"{row['ntee1_rank']} of {row['ntee1_total_orgs']}",
            "peer_average_revenue": round(peer_avg, 0),
            "peer_comparison": "above_average" if row["total_revenue"] > peer_avg else "below_average"
        }

@app.get("/ntee/{ntee1}")
def get_ntee_summary(ntee1: str):
    """Get aggregate stats for an NTEE1 category."""
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT 
                COUNT(*) as org_count,
                AVG(total_revenue) as avg_revenue,
                MAX(total_revenue) as max_revenue,
                MIN(total_revenue) as min_revenue
            FROM revenue_percentiles
            WHERE NTEE1 = ?
        """, (ntee1,))
        summary = c.fetchone()
        if summary["org_count"] == 0:
            raise HTTPException(status_code=404, detail="NTEE1 category not found")
        
        # Top 10 in category
        c.execute("""
            SELECT EIN, NAME, total_revenue, ntee1_percentile
            FROM revenue_percentiles
            WHERE NTEE1 = ?
            ORDER BY total_revenue DESC
            LIMIT 10
        """, (ntee1,))
        top10 = [dict(r) for r in c.fetchall()]
        
        return {
            "ntee1": ntee1,
            "org_count": summary["org_count"],
            "avg_revenue": round(summary["avg_revenue"], 0),
            "max_revenue": summary["max_revenue"],
            "min_revenue": summary["min_revenue"],
            "top_10": top10
        }

@app.get("/search")
def search_orgs(q: str, limit: int = 20):
    """Search nonprofits by name."""
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT EIN, NAME, NTEE1, STATE, total_revenue, ntee1_percentile
            FROM revenue_percentiles
            WHERE NAME LIKE ?
            ORDER BY total_revenue DESC
            LIMIT ?
        """, (f"%{q}%", limit))
        return {"results": [dict(r) for r in c.fetchall()]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

api_path = f"{API_DIR}/main.py"
with open(api_path, "w") as f:
    f.write(api_code.strip())

log(f"  Generated {api_path}")
log("  To start API later: cd api && uvicorn main:app --host 0.0.0.0 --port 8000")

# ============================================================
# DONE
# ============================================================
log("=== OVERNIGHT BUILD COMPLETE ===")
log(f"Outputs:")
log(f"  - SQLite: registry_enriched, revenue_percentiles")
log(f"  - CSVs: {OUT_DIR}/")
log(f"  - API: {API_DIR}/main.py")
log(f"  - Log: {LOG}")

