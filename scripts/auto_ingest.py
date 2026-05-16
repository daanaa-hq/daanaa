import os, sys, csv, json, time, math, requests, statistics
import sqlite3
from pathlib import Path
from collections import defaultdict

BASE = Path.home() / "meritgiving"
DB_PATH = BASE / "data" / "db" / "merit.db"
PROGRESS_FILE = BASE / "data" / "ingest_progress.json"
LOG_FILE = BASE / "logs" / "auto_ingest.log"

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + chr(10))

def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"total_ingested": 0, "last_ein": None, "errors": 0, "rebalance_count": 0}

def save_progress(p):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(p, f)

def get_db_count():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM organizations")
    count = c.fetchone()[0]
    conn.close()
    return count

def fetch_propublica(ein):
    try:
        url = f"https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 429:
            log(f"Rate limited on {ein}, sleeping 60s...")
            time.sleep(60)
            return fetch_propublica(ein)
        return None
    except Exception as e:
        return None

def extract_org_data(data):
    result = {}
    org = data.get("organization", {})
    result["name"] = org.get("name", "")
    result["city"] = org.get("city", "")
    result["state"] = org.get("state", "")
    result["ntee"] = org.get("ntee_code", "")
    result["ntee_major"] = result["ntee"][0].upper() if result["ntee"] else None
    result["website"] = org.get("website", "")
    filings = data.get("filings_with_data", [])
    if filings:
        latest = filings[0]
        result["tax_year"] = latest.get("tax_prd_yr")
        result["revenue"] = latest.get("totrevenue")
        result["total_expenses"] = latest.get("totfuncexpns")
        result["net_assets"] = latest.get("netassetsendyear")
        result["total_assets"] = latest.get("totassetsend")
        result["program_expenses"] = latest.get("totprogrevnue")
    return {k: v for k, v in result.items() if v is not None and v != ""}

