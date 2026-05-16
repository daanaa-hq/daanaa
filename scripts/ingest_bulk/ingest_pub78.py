import sqlite3, csv, os, zipfile, urllib.request, sys
from datetime import datetime

DB = os.path.expanduser("~/meritgiving/data/merit_registry.db")
ZIP_URL = "https://www.irs.gov/pub/irs-soi/eo_info.zip"
ZIP_PATH = "/tmp/eo_info.zip"
TXT_PATH = "/tmp/eo_info.txt"

print(f"[{datetime.now()}] Downloading Pub 78...")
urllib.request.urlretrieve(ZIP_URL, ZIP_PATH)
with zipfile.ZipFile(ZIP_PATH, 'r') as z:
    z.extractall("/tmp/")
    # Find the extracted file
    for f in z.namelist():
        if f.endswith('.txt'):
            TXT_PATH = f"/tmp/{f}"
            break

print(f"[{datetime.now()}] Ingesting into {DB}...")
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS irs_pub78 (ein TEXT PRIMARY KEY, name TEXT, city TEXT, state TEXT, country TEXT, deductibility_code TEXT, data_date TEXT)")
c.execute("CREATE INDEX IF NOT EXISTS idx_pub78_state ON irs_pub78(state)")
c.execute("DELETE FROM irs_pub78")

with open(TXT_PATH, 'r', encoding='utf-8', errors='replace') as f:
    reader = csv.reader(f, delimiter='|')
    batch = []
    total = 0
    for row in reader:
        if len(row) < 6:
            continue
        batch.append((row[0], row[1], row[3], row[4], row[5], row[6], str(datetime.now().date())))
        if len(batch) >= 5000:
            c.executemany("INSERT OR REPLACE INTO irs_pub78 VALUES (?,?,?,?,?,?,?)", batch)
            conn.commit()
            total += len(batch)
            batch = []
            if total % 50000 == 0:
                print(f"  ... {total} rows")
    if batch:
        c.executemany("INSERT OR REPLACE INTO irs_pub78 VALUES (?,?,?,?,?,?,?)", batch)
        conn.commit()
        total += len(batch)

conn.close()
print(f"[{datetime.now()}] Pub 78 DONE: {total} orgs ingested.")
