import os

code = r'''
import csv, math, json, os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

app = FastAPI(title="MeritGiving")
BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
CSV_DIR = DATA_DIR / "csv"
CACHE_DIR = DATA_DIR / "propublica_cache"
CAT_DIR = DATA_DIR / "categories"
STATIC_DIR = BASE / "static"

ORGS = {}
PERCENTILE = {}
CATEGORIES = {}
MERIT = {}

NTEE_NAMES = {
    "A": "Arts, Culture & Humanities", "B": "Education",
    "C": "Environment", "D": "Animal-Related",
    "E": "Health Care", "F": "Mental Health & Crisis Intervention",
    "G": "Voluntary Health Associations & Medical Disciplines",
    "H": "Medical Research", "I": "Crime & Legal-Related",
    "J": "Employment", "K": "Food, Agriculture & Nutrition",
    "L": "Housing & Shelter", "M": "Public Safety, Disaster Preparedness & Relief",
    "N": "Recreation & Sports", "O": "Youth Development",
    "P": "Human Services", "Q": "International, Foreign Affairs & National Security",
    "R": "Civil Rights, Social Action & Advocacy",
    "S": "Community Improvement & Capacity Building",
    "T": "Philanthropy, Voluntarism & Grantmaking Foundations",
    "U": "Science & Technology", "V": "Social Science",
    "W": "Public & Societal Benefit", "X": "Religion, Spiritual Development",
    "Y": "Mutual & Membership Benefit", "Z": "Unknown / Unclassified",
    "0": "Uncategorized",
}

def load_master_orgs():
    path = DATA_DIR / "master_orgs.csv"
    if not path.exists():
        print("[FATAL] data/master_orgs.csv not found")
        return
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            ein = str(row.get("EIN") or row.get("ein") or "").strip()
            if not ein:
                continue
            ORGS[ein] = {
                "ein": ein,
                "name": row.get("NAME") or row.get("name") or "",
                "state": row.get("STATE") or row.get("state") or "",
                "city": row.get("CITY") or row.get("city") or "",
                "tax_year": row.get("YEAR") or row.get("year") or "",
                "revenue": row.get("REVENUE") or row.get("revenue") or "",
                "ntee": row.get("NTEE") or row.get("ntee") or "",
                "form_type": "990",
            }
            count += 1
            if count % 50000 == 0:
                print(f"  Loaded {count}...")
    print(f"[MASTER] Loaded {count} orgs")

def load_percentiles():
    path = CSV_DIR / "percentile_engine_v2.csv"
    if not path.exists():
        path = CSV_DIR / "percentile_engine_latest.csv"
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ein = (row.get("ein") or "").strip().lstrip("0")
            if ein:
                PERCENTILE[ein] = {
                    "percentile": row.get("percentile"),
                    "peer_group": row.get("peer_group"),
                    "peer_count": row.get("peer_count"),
                }

def load_categories():
    if not CAT_DIR.exists():
        return
    for f in CAT_DIR.glob("*.json"):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                key = f.stem
                CATEGORIES[key] = data if isinstance(data, list) else data.get("orgs", [])
        except Exception as e:
            print(f"[WARN] {f}: {e}")

def load_MERIT():
    path = DATA_DIR / "MERIT_cache.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            global MERIT
            MERIT = json.load(f)

@app.on_event("startup")
def startup():
    os.makedirs(STATIC_DIR, exist_ok=True)
    load_master_orgs()
    load_percentiles()
    load_categories()
    load_MERIT()
    print(f"[MERIT] {len(ORGS)} orgs | {len(PERCENTILE)} percentiles | {len(CATEGORIES)} categories | {len(MERIT)} MERIT")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

def render_base(title, content):
    t = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | MERIT</title>
<link rel="stylesheet" href="/static/css/merit.css">
</head>
<body>
<nav class="navbar"><div class="container"><a href="/" class="brand">MERIT</a><div class="nav-links"><a href="/">Directory</a><a href="/categories">Categories</a></div></div></nav>
<main class="container">{content}</main>
<footer class="footer"><div class="container"><p>MERIT Civic Giving Platform</p></div></footer>
</body></html>"""
    return t.replace("{title}", title).replace("{content}", content)

def score_color(score):
    if score >= 90: return "#d97706"
    if score >= 75: return "#2563eb"
    if score >= 60: return "#16a34a"
    if score >= 40: return "#ca8a04"
    return "#6b7280"

def score_label(score):
    if score >= 90: return "Exceptional Impact"
    if score >= 75: return "High Impact"
    if score >= 60: return "Solid Performer"
    if score >= 40: return "Developing"
    return "Unscored"

def render_home():
    cats = []
    for cid in sorted(CATEGORIES.keys()):
        name = NTEE_NAMES.get(cid, cid)
        cnt = len(CATEGORIES.get(cid, []))
        cats.append(f'<a href="/category/{cid}" class="cat-card"><h3>{name}</h3><span class="count">{cnt} orgs</span></a>')
    featured = []
    for ein, data in list(MERIT.items())[:6]:
        org = ORGS.get(ein, {})
        if org.get("name"):
            featured.append((ein, org, data))
    fcards = []
    for ein, org, data in featured:
        sc = int(float(data.get("score", 50)))
        fcards.append(f'<div class="org-card"><div class="org-score" style="background:{score_color(sc)}">{sc}</div><h4><a href="/org/{ein}">{org.get("name")}</a></h4><p class="meta">{org.get("city","")}, {org.get("state","")}</p></div>')
    states = len(set(o.get("state") for o in ORGS.values() if o.get("state")))
    c = f"""
    <div class="hero"><h1>Every nonprofit. Verified. Benchmarked.</h1><p class="lead">Research {len(ORGS):,}+ tax-deductible 501(c)(3) organizations.</p>
    <form action="/search" method="get" class="search-form"><input type="text" name="q" placeholder="Search by name..." class="search-input"><button type="submit" class="search-btn">Search</button></form></div>
    <div class="stats-bar"><div class="stat"><strong>{len(ORGS):,}</strong><span>Organizations</span></div><div class="stat"><strong>{len(CATEGORIES)}</strong><span>Categories</span></div><div class="stat"><strong>{states}</strong><span>States</span></div></div>
    <h2>Browse by Category</h2><div class="category-grid">{"".join(cats)}</div>
    <h2>Featured</h2><div class="org-grid">{"".join(fcards)}</div>"""
    return render_base("Directory", c)

def render_search(q, results):
    rows = []
    for r in results:
        ein = r["ein"]
        imp = MERIT.get(ein, {})
        sc = int(float(imp.get("score", 0)))
        rows.append(f'<div class="result-item"><div><h4><a href="/org/{ein}">{r["name"]}</a></h4><div class="result-meta">{r.get("city","")}, {r.get("state","")} • {r.get("ntee","")}</div></div><div class="result-score"><strong>{sc}</strong><span>Impact</span></div></div>')
    c = f'<div style="margin-bottom:24px;"><h1>Search: {q}</h1><p>{len(results)} results</p></div><div class="results-list">{"".join(rows)}</div>'
    return render_base(f"Search: {q}", c)

def render_org(ein, org, p, pp, MERIT):
    name = org.get("name", "Unknown")
    state = org.get("state", "")
    city = org.get("city", "")
    ntee = org.get("ntee", "")
    sc = int(float(MERIT.get("score", 50)))
    badges = MERIT.get("badges", "Verified Active").split("|")
    perc = p.get("percentile", "N/A") or "N/A"
    bhtml = "".join([f'<span class="badge">{b}</span>' for b in badges if b])
    c = f"""
    <div class="profile-header"><div class="badge-row">{bhtml}</div><h1>{name}</h1><div class="profile-meta">EIN: {ein} • {city}, {state}</div></div>
    <div class="profile-grid"><div><div class="mission"><p>Data sourced from IRS and ProPublica public records.</p></div></div>
    <div><div class="side-card" style="text-align:center;"><h3>MERIT Score</h3><div class="score-ring" style="background:conic-gradient({score_color(sc)} calc({sc}*1%), #e2e8f0 0);"><span>{sc}</span></div><p>{score_label(sc)}</p></div>
    <div class="side-card"><h3>Peer Benchmark</h3><div class="metric"><span>Percentile</span><strong>{perc}</strong></div></div></div></div>"""
    return render_base(name, c)

def render_categories():
    cards = []
    for cid in sorted(CATEGORIES.keys()):
        name = NTEE_NAMES.get(cid, cid)
        cnt = len(CATEGORIES.get(cid, []))
        cards.append(f'<a href="/category/{cid}" class="cat-card"><h3>{name}</h3><span class="count">{cnt} orgs</span></a>')
    c = f'<div class="hero"><h1>Browse by Category</h1></div><div class="category-grid">{"".join(cards)}</div>'
    return render_base("Categories", c)

def render_category(cat, items, name):
    rows = []
    for item in items[:50]:
        ein = str(item.get("EIN") or item.get("ein") or "").strip().lstrip("0")
        if not ein: continue
        org = ORGS.get(ein, {})
        imp = MERIT.get(ein, {})
        sc = int(float(imp.get("score", 0)))
        nm = org.get("name", item.get("NAME", "Unknown"))
        rows.append(f'<div class="result-item"><div><h4><a href="/org/{ein}">{nm}</a></h4></div><div class="result-score"><strong>{sc}</strong></div></div>')
    c = f'<div style="margin-bottom:24px;"><h1>{name}</h1><p>{len(items)} organizations</p></div><div class="results-list">{"".join(rows)}</div>'
    return render_base(name, c)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if "text/html" in request.headers.get("accept", ""):
        return HTMLResponse(content=render_home())
    return JSONResponse({"status": "ok", "orgs": len(ORGS), "categories": len(CATEGORIES)})

@app.get("/search")
def search(q: str = Query(..., min_length=1), limit: int = 20, request: Request = None):
    qlower = q.lower()
    results = []
    for ein, o in ORGS.items():
        if qlower in (o.get("name") or "").lower():
            p = PERCENTILE.get(ein, {})
            results.append({
                "ein": ein, "name": o["name"], "state": o.get("state"),
                "city": o.get("city"), "revenue": o.get("revenue"),
                "ntee": o.get("ntee"), "percentile": p.get("percentile"),
                "peer_group": p.get("peer_group"),
            })
            if len(results) >= limit:
                break
    if request and "text/html" in request.headers.get("accept", ""):
        return HTMLResponse(content=render_search(q, results))
    return {"query": q, "count": len(results), "results": results}

@app.get("/org/{ein}")
def org_detail(ein: str, request: Request = None):
    ein = ein.strip().lstrip("0")
    org = ORGS.get(ein)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    p = PERCENTILE.get(ein, {})
    pp = load_propublica(ein)
    MERIT = MERIT.get(ein, {"score": 50, "badges": "Verified Active"})
    if request and "text/html" in request.headers.get("accept", ""):
        return HTMLResponse(content=render_org(ein, org, p, pp, MERIT))
    return {"ein": ein, "profile": org, "percentile_data": p, "propublica": pp, "MERIT": MERIT}

@app.get("/categories")
def list_categories(request: Request = None):
    if request and "text/html" in request.headers.get("accept", ""):
        return HTMLResponse(content=render_categories())
    out = []
    for k in sorted(CATEGORIES.keys()):
        out.append({"id": k, "name": NTEE_NAMES.get(k, k), "count": len(CATEGORIES[k])})
    return {"categories": out, "count": len(out)}

@app.get("/category/{cat}")
def category_detail(cat: str, limit: int = 50, request: Request = None):
    major = cat[0].upper() if cat else ""
    items = CATEGORIES.get(major, [])
    name = NTEE_NAMES.get(major, major)
    if request and "text/html" in request.headers.get("accept", ""):
        return HTMLResponse(content=render_category(cat, items, name))
    return {"requested": cat, "resolved": major, "name": name, "count": len(items), "results": items[:limit]}

@app.get("/health")
def health():
    return {"status": "ok", "orgs": len(ORGS), "percentiles": len(PERCENTILE), "categories": len(CATEGORIES), "MERIT_scored": len(MERIT)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
'''

with open("app.py", "w", encoding="utf-8") as f:
    f.write(code)
print(f"[WRITE] app.py: {len(code)} chars, {code.count(chr(10))} lines")
