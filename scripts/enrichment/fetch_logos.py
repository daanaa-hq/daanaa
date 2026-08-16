#!/usr/bin/env python3
import os, csv, json, time, requests
from pathlib import Path

BASE = Path.home() / "meritgiving"
MASTER_CSV = BASE / "data" / "csv" / "master_orgs.csv"
PROGRESS_FILE = BASE / "data" / "logo_progress.json"
PLACEHOLDER_DIR = BASE / "static" / "placeholders"

def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"completed": [], "errors": 0}

def save_progress(p):
    p["completed"] = list(p["completed"])
    with open(PROGRESS_FILE, "w") as f:
        json.dump(p, f)

def fetch_logo(ein):
    try:
        url = "https://projects.propublica.org/nonprofits/api/v2/organizations/" + ein + ".json"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            org = data.get("organization", {})
            logo = org.get("logo_url")
            if logo:
                return logo
        elif r.status_code == 429:
            time.sleep(60)
            return fetch_logo(ein)
    except:
        pass
    return None

def main(limit=500):
    p = load_progress()
    completed = set(p["completed"])
    
    rows = []
    with open(MASTER_CSV, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        if "LOGO_URL" not in fieldnames:
            fieldnames.append("LOGO_URL")
        for row in reader:
            rows.append(row)
    
    todo = []
    for row in rows:
        ein = str(row.get("EIN", "")).strip()
        if ein and ein not in completed:
            todo.append(ein)
    
    print("Total: " + str(len(rows)) + " | Need logos: " + str(len(todo)) + " | Will fetch: " + str(min(limit, len(todo))))
    
    fetched = 0
    for ein in todo[:limit]:
        print("[" + str(fetched+1) + "/" + str(limit) + "] " + ein + "...")
        logo = fetch_logo(ein)
        if logo:
            updated = 0
            for row in rows:
                if str(row.get("EIN", "")).strip() == ein:
                    row["LOGO_URL"] = logo
                    updated += 1
            print("  Logo found: " + logo[:60])
        else:
            p["errors"] += 1
            print("  No logo")
        
        completed.add(ein)
        fetched += 1
        if fetched < limit:
            time.sleep(1.5)
    
    # Normalize
    for row in rows:
        for k in fieldnames:
            if k not in row:
                row[k] = ""
    
    output = MASTER_CSV.with_suffix(".csv.logo")
    with open(output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    
    backup = MASTER_CSV.with_suffix(".csv.prelogo")
    os.rename(MASTER_CSV, backup)
    os.rename(output, MASTER_CSV)
    
    p["completed"] = list(completed)
    save_progress(p)
    print("Done! Fetched " + str(fetched) + " logos. Errors: " + str(p["errors"]))

if __name__ == "__main__":
    limit = int(os.environ.get("LOGO_LIMIT", "500"))
    main(limit)
