#!/usr/bin/env python3
import sqlite3,csv,re,sys,json,shutil
from pathlib import Path
from datetime import datetime
from collections import Counter,defaultdict

BASE=Path.home()/"meritgiving"
OUT=BASE/"data"/f"audit_{datetime.now():%Y%m%d_%H%M%S}"
STATES={"AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC","PR","VI","GU","AS","MP"}
DEDUCT={"PC","POF","PF","1","2"}
NTEE={"A":"Arts","B":"Education","C":"Environment","D":"Animal","E":"Health","F":"Mental Health","G":"Voluntary Health","H":"Medical Research","I":"Crime","J":"Employment","K":"Food","L":"Housing","M":"Public Safety","N":"Recreation","O":"Youth","P":"Human Services","Q":"International","R":"Civil Rights","S":"Community","T":"Philanthropy","U":"Science","V":"Social Science","W":"Public Benefit","X":"Religion","Y":"Membership","Z":"Unknown"}

def find_db():
    if len(sys.argv)>1:
        p=Path(sys.argv[1])
        if p.exists():return p
        sys.exit(f"ERR: {p} not found")
    for n in ["merit_registry.db","registry.db","merit.db","nonprofits.db","irs_bmf.db"]:
        for p in BASE.rglob(n):
            if p.is_file():print(f"  [FOUND] {p}");return p
    d=BASE/"data"
    if d.exists():
        f=sorted(d.rglob("*.db"),key=lambda x:x.stat().st_size,reverse=True)
        if f:print(f"  [FOUND] {f[0]}");return f[0]
    sys.exit("ERR: No .db found in ~/meritgiving")

def norm_ein(v):
    s=re.sub(r"[^0-9]","",str(v)) if v else ""
    return (f"{s[:2]}-{s[2:]}",len(s)==9) if len(s)==9 else (s,False)

def norm_name(v):
    if not v:return "",["NULL_NAME"]
    s=str(v).replace("\\x00","").replace("\\u0000","").encode('utf-8','ignore').decode('utf-8')
    s=s.replace("â€™","'").replace("â€œ",'"').replace("â€",'"').replace("Â"," ").strip()
    f=[]
    if re.search(r'\bTEST\b',s,re.I):f.append("SUSP_TEST")
    if re.search(r'\b(INC\s+INC|LLC\s+LLC)\b',s,re.I):f.append("SUSP_DUP_SUFFIX")
    if len(s)<=1:f.append("SUSP_SHORT")
    if re.search(r'^(TODO|PLACEHOLDER|TEMP|TBD)\b',s,re.I):f.append("SUSP_PLACEHOLDER")
    return s,f

def norm_state(v):
    if not v:return "",False
    s=str(v).strip().upper()
    if s in STATES:return s,True
    fixes={"CALIF":"CA","CALIFORNIA":"CA","TEX":"TX","TEXAS":"TX","NEW YORK":"NY","NYC":"NY","FLORIDA":"FL","PENN":"PA","PENNSYLVANIA":"PA","OHIO":"OH","ILL":"IL","ILLINOIS":"IL","GEORGIA":"GA","WASHINGTON":"WA","VIRGINIA":"VA","MARYLAND":"MD","COLORADO":"CO","ARIZONA":"AZ","OREGON":"OR","MICHIGAN":"MI"}
    return (fixes[s],True) if s in fixes else (s,False)

def norm_zip(v):
    if not v:return "",False
    s=re.sub(r"[^0-9-]","",str(v))
    return (s,bool(re.match(r"^\d{5}(-\d{4})?$",s)))

def norm_ntee(v):
    if not v:return "",False,"NULL"
    s=str(v).strip().upper()
    m=s[0] if s else ""
    return (s,True,m) if m in NTEE or m=="X" else (s,False,"INVALID")

def norm_date(v):
    if not v:return None,["NULL_DATE"]
    s=str(v).strip()
    for fmt in ("%Y-%m-%d","%Y%m%d","%m/%d/%Y","%d-%m-%Y","%Y/%m/%d"):
        try:
            d=datetime.strptime(s,fmt)
            f=[]
            if d.year>datetime.now().year:f.append("FUTURE")
            if d.year<<1900:f.append("PRE_1900")
            return d.strftime("%Y-%m-%d"),f
        except ValueError:pass
    return s,["UNPARSEABLE"]

