from fastapi import FastAPI, Query
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path.home() / "meritgiving" / "data" / "meritgiving.db"
app = FastAPI(title="MeritGiving API")

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
        c.execute("SELECT COUNT(*) FROM scores")
        scr = c.fetchone()[0]
    return {"status": "ok", "registry": reg, "scored": scr}

@app.get("/search")
def search(q: str = Query(None), state: str = Query(None), ntee: str = Query(None), min_score: float = Query(0), limit: int = Query(20)):
    with get_db() as conn:
        c = conn.cursor()
        sql = "SELECT r.EIN, r.NAME, r.STATE, r.CITY, r.NTEE1, r.REVENUE_AMT, s.merit_score FROM registry_enriched r JOIN scores s ON r.EIN=s.EIN WHERE 1=1"
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
        if min_score > 0:
            sql += " AND s.merit_score >= ?"
            params.append(min_score)
        sql += " ORDER BY s.merit_score DESC LIMIT ?"
        params.append(limit)
        c.execute(sql, params)
        return {"count": len(rows := c.fetchall()), "results": [dict(r) for r in rows]}

@app.get("/org/{ein}")
def get_org(ein: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT r.*, s.* FROM registry_enriched r JOIN scores s ON r.EIN=s.EIN WHERE r.EIN=?", (ein,))
        row = c.fetchone()
        return dict(row) if row else {"error": "Not found"}

@app.get("/top")
def top(limit: int = Query(20), state: str = Query(None)):
    with get_db() as conn:
        c = conn.cursor()
        sql = "SELECT r.EIN, r.NAME, r.STATE, r.REVENUE_AMT, s.merit_score FROM registry_enriched r JOIN scores s ON r.EIN=s.EIN"
        params = []
        if state:
            sql += " WHERE r.STATE=?"
            params.append(state.upper())
        sql += " ORDER BY s.merit_score DESC LIMIT ?"
        params.append(limit)
        c.execute(sql, params)
        return {"results": [dict(r) for r in c.fetchall()]}

@app.get("/stats")
def stats():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT STATE, COUNT(*) as c FROM registry_enriched GROUP BY STATE ORDER BY c DESC LIMIT 10")
        states = [dict(r) for r in c.fetchall()]
        c.execute("SELECT NTEE1, COUNT(*) as c FROM registry_enriched WHERE NTEE1 IS NOT NULL GROUP BY NTEE1 ORDER BY c DESC LIMIT 10")
        ntees = [dict(r) for r in c.fetchall()]
        c.execute("SELECT CASE WHEN REVENUE_AMT<100000 THEN 'small' WHEN REVENUE_AMT<500000 THEN 'medium' WHEN REVENUE_AMT<1000000 THEN 'large' WHEN REVENUE_AMT<5000000 THEN 'major' ELSE 'mega' END as band, COUNT(*) as c FROM registry_enriched GROUP BY band")
        bands = [dict(r) for r in c.fetchall()]
    return {"top_states": states, "top_ntee": ntees, "revenue_bands": bands}