def ingest_org(ein, source="propublica"):
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT ein FROM organizations WHERE ein = ?", (ein,))
    if c.fetchone():
        conn.close()
        return "exists"
    data = fetch_propublica(ein)
    if not data:
        conn.close()
        return "not_found"
    org = extract_org_data(data)
    if not org.get("name"):
        conn.close()
        return "no_data"
    c.execute("INSERT INTO organizations (ein, name, city, state, ntee, ntee_major, tax_year, revenue, total_expenses, program_expenses, total_assets, net_assets, website, data_source, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (ein, org.get("name"), org.get("city"), org.get("state"), org.get("ntee"), org.get("ntee_major"), org.get("tax_year"), org.get("revenue"), org.get("total_expenses"), org.get("program_expenses"), org.get("total_assets"), org.get("net_assets"), org.get("website"), source, time.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return "added"

def calculate_gauges(org):
    revenue = org.get("revenue") or 0
    total_expenses = org.get("total_expenses") or 0
    program_expenses = org.get("program_expenses") or 0
    total_assets = org.get("total_assets") or 0
    net_assets = org.get("net_assets") or 0
    tax_year = org.get("tax_year") or 0
    has_real_expenses = total_expenses > 0
    has_real_program = program_expenses > 0
    has_real_assets = total_assets > 0 and net_assets > 0
    if revenue > 0 and not has_real_expenses:
        total_expenses = revenue * 0.95
    if revenue > 0 and not has_real_program:
        program_expenses = total_expenses * 0.75
    if revenue > 0 and not has_real_assets:
        total_assets = revenue * 2.5
        net_assets = revenue * 0.8
    if total_expenses > 0:
        monthly = total_expenses / 12
        runway = net_assets / monthly if monthly > 0 else 0
    else:
        runway = 0
    if runway >= 24: fh = 100
    elif runway >= 12: fh = 85
    elif runway >= 6: fh = 70
    elif runway >= 3: fh = 50
    elif runway > 0: fh = 30
    else:
        if revenue > 0 and total_assets > 0:
            ratio = total_assets / revenue
            if ratio >= 5: fh = 85
            elif ratio >= 2: fh = 65
            elif ratio >= 1: fh = 45
            else: fh = 25
        else: fh = 0
    if total_expenses > 0 and program_expenses > 0:
        oe = min(100, max(0, int((program_expenses / total_expenses) * 100)))
    elif revenue > 0:
        if revenue >= 10_000_000: oe = 82
        elif revenue >= 1_000_000: oe = 78
        elif revenue >= 100_000: oe = 75
        else: oe = 72
    else: oe = 0
    if revenue > 0:
        if revenue >= 100_000_000: st = 95
        elif revenue >= 10_000_000: st = 85
        elif revenue >= 1_000_000: st = 70
        elif revenue >= 100_000: st = 50
        elif revenue >= 10_000: st = 35
        else: st = 20
    else: st = 0
    sp = 50
    if tax_year >= 2023: comp = 100
    elif tax_year >= 2022: comp = 90
    elif tax_year >= 2021: comp = 75
    elif tax_year >= 2020: comp = 60
    elif tax_year > 0: comp = 40
    else: comp = 0
    MERIT = int(round(fh * 0.25 + oe * 0.25 + st * 0.20 + sp * 0.20 + comp * 0.10))
    return {"MERIT_score": MERIT, "financial_health": fh, "operational_efficiency": oe, "scale_trajectory": st, "sector_position": sp, "compliance": comp}

def rebalance_scoring():
    log("=== REBALANCING ALL SCORES ===")
    start = time.time()
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT * FROM organizations")
    rows = c.fetchall()
    cols = [d[0] for d in c.description]
    orgs = [dict(zip(cols, row)) for row in rows]
    log(f"Loaded {len(orgs)} orgs")
    cohorts = defaultdict(list)
    for org in orgs:
        major = org.get("ntee_major") or "Z"
        cohorts[major].append(org)
    for major, group in cohorts.items():
        revs = [(i, org.get("revenue") or 0) for i, org in enumerate(group)]
        revs.sort(key=lambda x: x[1])
        n = len(revs)
        for rank, (idx, _) in enumerate(revs):
            pct = (rank / (n - 1)) * 100 if n > 1 else 50.0
            group[idx]["percentile"] = round(pct, 1)
    all_orgs = []
    for g in cohorts.values():
        all_orgs.extend(g)
    scores = []
    for org in all_orgs:
        g = calculate_gauges(org)
        org.update(g)
        scores.append(g)
    for org in all_orgs:
        c.execute("UPDATE organizations SET percentile = ?, MERIT_score = ?, financial_health = ?, operational_efficiency = ?, scale_trajectory = ?, sector_position = ?, compliance = ?, updated_at = ? WHERE ein = ?", (org.get("percentile"), org.get("MERIT_score"), org.get("financial_health"), org.get("operational_efficiency"), org.get("scale_trajectory"), org.get("sector_position"), org.get("compliance"), time.strftime("%Y-%m-%d %H:%M:%S"), org["ein"]))
    fh_vals = [s["financial_health"] for s in scores]
    oe_vals = [s["operational_efficiency"] for s in scores]
    st_vals = [s["scale_trajectory"] for s in scores]
    sp_vals = [s["sector_position"] for s in scores]
    comp_vals = [s["compliance"] for s in scores]
    imp_vals = [s["MERIT_score"] for s in scores]
    c.execute("INSERT INTO scoring_runs (org_count, fh_mean, fh_std, oe_mean, oe_std, st_mean, st_std, sp_mean, sp_std, comp_mean, comp_std, MERIT_mean, MERIT_std) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (len(orgs), statistics.mean(fh_vals), statistics.pstdev(fh_vals), statistics.mean(oe_vals), statistics.pstdev(oe_vals), statistics.mean(st_vals), statistics.pstdev(st_vals), statistics.mean(sp_vals), statistics.pstdev(sp_vals), statistics.mean(comp_vals), statistics.pstdev(comp_vals), statistics.mean(imp_vals), statistics.pstdev(imp_vals)))
    conn.commit()
    conn.close()
    elapsed = time.time() - start
    log(f"Rebalanced {len(orgs)} orgs in {elapsed:.1f}s")
    log(f"  Impact mean: {statistics.mean(imp_vals):.1f} (std: {statistics.pstdev(imp_vals):.1f})")
    log(f"  Financial Health mean: {statistics.mean(fh_vals):.1f}")
    log(f"  Operational Eff mean: {statistics.mean(oe_vals):.1f}")

def export_to_csv():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT * FROM organizations")
    rows = c.fetchall()
    cols = [d[0] for d in c.description]
    output = BASE / "data" / "csv" / "master_orgs.csv"
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(zip(cols, row)))
    conn.close()
    log(f"Exported {len(rows)} orgs to CSV")

def generate_ein_pool():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT ein FROM organizations ORDER BY RANDOM() LIMIT 50")
    existing = [r[0] for r in c.fetchall()]
    conn.close()
    pool = []
    for ein in existing:
        prefix = ein[:2]
        base = int(ein[2:7])
        for i in range(1, 21):
            new_num = base + i
            new_ein = f"{prefix}{str(new_num).zfill(7)}"
            if len(new_ein) == 9:
                pool.append(new_ein)
    return list(set(pool))[:500]

def main(batch_size=100, rebalance_threshold=1000):
    log("=" * 60)
    log("MERIT Auto-Ingestion Engine v2.0")
    log("=" * 60)
    progress = load_progress()
    start_count = get_db_count()
    log(f"Database: {start_count} orgs | Rebalances: {progress['rebalance_count']}")
    if progress["rebalance_count"] == 0 and start_count > 0:
        rebalance_scoring()
        export_to_csv()
        progress["rebalance_count"] += 1
        save_progress(progress)
    pool = generate_ein_pool()
    log(f"Pool: {len(pool)} candidates")
    added = 0
    for ein in pool:
        if added >= batch_size:
            break
        result = ingest_org(ein)
        if result == "added":
            added += 1
            progress["total_ingested"] += 1
            progress["last_ein"] = ein
            log(f"[{added}/{batch_size}] + {ein}")
        elif result == "exists":
            pass
        else:
            progress["errors"] += 1
        if added < batch_size:
            time.sleep(1.5)
    log(f"Added {added} orgs")
    new_count = get_db_count()
    if added > 0 and (new_count % rebalance_threshold < batch_size or progress["rebalance_count"] == 0):
        log(f"Triggering rebalance at {new_count} orgs")
        rebalance_scoring()
        export_to_csv()
        progress["rebalance_count"] += 1
    save_progress(progress)
    log(f"Total: {new_count} orgs | Ingested: {progress['total_ingested']}")
    log("=" * 60)

if __name__ == "__main__":
    batch = int(os.environ.get("INGEST_BATCH", "100"))
    threshold = int(os.environ.get("REBALANCE_THRESHOLD", "1000"))
    main(batch, threshold)