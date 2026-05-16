#!/bin/bash
set -e
cd ~/meritgiving

echo "=========================================="
echo "  MERITGIVING PHASE 2: PROPUBLICA + DATA  "
echo "=========================================="

# 1. Ensure cache dir exists
mkdir -p data/propublica_cache

# 2. Test ProPublica API
echo "[1] Testing ProPublica API..."
curl -s "https://projects.propublica.org/nonprofits/api/v2/organizations/10143485.json" > /tmp/pp_test_10143485.json && echo "    10143485: OK" || echo "    10143485: FAIL"
curl -s "https://projects.propublica.org/nonprofits/api/v2/organizations/142007220.json" > /tmp/pp_test_142007220.json && echo "    142007220: OK" || echo "    142007220: FAIL"

python3 -c "
import json
for ein in ['10143485', '142007220']:
    try:
        with open(f'/tmp/pp_test_{ein}.json') as f:
            data = json.load(f)
        print(f'    {ein}: {data.get(\"organization\", {}).get(\"name\", \"NO NAME\")}')
    except Exception as e:
        print(f'    {ein}: INVALID - {e}')
"

# 3. Check current multi-year count
echo "[2] Checking current multi-year coverage..."
python3 -c "
import csv, glob, os
from collections import defaultdict
org_years = defaultdict(set)
for f in glob.glob('data/csv/*.csv'):
    year = os.path.basename(f).replace('.csv', '')
    with open(f) as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            ein = row.get('EIN', '').strip().zfill(9)
            if ein:
                org_years[ein].add(year)
multi = len([k for k, v in org_years.items() if len(v) >= 2])
print(f'    Total orgs: {len(org_years)}')
print(f'    Multi-year orgs: {multi}')
"

# 4. Run ProPublica backfill
echo "[3] Running ProPublica backfill (this will take 30-60 mins)..."
python3 expand_multiyear.py > logs/phase2_backfill.log 2>&1 &
BACKFILL_PID=$!
echo "    Backfill started (PID: $BACKFILL_PID)"
echo "    tail -f ~/meritgiving/logs/phase2_backfill.log"

# 5. Restart server
echo "[4] Restarting server..."
pkill -f "uvicorn app:app" || true
sleep 2
nohup python3 -m uvicorn app:app --host 0.0.0.0 --port 8081 --workers 1 > app.log 2>&1 &
echo "    Server restarted on port 8081"

echo ""
echo "=========================================="
echo "  PHASE 2 RUNNING IN BACKGROUND           "
echo "=========================================="
echo "Check status:"
echo "  tail -f ~/meritgiving/logs/phase2_backfill.log"
echo "  tail -f ~/meritgiving/app.log"
echo "  curl -s http://127.0.0.1:8081/api/health"
echo "  ls ~/meritgiving/data/propublica_cache/ | wc -l"