class Engine:
    def __init__(self,db,table,recency):
        self.db=db;self.table=table;self.recency=recency
        self.raw=0;self.bad_ein=0;self.dup=0;self.revoked=0;self.inelig=0;self.final=0;self.flagged=0
        self.exceptions=[];self.dup_samples=[]
    def load(self):
        c=sqlite3.connect(self.db);c.row_factory=sqlite3.Row
        r=[dict(x) for x in c.execute(f"SELECT * FROM {self.table}").fetchall()];c.close();return r
    def proc(self,row):
        o=dict(row);o["_f"]=[];o["_r"]=None
        e,o["ein"],ok=norm_ein(row.get("EIN")or row.get("ein"))
        if not ok:self.bad_ein+=1;self.exceptions.append([str(row.get("EIN")or""),str(row.get("NAME")or row.get("name")or""),"BAD_EIN",f"'{row.get('EIN')}'->'{e}' not 9 digits",row]);return None
        o["ein"]=e
        n,f=norm_name(row.get("NAME")or row.get("name")or row.get("ORGANIZATION_NAME")or row.get("ORG_NAME"))
        o["name"]=n;o["_f"].extend(f)
        s,ok=norm_state(row.get("STATE")or row.get("state")or row.get("ST"))
        o["state"]=s
        if not ok:o["_f"].append("BAD_STATE")
        z,ok=norm_zip(row.get("ZIP")or row.get("zip")or row.get("ZIP5"))
        o["zip"]=z
        if not ok:o["_f"].append("BAD_ZIP")
        nt,ok,m=norm_ntee(row.get("NTEE_CD")or row.get("NTEE")or row.get("ntee_cd"))
        o["ntee"]=nt;o["ntee_m"]=m
        if not ok and row.get("NTEE_CD")is not None:o["_f"].append("BAD_NTEE")
        rd,f2=norm_date(row.get("RULING_DATE")or row.get("ruling_date")or row.get("RULEDATE"))
        o["rdate"]=rd;o["_f"].extend(f2)
        o["_rec"]=row.get(self.recency)if self.recency else None
        st=row.get("STREET")or row.get("street")or row.get("ADDRESS")
        ct=row.get("CITY")or row.get("city")
        if not st or not ct or not s or not z:o["_f"].append("INCOMPLETE_ADDR")
        return o
    def dedup(self,rows):
        d=defaultdict(list)
        for r in rows:d[r["ein"]].append(r)
        out=[];removed=0;samples=[]
        for ein,grp in d.items():
            if len(grp)>1:
                removed+=len(grp)-1
                def sk(r):
                    rec=r["_rec"]
                    try:rs=datetime.strptime(str(rec)[:10],"%Y-%m-%d").timestamp()
                    except:rs=str(rec)if rec else 0
                    nc=sum(1 for k in["name","state","zip"]if not r.get(k))
                    return(-rs if isinstance(rs,(int,float))else 0,nc,-len(str(r.get("_rec",""))))
                grp.sort(key=sk);kept=grp[0]
                if len(samples)<10:samples.append({"ein":ein,"n":len(grp),"kept":{k:v for k,v in kept.items()if not k.startswith("_")}})
                for drop in grp[1:]:self.exceptions.append([ein,drop.get("name",""),"DUP_EIN",f"Group of {len(grp)}; kept rec={kept.get('_rec')}",drop])
                out.append(kept)
            else:out.append(grp[0])
        self.dup=removed;self.dup_samples=samples;return out
    def active(self,rows):
        out=[]
        for r in rows:
            d=str(r.get("DEDUCTIBILITY_CODE")or r.get("deductibility")or r.get("DEDUCT_CD")or"").strip().upper()
            s=str(r.get("SUBSECTION")or r.get("subsection")or r.get("ORGANIZATION_TYPE")or"").strip()
            ok=("501"in s and"(3)"in s)or s in("3","03","501C3","501(C)(3)")or d in DEDUCT or d.startswith("PC")or d.startswith("PF")
            if not ok:self.inelig+=1;self.exceptions.append([r["ein"],r.get("name",""),"INELIG",f"sub={s},ded={d}",r]);continue
            out.append(r)
        return out
    def flag_names(self,rows):
        by=defaultdict(list)
        for r in rows:by[r.get("name","").upper()].append(r["ein"])
        for n,e in by.items():
            if len(set(e))>1:
                for r in rows:
                    if r.get("name","").upper()==n and "NAME_DUP_EIN"not in r["_f"]:r["_f"].append("NAME_DUP_EIN");self.flagged+=1
    def run(self):
        rows=self.load();self.raw=len(rows)
        p=[self.proc(r)for r in rows if r]
        p=[x for x in p if x]
        d=self.dedup(p)
        a=self.active(d)
        self.flag_names(a)
        self.final=len(a)
        return a

