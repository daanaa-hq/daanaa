import sqlite3, csv, os, zipfile, urllib.request, sys
from datetime import datetime

DB = os.path.expanduser("~/meritgiving/data/merit_registry.db")
ZIP_URL = "https://www.irs.gov/pub/irs-soi/eo_rev.zip"
ZIP_PATH = "/tmp/eo_rev.zip"

print(f"[{datetime.now()}] Downloading Auto-Revocation list...")
urllib.request.urlretrieve(ZIP_URL, ZIP_PATH)
with zipfile.ZipFile(ZIP_PATH, 'r') as z:
    z.extractall("/tmp/")

txt_file = None
for f in os.listdir("/tmp"):
    if f.startswith("eo") and f.endswith(".txt") and "rev" in f.lower():
        txt_file = f"/tmp/{f}"
        break

if not txt_file:
    print("ERROR: Could not find extracted revocation file")
    sys.exit(1)

print(f"[{datetime.now()}] Ingesting revocations into {DB}...")
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS irs_revocations (ein TEXT PRIMARY KEY, name TEXT, city TEXT, state TEXT, zip TEXT, country TEXT, exemption_type TEXT, revocation_date TEXT, data_date TEXT)")
c.execute("DELETE FROM irs_revocations")

with open(txt_file, 'r', encoding='utf-8', errors='replace') as f:
    reader = csv.reader(f, delimiter='|')
    batch = []
    total = 0
    for row in reader:
        if len(row) < 8:
            continue
        batch.append((row[0], row[1], row[3], row[4], row[5], row[6], row[7], row[8], str(datetime.now().date())))
        if len(batch) >= 5000:
            c.executemany("INSERT OR REPLACE INTO irs_revocations VALUES (?,?,?,?,?,?,?,?,?)", batch)
            conn.commit()
            total += len(batch)
            batch = []
            if total % 50000 == 0:
                print(f"  ... {total} rows")
    if batch:
        c.executemany("INSERT OR REPLACE INTO irs_revocations VALUES (?,?,?,?,?,?,?,?,?)", batch)
        conn.commit()
        total += len(batch)

conn.close()
print(f"[{datetime.now()}] Revocations DONE: {total} dead orgs flagged.")
