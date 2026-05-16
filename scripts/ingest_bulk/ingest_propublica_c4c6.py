import sqlite3, requests, time, os
from datetime import datetime

DB = os.path.expanduser("~/meritgiving/data/merit_state.db")
API = "https://projects.propublica.org/nonprofits/api/v2/search.json"

conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS propublica_c4c6 (ein TEXT PRIMARY KEY, name TEXT, city TEXT, state TEXT, ntee TEXT, subsection TEXT, data TEXT, fetched TEXT)")
c.execute("CREATE INDEX IF NOT EXISTS idx_pp_c4c6_state ON propublica_c4c6(state)")

# Get all EINs FROM registry_enriched that are NOT c3 and NOT already in this table
c.execute("SELECT ein FROM irs_bmf WHERE subsection IN ('04','06') AND ein NOT IN (SELECT ein FROM propublica_c4c6)")
eins = [r[0] for r in c.fetchall()]
print(f"[{datetime.now()}] {len(eins)} C4/C6 EINs to fetch")

for i, ein in enumerate(eins):
    try:
        r = requests.get(f"{API}?q=ein:{ein}", timeout=15)
        data = r.json()
        orgs = data.get("organizations", [])
        if orgs:
            o = orgs[0]
            c.execute("INSERT OR REPLACE INTO propublica_c4c6 VALUES (?,?,?,?,?,?,?,?)",
                (ein, o.get("name"), o.get("city"), o.get("state"), o.get("ntee_code"), o.get("subsection"), str(data), str(datetime.now())))
        else:
            c.execute("INSERT OR REPLACE INTO propublica_c4c6 VALUES (?,?,?,?,?,?,?,?)",
                (ein, None, None, None, None, None, "{}", str(datetime.now())))
        if i % 100 == 0:
            conn.commit()
            print(f"  ... {i}/{len(eins)}")
        time.sleep(0.5)
    except Exception as e:
        print(f"  {ein}: ERROR {e}")
        time.sleep(2)

conn.commit()
conn.close()
print(f"[{datetime.now()}] C4/C6 DONE: {len(eins)} processed.")
