#!/bin/bash
# MeritGiving v2.1 Master Setup — One Drop
# Copies all scripts, creates dirs, prints execution commands

set -e

BASE="$HOME/meritgiving"
mkdir -p "$BASE"/{data/{nccs,corepcf,xml,zip},scripts,logs,config}

echo "=========================================="
echo "MeritGiving v2.1 Master Setup"
echo "=========================================="

# Copy scripts to user's machine
# (In practice, user will download these from the output links)

echo ""
echo "Scripts to place in $BASE/scripts/:"
echo "  1. ingest_bmf_master.py      → Build filtered registry from BMF"
echo "  2. track_bmf_changes.py      → Track org lifecycle across months"
echo "  3. analyze_data_gaps.py      → Report what's missing"
echo "  4. download_corepcf.sh       → Get NCCS financial files"
echo "  5. merge_corepcf.py          → Load financials into SQLite"
echo "  6. compute_scores.py         → Compute MeritGiving scores"
echo ""

cat << 'EOF'
==========================================
EXECUTION PLAN — Run These In Order
==========================================

STEP 1 — Build Registry (uses your existing BMF files)
----------------------------------------------
cd ~/meritgiving
python3 scripts/ingest_bmf_master.py
→ Outputs: data/meritgiving.db (registry table)
→ Time: 2-5 minutes

STEP 2 — Track Changes (uses your monthly snapshots)
----------------------------------------------
python3 scripts/track_bmf_changes.py
→ Outputs: lifecycle tables in same DB
→ Time: 5-10 minutes

STEP 3 — See What's Missing
----------------------------------------------
python3 scripts/analyze_data_gaps.py
→ Outputs: gap_analysis.json
→ Time: <1 minute

STEP 4 — Get Financial Data (NCCS CorePCF)
----------------------------------------------
bash scripts/download_corepcf.sh
→ Downloads: corepcf_2019.csv through corepcf_2022.csv
→ Time: 10-30 minutes (depends on connection)

STEP 5 — Merge Financials
----------------------------------------------
python3 scripts/merge_corepcf.py
→ Outputs: financials_2019 through financials_2022 tables
→ Time: 5-10 minutes

STEP 6 — Compute Scores
----------------------------------------------
python3 scripts/compute_scores.py
→ Outputs: scores table with MeritGiving composite score
→ Time: 2-5 minutes

STEP 7 — Query Your Data
----------------------------------------------
sqlite3 data/meritgiving.db

-- Top 10 orgs by score
SELECT EIN, NAME, STATE, NTEE1, merit_score 
FROM registry r JOIN scores s ON r.EIN = s.EIN 
ORDER BY merit_score DESC LIMIT 10;

-- Orgs by state count
SELECT STATE, COUNT(*) FROM registry GROUP BY STATE ORDER BY COUNT(*) DESC;

-- Revenue distribution
SELECT 
  CASE 
    WHEN REVENUE_AMT < 100000 THEN '<100K'
    WHEN REVENUE_AMT < 500000 THEN '100K-500K'
    WHEN REVENUE_AMT < 1000000 THEN '500K-1M'
    WHEN REVENUE_AMT < 5000000 THEN '1M-5M'
    ELSE '>5M'
  END as band,
  COUNT(*) as count
FROM registry GROUP BY band;

==========================================
MONITORING
==========================================

# Check disk space
df -h ~/meritgiving

# Check DB size
ls -lh ~/meritgiving/data/meritgiving.db

# Check table sizes
sqlite3 ~/meritgiving/data/meritgiving.db "SELECT name, (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=t.name) as rows FROM sqlite_master t WHERE type='table';"

EOF

chmod +x $BASE/scripts/*.py 2>/dev/null || true
chmod +x $BASE/scripts/*.sh 2>/dev/null || true

echo ""
echo "Setup complete. Place the 6 scripts in $BASE/scripts/ and run Step 1."
