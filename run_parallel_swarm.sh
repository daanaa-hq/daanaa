#!/bin/bash
cd ~/meritgiving
mkdir -p logs data/csv data/categories data/propublica_cache

LOG="logs/parallel_swarm.log"
echo "========================================" > $LOG
echo "  PARALLEL SWARM $(date)" >> $LOG
echo "========================================" >> $LOG

echo "[MASTER] Phase 1: Parallel XML Parsing (all CPU cores)"
nohup python3 scripts/agent1b_parallel_parser.py > logs/agent1b.log 2>&1 &
PID1=$!
echo "[MASTER] Agent 1b started (PID $PID1)"

if [ ! -f "data/irs_bmf.csv" ]; then
    echo "[MASTER] Phase 1b: Downloading BMF (background)"
    nohup wget -q --show-progress https://www.irs.gov/pub/irs-soi/eo1.csv -O data/irs_bmf.csv > logs/bmf.log 2>&1 &
    PID_BMF=$!
fi

echo "[MASTER] Waiting for Agent 1b..."
wait $PID1
echo "[MASTER] Agent 1b complete."

echo "[MASTER] Phase 2: Score Calculator"
python3 scripts/agent2_scorer.py | tee -a $LOG
if [ $? -ne 0 ]; then echo "Agent 2 failed"; exit 1; fi

echo "[MASTER] Phase 3: Enrichment + ProPublica (parallel)"
nohup python3 scripts/agent3_enricher.py > logs/agent3.log 2>&1 &
PID3=$!
nohup python3 scripts/agent12_parallel_propublica.py > logs/agent12.log 2>&1 &
PID12=$!

echo "[MASTER] Agent 3 (PID $PID3) + Agent 12 (PID $PID12) running..."
wait $PID3
wait $PID12
echo "[MASTER] Phase 3 complete."

echo "[MASTER] Phase 4: Index + Validation"
python3 scripts/agent8_search_index.py | tee -a $LOG
python3 scripts/agent4_validator.py | tee -a $LOG

echo ""
echo "========================================"
echo "  PARALLEL SWARM COMPLETE"
echo "  Check: VALIDATION_REPORT.txt"
echo "========================================"
