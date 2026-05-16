import sqlite3, csv, os, zipfile, urllib.request, sys
from datetime import datetime

DB = os.path.expanduser("~/meritgiving/data/merit_registry.db")
ZIP_URL = "https://www.irs.gov/pub/irs-soi/eo_postcard.zip"
ZIP_PATH = "/tmp/eo_postcard.zip"

print(f"[{datetime.now()}] Downloading 990-N e-Postcard data...")
urllib.request.urlretrieve(ZIP_URL, ZIP_PATH)
with zipfile.ZipFile(ZIP_PATH, 'r') as z:
    z.extractall("/tmp/")

txt_file = None
for f in os.listdir("/tmp"):
    if f.startswith("eo") and f.endswith(".txt") and "post" in f.lower():
        txt_file = f"/tmp/{f}"
        break

if not txt_file:
    print("ERROR: Could not find extracted postcard file")
    sys.exit(1)

print(f"[{datetime.now()}] Ingesting e-Postcards into {DB}...")
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS irs_epostcard (ein TEXT PRIMARY KEY, name TEXT, address TEXT, city TEXT, state TEXT, zip TEXT, tax_year TEXT, data_date TEXT)")
c.execute("DELETE FROM irs_epostcard")

with open(txt_file, 'r', encoding='utf-8', errors='replace') as f:
    reader = csv.reader(f, delimiter='|')
    batch = []
    total = 0
    for row in reader:
        if len(row) < 7:
            continue
        batch.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], str(datetime.now().date())))
        if len(batch) >= 5000:
            c.executemany("INSERT OR REPLACE INTO irs_epostcard VALUES (?,?,?,?,?,?,?,?)", batch)
            conn.commit()
            total += len(batch)
            batch = []
            if total % 50000 == 0:
                print(f"  ... {total} rows")
    if batch:
        c.executemany("INSERT OR REPLACE INTO irs_epostcard VALUES (?,?,?,?,?,?,?,?)", batch)
        conn.commit()
        total += len(batch)

conn.close()
print(f"[{datetime.now()}] e-Postcard DONE: {total} small orgs ingested.")
