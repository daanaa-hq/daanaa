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