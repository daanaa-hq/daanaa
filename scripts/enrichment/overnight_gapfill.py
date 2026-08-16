#!/usr/bin/env python3
import sqlite3,requests,time,os,sys
from datetime import datetime
DB=os.path.expanduser("~/meritgiving/data/merit_registry.db")
LOGD=os.path.expanduser("~/meritgiving/logs")
os.makedirs(LOGD,exist_ok=True)
LP=os.path.join(LOGD,"ovn_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".log")
PP="https://projects.propublica.org/nonprofits/api/v2"
BMF=os.path.expanduser("~/meritgiving/data/irs_bmf_latest.csv")
NCCS=os.path.expanduser("~/meritgiving/data/corepcf")
CHK,DLY=2000,0.15

def log(m):
    t=datetime.now().isoformat()
    L=f"[{t}] {m}"
    print(L)
    open(LP,"a",encoding="utf-8").write(L+"\n")

def db():
    c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c

def s0():
    log("=== GAP AUDIT ===")
    c=db().cursor()
    for k,q in [("total","SELECT COUNT(*) FROM registry_enriched"),
                ("no_ntee","SELECT COUNT(*) FROM registry_enriched WHERE ntee_code IS NULL OR ntee_code=''"),
                ("no_rev","SELECT COUNT(*) FROM registry_enriched WHERE total_revenue IS NULL OR total_revenue=0"),
                ("no_name","SELECT COUNT(*) FROM registry_enriched WHERE name IS NULL OR name=''"),
                ("no_geo","SELECT COUNT(*) FROM registry_enriched WHERE city IS NULL OR city=''"),
                ("no_web","SELECT COUNT(*) FROM registry_enriched WHERE website IS NULL OR website=''"),
                ("no_990","SELECT COUNT(*) FROM registry_enriched WHERE filing_object_id IS NULL")]:
        c.execute(q);log(f"  {k}: {c.fetchone()[0]:,}")

def pp(ein):
    try:
        r=requests.get(f"{PP}/organizations/{ein}.json",timeout=30)
        if r.status_code==404:return None
        r.raise_for_status();d=r.json()
        o=d.get("organization",{})
        f=(d.get("filings_with_data",[])+d.get("filings_without_data",[]))
        l=f[0] if f else {}
        return {"name":o.get("name"),"city":o.get("city"),"state":o.get("state"),
                "ntee":o.get("ntee_code"),"ntee_desc":o.get("ntee_description"),
                "sub":o.get("subseccd"),"pdfs":o.get("have_pdfs"),"web":o.get("website"),
                "mission":o.get("mission"),"oid":l.get("object_id"),"yr":l.get("tax_prd_yr"),
                "rev":l.get("totrevenue"),"ast":l.get("totassetsend")}
    except Exception as e:return {"_err":str(e)}

def s1(limit=25000):
    log("STAGE1: ProPublica")
    c=db().cursor()
    c.execute("SELECT ein FROM registry_enriched WHERE ntee_code IS NULL OR name IS NULL OR filing_object_id IS NULL ORDER BY ein LIMIT ?",(limit,))
    eins=[r[0] for r in c.fetchall()]
    if not eins:log("  skip");return
    log(f"  {len(eins):,} EINs")
    u=0;err=0;conn=db()
    for ein in eins:
        d=pp(ein);time.sleep(DLY)
        if d is None:continue
        if "_err" in d:err+=1;continue
        try:
            conn.execute("""UPDATE registry_enriched SET
                name=COALESCE(name,?),city=COALESCE(city,?),state=COALESCE(state,?),
                ntee_code=COALESCE(ntee_code,?),ntee_description=COALESCE(ntee_description,?),
                subseccd=COALESCE(subseccd,?),have_pdfs=COALESCE(have_pdfs,?),
                website=COALESCE(website,?),mission=COALESCE(mission,?),
                filing_object_id=COALESCE(filing_object_id,?),latest_tax_year=COALESCE(latest_tax_year,?),
                total_revenue=COALESCE(total_revenue,?),total_assets=COALESCE(total_assets,?),
                data_source=COALESCE(data_source,'')||';pp',updated_at=?
                WHERE ein=?""",(d["name"],d["city"],d["state"],d["ntee"],d["ntee_desc"],
                d["sub"],d["pdfs"],d["web"],d["mission"],d["oid"],d["yr"],d["rev"],d["ast"],
                datetime.now().isoformat(),ein))
            u+=1
        except:err+=1
        if u%CHK==0:conn.commit();log(f"    {u:,}")
    conn.commit();conn.close()
    log(f"  done {u:,} ok, {err:,} err")

def s2():
    log("STAGE2: BMF NTEE")
    if not os.path.exists(BMF):log("  no bmf");return
    import csv
    c=db().cursor()
    c.execute("SELECT ein FROM registry_enriched WHERE ntee_code IS NULL OR ntee_code=''")
    need={r[0] for r in c.fetchall()}
    log(f"  need {len(need):,}")
    u=0;conn=db()
    with open(BMF,"r",encoding="latin-1") as f:
        for row in csv.DictReader(f):
            e=row.get("EIN","").strip().zfill(9)
            if e in need:
                n=row.get("NTEE_CD","") or row.get("NTEE_CODE","")
                if n:
                    conn.execute("UPDATE registry_enriched SET ntee_code=?,data_source=data_source||';bmf' WHERE ein=?",(n.strip(),e))
                    u+=1
                    if u%5000==0:conn.commit();log(f"    {u:,}")
    conn.commit();conn.close()
    log(f"  done {u:,}")

def s3():
    log("STAGE3: NCCS revenue")
    import glob,pandas as pd
    files=glob.glob(os.path.join(NCCS,"core_*.csv"))
    if not files:log("  no nccs");return
    c=db().cursor()
    c.execute("SELECT ein FROM registry_enriched WHERE total_revenue IS NULL OR total_revenue=0")
    need={r[0] for r in c.fetchall()}
    log(f"  need {len(need):,}")
    u=0
    for fp in sorted(files):
        log(f"  {os.path.basename(fp)}")
        try:
            df=pd.read_csv(fp,usecols=["EIN","TOTREV"],dtype={"EIN":str},low_memory=False)
            df["EIN"]=df["EIN"].str.strip().str.zfill(9)
            df=df[df["EIN"].isin(need)]
            conn=db()
            for _,r in df.iterrows():
                v=r["TOTREV"]
                if pd.notna(v) and v>0:
                    conn.execute("UPDATE registry_enriched SET total_revenue=?,data_source=data_source||';nccs' WHERE ein=?",(float(v),r["EIN"]))
                    u+=1
            conn.commit();conn.close()
            log(f"    +{u:,}")
        except Exception as e:log(f"    err {e}")
    log(f"  done {u:,}")

def s4():
    log("STAGE4: 990 object IDs")
    c=db().cursor()
    c.execute("SELECT ein FROM registry_enriched WHERE filing_object_id IS NULL AND (have_pdfs=1 OR have_pdfs IS NULL) LIMIT 10000")
    eins=[r[0] for r in c.fetchall()]
    if not eins:log("  skip");return
    log(f"  {len(eins):,} EINs")
    u=0;conn=db()
    for ein in eins:
        try:
            r=requests.get(f"{PP}/organizations/{ein}.json",timeout=20)
            if r.status_code!=200:continue
            d=r.json()
            f=d.get("filings_with_data",[])
            if f:
                oid=f[0].get("object_id")
                if oid:
                    conn.execute("UPDATE registry_enriched SET filing_object_id=?,latest_tax_year=? WHERE ein=?",(oid,f[0].get("tax_prd_yr"),ein))
                    u+=1
            time.sleep(DLY)
            if u%500==0:conn.commit();log(f"    {u:,}")
        except:pass
    conn.commit();conn.close()
    log(f"  done {u:,}")

def s5():
    log("STAGE5: scoring")
    conn=db()
    conn.execute("""UPDATE registry_enriched SET coverage_score=(
        (name IS NOT NULL AND name!='')*15+(ntee_code IS NOT NULL AND ntee_code!='')*20+
        (total_revenue IS NOT NULL AND total_revenue>0)*20+(city IS NOT NULL AND city!='')*10+
        (state IS NOT NULL AND state!='')*10+(filing_object_id IS NOT NULL)*15+
        (website IS NOT NULL AND website!='')*10)""")
    conn.commit()
    c=conn.cursor()
    c.execute("SELECT COUNT(*)t,AVG(coverage_score)a,SUM(coverage_score>=80)h,SUM(coverage_score<<40)p FROM registry_enriched")
    r=c.fetchone()
    log(f"  total {r['t']:,} avg {r['a']:.1f} high {r['h']:,} poor {r['p']:,}")
    conn.close()
    log("=== DONE ===")

if __name__=="__main__":
    log("START")
    try:
        s0();s1();s2();s3();s4();s5()
        log("COMPLETE")
    except Exception as e:
        log(f"FATAL {e}")
        import traceback
        log(traceback.format_exc())
        sys.exit(1)
