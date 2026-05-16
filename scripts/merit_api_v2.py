from fastapi import FastAPI, Query
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path.home() / "meritgiving" / "data" / "meritgiving.db"
app = FastAPI(title="MeritGiving API v2.0")

@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

@app.get("/")
def health():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM registry_enriched")
        reg = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM percentiles")
        pct = c.fetchone()[0]
    return {"status": "ok", "registry": reg, "percentiles": pct, "version": "2.0"}

@app.get("/search")
def search(q: str = Query(None), state: str = Query(None), ntee: str = Query(None), tier: str = Query(None), limit: int = Query(20)):
    with get_db() as conn:
        c = conn.cursor()
        sql = """
            SELECT r.EIN, r.NAME, r.STATE, r.CITY, r.NTEE1, r.REVENUE_AMT,
                   p.peer_percentile, p.national_percentile, p.tier
            FROM registry_enriched r
            JOIN percentiles p ON r.EIN = p.EIN
            WHERE 1=1
        """
        params = []
        if q:
            sql += " AND (r.NAME LIKE ? OR r.CITY LIKE ? OR r.EIN LIKE ?)"
            params.extend(["%" + q + "%", "%" + q + "%", "%" + q + "%"])
        if state:
            sql += " AND r.STATE = ?"
            params.append(state.upper())
        if ntee:
            sql += " AND r.NTEE1 LIKE ?"
            params.append("%" + ntee + "%")
        if tier:
            sql += " AND p.tier = ?"
            params.append(tier)
        sql += " ORDER BY p.peer_percentile DESC LIMIT ?"
        params.append(limit)
        c.execute(sql, params)
        rows = c.fetchall()
        return {"count": len(rows), "results": [dict(r) for r in rows]}

@app.get("/org/{ein}")
def get_org(ein: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT r.*, p.peer_percentile, p.national_percentile, p.tier
            FROM registry_enriched r
            JOIN percentiles p ON r.EIN = p.EIN
            WHERE r.EIN = ?
        """, (ein,))
        row = c.fetchone()
    return dict(row) if row else {"error": "Not found"}

@app.get("/top")
def top(limit: int = Query(20), state: str = Query(None), tier: str = Query(None)):
    with get_db() as conn:
        c = conn.cursor()
        sql = """
            SELECT r.EIN, r.NAME, r.STATE, r.REVENUE_AMT, p.peer_percentile, p.tier
            FROM registry_enriched r
            JOIN percentiles p ON r.EIN = p.EIN
        """
        params = []
        conditions = []
        if state:
            conditions.append("r.STATE = ?")
            params.append(state.upper())
        if tier:
            conditions.append("p.tier = ?")
            params.append(tier)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY p.peer_percentile DESC LIMIT ?"
        params.append(limit)
        c.execute(sql, params)
        return {"results": [dict(r) for r in c.fetchall()]}

@app.get("/stats")
def stats():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT STATE, COUNT(*) as c FROM registry_enriched GROUP BY STATE ORDER BY c DESC LIMIT 10")
        states = [dict(r) for r in c.fetchall()]
        c.execute("SELECT p.tier, COUNT(*) as c FROM percentiles p GROUP BY p.tier ORDER BY c DESC")
        tiers = [dict(r) for r in c.fetchall()]
        c.execute("""
            SELECT CASE WHEN r.REVENUE_AMT < 100000 THEN 'small'
                        WHEN r.REVENUE_AMT < 500000 THEN 'medium'
                        WHEN r.REVENUE_AMT < 1000000 THEN 'large'
                        WHEN r.REVENUE_AMT < 5000000 THEN 'major'
                        ELSE 'mega' END as band,
                   COUNT(*) as c
            FROM registry_enriched r GROUP BY band
        """)
        bands = [dict(r) for r in c.fetchall()]
    return {"top_states": states, "tier_distribution": tiers, "revenue_bands": bands}
