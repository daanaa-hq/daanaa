import sqlite3, csv, os, zipfile, urllib.request, sys
from datetime import datetime

DB = os.path.expanduser("~/meritgiving/data/merit_registry.db")
BASE = "https://www.irs.gov/pub/irs-soi/"

states = ["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC","PR"]

conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS irs_bmf (ein TEXT PRIMARY KEY, name TEXT, ico_name TEXT, street TEXT, city TEXT, state TEXT, zip TEXT, ntee TEXT, subsection TEXT, affiliation TEXT, ruling_date TEXT, deductibility TEXT, foundation TEXT, activity TEXT, organization TEXT, status TEXT, tax_period TEXT, asset_cd TEXT, income_cd TEXT, filing_req_cd TEXT, pf_filing_req_cd TEXT, acct_pd TEXT, asset_amt REAL, income_amt REAL, revenue_amt REAL, data_date TEXT)")
c.execute("DELETE FROM irs_bmf")

total = 0
for st in states:
    url = f"{BASE}{st.lower()}_exempt.csv"
    path = f"/tmp/{st.lower()}_exempt.csv"
    try:
        urllib.request.urlretrieve(url, path)
    except Exception as e:
        print(f"  {st}: SKIP ({e})")
        continue
    
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        batch = []
        for row in reader:
            batch.append((
                row.get("EIN",""), row.get("NAME",""), row.get("ICO",""), row.get("STREET",""),
                row.get("CITY",""), row.get("STATE",""), row.get("ZIP",""), row.get("NTEE_CD",""),
                row.get("SUBSECTION",""), row.get("AFFILIATION",""), row.get("RULING_DT",""),
                row.get("DEDUCTIBILITY",""), row.get("FOUNDATION",""), row.get("ACTIVITY",""),
                row.get("ORGANIZATION",""), row.get("STATUS",""), row.get("TAX_PERIOD",""),
                row.get("ASSET_CD",""), row.get("INCOME_CD",""), row.get("FILING_REQ_CD",""),
                row.get("PF_FILING_REQ_CD",""), row.get("ACCT_PD",""),
                float(row.get("ASSET_AMT",0) or 0), float(row.get("INCOME_AMT",0) or 0),
                float(row.get("REVENUE_AMT",0) or 0), str(datetime.now().date())
            ))
            if len(batch) >= 5000:
                c.executemany("INSERT OR REPLACE INTO irs_bmf VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
                conn.commit()
                total += len(batch)
                batch = []
        if batch:
            c.executemany("INSERT OR REPLACE INTO irs_bmf VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
            conn.commit()
            total += len(batch)
    print(f"  {st}: done | Running total: {total}")

conn.close()
print(f"[{datetime.now()}] BMF DONE: {total} orgs from {len(states)} states.")
