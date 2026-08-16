#!/usr/bin/env python3
# Credential scrubbed 2026-06-09. DATABASE_URL now comes only from env or a
# gitignored .env file (see DB_URL loading below). Legacy TiDB pipeline (retired).
import os, sys, csv, json, time
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

BASE = Path.home() / "meritgiving"
DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    for line in open(BASE / ".env"):
        if line.startswith("DATABASE_URL="):
            DB_URL = line.strip().split("=",1)[1].strip().strip('"').strip("'"); break
if not DB_URL: print("Set DATABASE_URL"); sys.exit(1)
p = urlparse(DB_URL.replace("mysql://","http://"))
DB = {"host":p.hostname,"port":p.port or 4000,"user":p.username,"password":p.password,"database":p.path.lstrip("/")}
try: import pymysql
except: os.system(f"{sys.executable} -m pip install pymysql -q"); import pymysql

FOUNDATION = {10:"Church",11:"School",12:"Hospital",15:"Public Charity",16:"Supporting Org",17:"Public Charity",18:"Public Charity",2:"Private Foundation",3:"Private Foundation",4:"Private Foundation",9:"Supporting Org"}
STATUS = {1:"Active",2:"Conditional",7:"Revoked",12:"Filing Required",14:"Auto-Revoked"}
NTEE_CAT = {"A":"Arts","B":"Education","C":"Environment","D":"Animal","E":"Health","F":"Mental Health","G":"Voluntary Health","H":"Medical Research","I":"Crime/Legal","J":"Employment","K":"Food","L":"Housing","M":"Public Safety","N":"Recreation","O":"Youth","P":"Human Services","Q":"International","R":"Civil Rights","S":"Community","T":"Philanthropy","U":"Science","V":"Social Science","W":"Public Benefit","X":"Religion","Y":"Mutual","Z":"Unknown"}

def connect():
    ssl = DB_URL.split("ssl=")[1] if "ssl=" in DB_URL else None
    s = {"rejectUnauthorized":True} if ssl and "true" in ssl.lower() else None
    return pymysql.connect(host=DB["host"],port=DB["port"],user=DB["user"],password=DB["password"],database=DB["database"],charset="utf8mb4",autocommit=False,ssl=s,connect_timeout=30)

def load_csv(path, key):
    d={}
    with open(path,"r",encoding="utf-8",errors="ignore") as f:
        for r in csv.DictReader(f):
            k=r.get(key,r.get(key.upper(),"")).strip()
            if k: d[k]=r
    return d
def load_json(path):
    try:
        with open(path) as f: d=json.load(f)
        return {o["ein"]:o for o in d["orgs"]} if isinstance(d,dict) and "orgs" in d else {k:v for k,v in d.items() if isinstance(v,dict)}
    except: return {}
def load_pp(ein):
    try:
        with open(BASE/"data/propublica_cache"/f"{ein}.json","r",encoding="utf-8",errors="ignore") as f: return json.load(f)
    except: return None

def build_row(ein, master, merit_scores, percentiles):
    m=master; pp=load_pp(ein); org=pp.get("organization",{}) if pp else {}; filings=pp.get("filings_with_data",[]) if pp else []
    merit=merit_scores.get(ein,{}); perc=percentiles.get(ein,{})
    name=m.get("NAME",m.get("name",""))[:500]
    city=(m.get("CITY","") or org.get("city",""))[:100]
    state=(m.get("STATE","") or org.get("state",""))[:10]
    ntee=(m.get("NTEE","") or org.get("ntee_code",""))[:20]
    ntee_c=(ntee[0] if ntee else "0").upper()
    revenue=org.get("revenue_amount"); assets=org.get("asset_amount"); income=org.get("income_amount")
    ruling=org.get("ruling_date"); yr=int(str(ruling)[:4]) if ruling and str(ruling)[:4].isdigit() else None
    fc=org.get("foundation_code"); sc=org.get("subsection_code"); stc=org.get("exempt_organization_status_code")
    careof=org.get("careofname",""); careof=careof.lstrip("% ").strip() if careof and isinstance(careof,str) else ""
    rev_calc=revenue or (filings[0]["totrevenue"] if filings else 0) or 0
    exp=filings[0]["totfuncexpns"] if filings else 0
    prog=filings[0].get("prgmservrev",0) if filings else 0
    pe=round((prog/rev_calc)*100) if rev_calc>0 else 0
    fr=round((filings[0].get("totcntrbs",0)/rev_calc)*100) if rev_calc>0 and filings else 0
    or_=round((filings[0]["totassetsend"]/exp)*12) if exp>0 and filings else 0
    tx=min(100,40+(30 if org.get("have_extracts") else 0)+(15 if len(filings)>2 else 0)+(15 if len(filings)>4 else 0))
    ms=merit.get("score") if isinstance(merit,dict) else None
    mb=merit.get("badges","") if isinstance(merit,dict) else ""
    pv=perc.get("percentile","") if isinstance(perc,dict) else ""
    pg=perc.get("peer_group","") if isinstance(perc,dict) else ""
    pdfs=json.dumps([f["pdf_url"] for f in filings if f.get("pdf_url")][:5])
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (ein,name,org.get("sort_name","")[:500],careof or None,org.get("address") or None,city or None,state or None,org.get("zipcode") or None,ntee or None,ntee_c,sc,fc,FOUNDATION.get(fc) if fc else None,stc,STATUS.get(stc,f"S{stc}"),ruling,yr,revenue,assets,income,ms,mb[:255] if mb else None,str(pv)[:20] if pv else None,pg[:100] if pg else None,pe,fr,or_,tx,bool(org.get("have_extracts")),bool(org.get("have_pdfs")),pdfs,now,now,now)

