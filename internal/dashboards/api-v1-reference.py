"""MERIT API — FastAPI backend.

Data source: SQLite (local dev) → Neon Postgres (production).
DATABASE_URL env var controls which is used.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import sqlite3
from contextlib import contextmanager

app = FastAPI(
    title="MERIT API",
    version="0.1.0",
    description="Serves MERIT nonprofit data.",
)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3003").split(",")
DB_PATH = os.getenv("SQLITE_PATH", "/home/akbar/meritgiving/data/merit_registry.db")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _fmt_ein(ein: str) -> str:
    digits = ein.replace("-", "").zfill(9)
    return f"{digits[:2]}-{digits[2:]}"


def _row_to_org(row) -> dict:
    r = dict(row)
    ein = str(r.get("EIN", "") or "").zfill(9)
    return {
        "ein": ein,
        "ein_display": _fmt_ein(ein),
        "name": r.get("organization_name") or "",
        "city": r.get("CITY") or "",
        "state": r.get("STATE") or "",
        "zipcode": r.get("zipcode") or "",
        "ntee1": r.get("NTEE1") or "",
        "ntee_description": r.get("ntee_description") or "",
        "merit_score": r.get("merit_score"),
        "merit_tier": r.get("merit_tier") or "",
        "merit_band": r.get("merit_band") or "",
        "ntee1_percentile": r.get("ntee1_percentile"),
        "peer_percentile": r.get("peer_percentile"),
        "peer_total": r.get("peer_total"),
        "total_revenue": r.get("total_revenue"),
        "total_assets": r.get("total_assets"),
        "total_expenses": r.get("total_expenses"),
        "employee_count": r.get("employee_count"),
        "website": r.get("website") or "",
        "website_status": r.get("website_status") or "",
        "donate_url": r.get("donate_url") or "",
        "donate_platform": r.get("donate_platform") or "",
        "mission": r.get("mission") or "",
        "ruling_date": r.get("ruling_date") or "",
        "latest_tax_year": r.get("latest_tax_year"),
        "is_hidden_gem": bool(r.get("is_hidden_gem")),
        "source": r.get("source") or "",
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "merit-api", "version": "0.1.0"}


@app.get("/api/v1/orgs")
def list_orgs(
    q: Optional[str] = Query(None, description="Name search"),
    state: Optional[str] = Query(None, description="Two-letter state code"),
    ntee: Optional[str] = Query(None, description="NTEE1 category code (A-Z)"),
    min_score: Optional[float] = Query(None, description="Minimum merit_score"),
    hidden_gems: Optional[bool] = Query(None, description="Only hidden gems"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
):
    """Search and filter nonprofits."""
    conditions = []
    params: list = []

    if q:
        conditions.append("organization_name LIKE ?")
        params.append(f"%{q}%")
    if state:
        conditions.append("STATE = ?")
        params.append(state.upper())
    if ntee:
        conditions.append("NTEE1 = ?")
        params.append(ntee.upper())
    if min_score is not None:
        conditions.append("merit_score >= ?")
        params.append(min_score)
    if hidden_gems:
        conditions.append("is_hidden_gem = 1")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    offset = (page - 1) * per_page

    with get_db() as db:
        total = db.execute(
            f"SELECT COUNT(*) FROM registry_enriched {where}", params
        ).fetchone()[0]

        rows = db.execute(
            f"SELECT * FROM registry_enriched {where} "
            "ORDER BY merit_score DESC NULLS LAST "
            f"LIMIT ? OFFSET ?",
            params + [per_page, offset],
        ).fetchall()

    return {
        "orgs": [_row_to_org(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@app.get("/api/v1/orgs/{ein}")
def get_org(ein: str):
    """Fetch a single nonprofit by EIN."""
    clean = ein.replace("-", "").zfill(9)
    if len(clean) != 9 or not clean.isdigit():
        raise HTTPException(status_code=400, detail="Invalid EIN format")

    with get_db() as db:
        row = db.execute(
            "SELECT * FROM registry_enriched WHERE EIN = ?", [clean]
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Organization not found")

    return _row_to_org(row)


@app.get("/api/v1/stats")
def stats():
    """Public stats — used by /mission dashboard."""
    with get_db() as db:
        total = db.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
        scored = db.execute(
            "SELECT COUNT(*) FROM registry_enriched WHERE merit_score IS NOT NULL"
        ).fetchone()[0]
        states = db.execute(
            "SELECT COUNT(DISTINCT STATE) FROM registry_enriched WHERE STATE != ''"
        ).fetchone()[0]

        # Badge tiers are score ranges (not the lamp-metaphor merit_tier column)
        badge_q = db.execute("""
            SELECT
                SUM(CASE WHEN merit_score >= 90 THEN 1 ELSE 0 END) as exceptional,
                SUM(CASE WHEN merit_score >= 75 AND merit_score < 90 THEN 1 ELSE 0 END) as high,
                SUM(CASE WHEN merit_score >= 60 AND merit_score < 75 THEN 1 ELSE 0 END) as solid,
                SUM(CASE WHEN merit_score >= 40 AND merit_score < 60 THEN 1 ELSE 0 END) as developing,
                SUM(CASE WHEN merit_score < 40 THEN 1 ELSE 0 END) as needs_data
            FROM registry_enriched WHERE merit_score IS NOT NULL
        """).fetchone()

    return {
        "orgs_indexed": total,
        "orgs_scored": scored,
        "states_covered": states,
        "badge_counts": {
            "exceptional": badge_q[0] or 0,
            "high": badge_q[1] or 0,
            "solid": badge_q[2] or 0,
            "developing": badge_q[3] or 0,
            "needs_data": badge_q[4] or 0,
        },
        "last_ingest": None,
    }


@app.get("/api/v1/ntee")
def ntee_categories():
    """NTEE1 codes present in the database with org counts."""
    with get_db() as db:
        rows = db.execute(
            "SELECT NTEE1, ntee_description, COUNT(*) as count "
            "FROM registry_enriched WHERE NTEE1 != '' "
            "GROUP BY NTEE1, ntee_description ORDER BY NTEE1"
        ).fetchall()

    return {
        "categories": [
            {"code": r[0], "label": r[1] or r[0], "count": r[2]} for r in rows
        ]
    }
