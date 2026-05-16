import os, sys, subprocess, json, pandas as pd
from pathlib import Path
REPORT = 'HEALTH_CHECK_REPORT.txt'
lines = []; lines.append('='*70); lines.append('  MERITGIVING COMPREHENSIVE HEALTH CHECK'); lines.append(f'  {pd.Timestamp.now()}'); lines.append('='*70)
failures = 0; passes = 0
def check(name, condition, detail=''):
    global failures, passes
    status = 'PASS' if condition else 'FAIL'
    if condition: passes += 1
    else: failures += 1
    lines.append(f'\n[{name}] {status}')
    if detail: lines.append(f'  {detail}')
    return condition
df = None
if os.path.exists('data/csv/final_profiles.csv'):
    df = pd.read_csv('data/csv/final_profiles.csv', dtype=str)
    check('D1. final_profiles.csv', True, f'{len(df)} rows')
    cols = ['EIN','NAME','MERIT_score','financial_health','operational_efficiency','sustainability_score','scale_trajectory','compliance_score','badges','foundation_type','deductibility']
    missing = [c for c in cols if c not in df.columns]
    check('D2. Required columns', len(missing)==0, f'Missing: {missing}')
    if 'MERIT_score' in df.columns:
        scores = pd.to_numeric(df['MERIT_score'], errors='coerce')
        check('D3. Score distribution', scores.nunique()>100 and scores.std()>5, f'Range: {scores.min():.1f}-{scores.max():.1f}, Mean: {scores.mean():.1f}')
        check('D4. No 100.0 bug', (scores==100.0).sum() < len(df)*0.1, f'At 100.0: {(scores==100.0).sum()}/{len(df)}')
    if 'operational_efficiency' in df.columns:
        oe = pd.to_numeric(df['operational_efficiency'], errors='coerce')
        check('D5. OE coverage', oe.notna().sum()>len(df)*0.5, f'Scored: {oe.notna().sum()}/{len(df)}')
    if 'badges' in df.columns:
        bt = df['badges'].str.split('|').explode().nunique()
        check('D6. Badge diversity', bt>=3, f'Types: {bt}')
else:
    check('D1. final_profiles.csv', False, 'Not found'); failures += 5
check('D7. scored_orgs.csv', os.path.exists('data/csv/scored_orgs.csv'))
check('D8. extracted_financials.csv', os.path.exists('data/csv/extracted_financials.csv'))
check('D9. master_orgs.csv', os.path.exists('data/csv/master_orgs.csv'))
cat_dir = Path('data/categories')
if cat_dir.exists():
    cf = list(cat_dir.glob('*.json'))
    check('C1. Category files', len(cf)>0, f'{len(cf)} files')
    valid = 0
    for f in cf[:5]:
        try:
            with open(f) as fh: data=json.load(fh)
            if 'orgs' in data and len(data['orgs'])>0: valid += 1
        except: pass
    check('C2. Valid categories', valid>0, f'Valid: {valid}/5')
else:
    check('C1. Category files', False, 'No dir'); check('C2. Valid categories', False, 'N/A')
pp_dir = Path('data/propublica_cache')
if pp_dir.exists():
    pf = list(pp_dir.glob('*.json'))
    check('P1. ProPublica cache', True, f'{len(pf)} files')
    missions = 0
    for f in pf[:100]:
        try:
            with open(f) as fh: data=json.load(fh)
            if data.get('mission') and len(data['mission'])>10: missions += 1
        except: pass
    check('P2. Missions present', missions>0, f'With missions: {missions}/100')
else:
    check('P1. ProPublica cache', False, 'No dir'); check('P2. Missions present', False, 'N/A')
bmf = Path('data/irs_bmf.csv')
check('B1. BMF downloaded', bmf.exists(), f'{bmf.stat().st_size/(1024**2):.1f} MB' if bmf.exists() else 'Not found')
try:
    r = subprocess.run(['curl','-s','-o','/dev/null','-w','%{http_code}','http://127.0.0.1:8081/search?q=education'], capture_output=True, text=True, timeout=10)
    check('A1. Search endpoint', r.stdout.strip()=='200', f'Status: {r.stdout.strip()}')
    if r.stdout.strip()=='200':
        r2 = subprocess.run(['curl','-s','http://127.0.0.1:8081/search?q=education'], capture_output=True, text=True, timeout=10)
        try:
            data = json.loads(r2.stdout)
            check('A2. Search results', len(data.get('results',[]))>0, f'Results: {len(data.get("results",[]))}')
        except: check('A2. Search results', False, 'Invalid JSON')
except Exception as e: check('A1. Search endpoint', False, str(e)); check('A2. Search results', False, 'N/A')
try:
    sample = df[df['MERIT_score'].notna()].iloc[0]['EIN'] if df is not None and len(df)>0 else '010211502'
    r = subprocess.run(['curl','-s',f'http://127.0.0.1:8081/org/{sample}'], capture_output=True, text=True, timeout=10)
    try:
        data = json.loads(r.stdout)
        check('A3. Org detail', bool(data.get('name')) and 'MERIT_score' in data, f'EIN: {sample}')
    except: check('A3. Org detail', False, 'Invalid JSON')
except Exception as e: check('A3. Org detail', False, str(e))
try:
    r = subprocess.run(['curl','-s','http://127.0.0.1:8081/categories'], capture_output=True, text=True, timeout=10)
    try: data=json.loads(r.stdout); check('A4. Categories', len(data.get('categories',[]))>0, f'Cats: {len(data.get("categories",[]))}')
    except: check('A4. Categories', False, 'Invalid JSON')
except Exception as e: check('A4. Categories', False, str(e))
try:
    r = subprocess.run(['curl','-s','http://127.0.0.1:8081/stats'], capture_output=True, text=True, timeout=10)
    try: data=json.loads(r.stdout); check('A5. Stats', data.get('total_orgs',0)>0, f'Total: {data.get("total_orgs",0)}')
    except: check('A5. Stats', False, 'Invalid JSON')
except Exception as e: check('A5. Stats', False, str(e))
try:
    stat = os.statvfs('.'); free = stat.f_bavail * stat.f_frsize / (1024**3)
    check('S1. Disk space', free>50, f'Free: {free:.1f} GB')
except: check('S1. Disk space', False, 'Cannot check')
try:
    import multiprocessing; cores = multiprocessing.cpu_count()
    check('S2. CPU cores', cores>=4, f'Cores: {cores}')
except: check('S2. CPU cores', False, 'Cannot check')
lines.append('\n' + '='*70); lines.append('  SUMMARY'); lines.append('='*70)
lines.append(f'\n  RESULTS: {passes} passed, {failures} failed'); lines.append(f'  SCORE: {passes}/{passes+failures}')
if failures==0: lines.append('\n  ALL SYSTEMS GREEN'); lines.append('  Ready for parallel execution'); exit_code=0
elif failures<=2: lines.append('\n  MOSTLY GREEN'); lines.append('  Safe to proceed with parallel execution'); exit_code=0
else: lines.append('\n  MULTIPLE FAILURES'); lines.append('  Do NOT proceed with parallel execution'); exit_code=1
lines.append('='*70)
report = '\n'.join(lines)
with open(REPORT, 'w') as f: f.write(report)
print(report); sys.exit(exit_code)