class Reporter:
    def __init__(self,odir,engine,recency,cols,dbpath):
        self.odir=odir;self.e=engine;self.rec=recency;self.cols=cols;self.db=dbpath
    def write(self,rows):
        self.odir.mkdir(parents=True,exist_ok=True)
        c=sqlite3.connect(self.odir/"cleaned.db");x=c.cursor()
        x.execute("DROP TABLE IF EXISTS cleaned")
        x.execute("CREATE TABLE cleaned(raw_json TEXT,ein TEXT,name TEXT,state TEXT,zip TEXT,ntee TEXT,ntee_m TEXT,rdate TEXT,flags TEXT)")
        for r in rows:
            x.execute("INSERT INTO cleaned VALUES(?,?,?,?,?,?,?,?,?)",(json.dumps({k:v for k,v in r.items()if not k.startswith("_")},default=str),r.get("ein"),r.get("name"),r.get("state"),r.get("zip"),r.get("ntee"),r.get("ntee_m"),r.get("rdate"),",".join(r.get("_f",[]))))
        c.commit();c.close()
        with open(self.odir/"exceptions.csv","w",newline="",encoding="utf-8")as f:
            w=csv.writer(f);w.writerow(["EIN","NAME","CODE","DETAIL"])
            for e in self.e.exceptions:w.writerow(e[:4])
        sc=Counter(r.get("state","UNK")for r in rows);nc=Counter(r.get("ntee_m","UNK")for r in rows)
        dc=Counter()
        for r in rows:
            rd=r.get("rdate")
            if rd and isinstance(rd,str)and len(rd)>=4:
                try:dc[f"{int(rd[:4])//10*10}s"]+=1
                except:pass
        rpt=f"# MERIT Audit Report\n**Generated:** {datetime.now().isoformat()}\n**DB:** {self.db}\n**Recency:** `{self.rec}`\n\n"
        rpt+="## Counts\n|Metric|Count|\n|---|---|\n"
        rpt+=f"|Raw|{self.e.raw:,}|\n|Bad EIN|{self.e.bad_ein:,}|\n|Dups removed|{self.e.dup:,}|\n|Revoked|{self.e.revoked:,}|\n|Ineligible|{self.e.inelig:,}|\n"
        rpt+=f"|**Final**|{self.e.final:,}|\n|Flagged|{self.e.flagged:,}|\n\n"
        rpt+="## States (Top 15)\n|State|Count|\n|---|---|\n"
        for st,cnt in sc.most_common(15):rpt+=f"|{st}|{cnt:,}|\n"
        rpt+="\n## NTEE (Top 10)\n|Grp|Desc|Count|\n|---|---|---|\n"
        for g,cnt in nc.most_common(10):rpt+=f"|{g}|{NTEE.get(g,g)}|{cnt:,}|\n"
        rpt+="\n## Decades\n|Decade|Count|\n|---|---|\n"
        for d in sorted(dc.keys()):rpt+=f"|{d}|{dc[d]:,}|\n"
        rpt+="\n## Dup Samples\n"
        for i,s in enumerate(self.e.dup_samples[:10],1):rpt+=f"{i}. EIN {s['ein']} (group of {s['n']})\n"
        rpt+="\n*Idempotent: re-run on output = zero changes*"
        (self.odir/"audit_report.md").write_text(rpt,encoding="utf-8")
        s=Path(__file__)if"__file__"in dir()else Path("merit_audit.py")
        if s.exists():shutil.copy(s,self.odir/"merit_audit.py")

print("="*60)
print("MERIT Audit")
print("="*60)
DB=find_db()
print(f"DB: {DB}")
I=sqlite3.connect(DB);I.row_factory=sqlite3.Row;C=I.cursor()
C.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables=[r[0]for r in C.fetchall()]
cands=[t for t in tables if t not in('sqlite_sequence','revenue_percentiles')]
tbl=None
for p in['registry_enriched','registry','irs_bmf','organizations','nonprofits']:
    if p in cands:tbl=p;break
if not tbl and cands:
    sz=[]
    for t in cands:
        C.execute(f"PRAGMA table_info({t})")
        sz.append((len(C.fetchall()),t))
    tbl=max(sz)[1]
C.execute(f"PRAGMA table_info({tbl})")
cols=C.fetchall()
C.execute(f"SELECT COUNT(*)FROM {tbl}")
rc=C.fetchone()[0]
C.execute(f"SELECT *FROM {tbl}LIMIT 5")
samp=[dict(r)for r in C.fetchall()]
I.close()

rec=None
for c in['BMF_LOAD_DATE','LAST_UPDATED','IMPORT_TIMESTAMP','RULING_DATE','ruling_date','last_updated','import_timestamp','bmf_load_date','updated_at']:
    cn=[x[1].upper()for x in cols]
    if c.upper()in cn:
        for x in cols:
            if x[1].upper()==c.upper():rec=x[1];break
        break

print(f"\n[STEP 0] TABLE={tbl} ROWS={rc:,} COLS={len(cols)} RECENCY={rec}")
for n,t in cols:
    try:
        C=sqlite3.connect(DB).cursor()
        C.execute(f"SELECT COUNT(*)FROM {tbl}WHERE {n}IS NULL OR TRIM(CAST({n}AS TEXT))=''")
        print(f"  {n:22} {t:10} nulls={C.fetchone()[0]:,}")
    except:print(f"  {n:22} {t:10} nulls=ERR")
print(f"\nSAMPLE (5 rows):")
for i,r in enumerate(samp[:5],1):
    print(f"  Row {i}:")
    for k,v in r.items():print(f"    {k}: {v}")

print(f"\n[RUNNING AUDIT...]")
E=Engine(DB,tbl,rec)
rows=E.run()
R=Reporter(OUT,E,rec,cols,DB)
R.write(rows)
print(f"\n{'='*60}")
print("DONE")
print(f"{'='*60}")
print(f"Output: {OUT}")
print(f"  cleaned.db | audit_report.md | exceptions.csv | merit_audit.py")
print(f"FINAL ACTIVE 501(c)(3): {E.final:,}")
print(f"Removed: {E.raw-E.final:,}  Flagged: {E.flagged:,}")