def main():
    print("="*60); print("  MERIT Batch Importer"); print(f"  DB: {DB['host']}:{DB['port']}"); print("="*60)
    MASTER_CSV=BASE/"data/master_orgs.csv"
    if not MASTER_CSV.exists(): print(f"ERROR: {MASTER_CSV} not found"); sys.exit(1)
    master=load_csv(MASTER_CSV,"ein"); merit=load_json(BASE/"data/MERIT_cache.json")
    perc=load_csv(BASE/"data/percentile_engine_v2.csv","ein") if (BASE/"data/percentile_engine_v2.csv").exists() else {}
    total=len(master); print(f"\nTotal: {total:,}")
    conn=connect(); cur=conn.cursor(); cur.execute("SELECT COUNT(*) FROM organizations"); print(f"Existing: {cur.fetchone()[0]:,}")
    SQL="""INSERT INTO organizations (ein,name,sort_name,careofname,address,city,state,zipcode,ntee_code,ntee_category,subsection_code,foundation_code,foundation_type,status_code,status,ruling_date,year_founded,revenue,assets,income,merit_score,merit_badges,percentile,peer_group,program_efficiency,fundraising_ratio,operating_reserve,transparency_score,have_extracts,have_pdfs,pdf_urls,created_at,updated_at,last_synced_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE name=VALUES(name),city=VALUES(city),state=VALUES(state),revenue=VALUES(revenue),assets=VALUES(assets),income=VALUES(income),merit_score=VALUES(merit_score),merit_badges=VALUES(merit_badges),ntee_code=VALUES(ntee_code),ntee_category=VALUES(ntee_category),year_founded=VALUES(year_founded),foundation_type=VALUES(foundation_type),status=VALUES(status),have_extracts=VALUES(have_extracts),have_pdfs=VALUES(have_pdfs),pdf_urls=VALUES(pdf_urls),program_efficiency=VALUES(program_efficiency),updated_at=VALUES(updated_at),last_synced_at=VALUES(last_synced_at)"""
    BATCH=500; eins=list(master.keys()); imported=0; t0=time.time()
    print(f"\nImporting (batch={BATCH})...")
    for i in range(0,len(eins),BATCH):
        batch=eins[i:i+BATCH]
        try:
            rows=[r for r in (build_row(e,master[e],merit,perc) for e in batch) if r]
            if rows: cur.executemany(SQL,rows); conn.commit(); imported+=len(rows)
            if (i//BATCH)%20==0:
                el=time.time()-t0; rate=imported/el if el>0 else 0
                print(f"  {(i/len(eins))*100:.1f}% | {imported:,} | {rate:.0f}/s | ETA {(len(eins)-i)/rate/60:.0f}m")
        except Exception as e: conn.rollback(); print(f"  ERR: {e}") if i<10000 else None
    el=time.time()-t0; cur.execute("SELECT COUNT(*) FROM organizations"); final=cur.fetchone()[0]
    cur.close(); conn.close()
    print(f"\n{'='*60}\nDONE | Imported: {imported:,} | Time: {el/60:.1f}m | DB: {final:,}\n{'='*60}")

if __name__=="__main__":
    main()
