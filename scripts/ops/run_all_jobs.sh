#!/bin/bash
# MERIT Master Orchestrator
# Launches CPU-bound data cleanup + GPU LLM inference in parallel
# Run from ~/meritgiving/

set -e
cd ~/meritgiving
mkdir -p logs/batch jobs/gpu_output

echo "=========================================="
echo "MERIT Master Orchestrator"
echo "$(date)"
echo "=========================================="

# Check GPU
echo ""
echo "GPU Status:"
rocm-smi --showmeminfo vram 2>/dev/null | head -6 || echo "  rocm-smi unavailable"

echo ""
echo "Starting parallel jobs..."
echo ""

# JOB 1: NTEE Crosswalk (CPU, ~5 min for 45k cache files)
echo "[Job 1] NTEE Crosswalk — fixing 16,275 missing codes"
nohup python3 scripts/ntee_crosswalk.py > logs/batch/ntee_crosswalk.log 2>&1 &
JOB1=$!
echo "  PID $JOB1 -> logs/batch/ntee_crosswalk.log"

# JOB 2: 990 Gap Analysis (CPU, ~2 min)
echo "[Job 2] 990 Gap Analysis — finding 15k orgs needing filings"
nohup python3 scripts/extract_990s.py > logs/batch/990_gap.log 2>&1 &
JOB2=$!
echo "  PID $JOB2 -> logs/batch/990_gap.log"

# JOB 3: Category Cleanup (CPU, ~5 min)
echo "[Job 3] Category File Cleanup — dedupe + format"
nohup python3 scripts/merit_p0_fixes_v2.py > logs/batch/category_cleanup.log 2>&1 &
JOB3=$!
echo "  PID $JOB3 -> logs/batch/category_cleanup.log"

# JOB 4: GPU LLM Inference (GPU, ~2-4 hrs depending on batch size)
echo "[Job 4] GPU Batch Inference — NTEE classification + mission enhancement"
# Check if LLM backend is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1 || curl -s http://localhost:8080/models > /dev/null 2>&1; then
    nohup python3 scripts/gpu_batch_inference.py --task ntee --batch 1000 > logs/batch/gpu_ntee.log 2>&1 &
    JOB4=$!
    echo "  PID $JOB4 -> logs/batch/gpu_ntee.log (GPU ACTIVE)"
else
    echo "  ⚠️  SKIPPED: No LLM backend detected."
    echo "      Start ollama or llama.cpp server first:"
    echo "        ollama serve &"
    echo "        # OR"
    echo "        llama-server -m ~/models/your-model.gguf --port 8080 -ngl 99 &"
    JOB4="NONE"
fi

echo ""
echo "=========================================="
echo "All jobs launched."
echo ""
echo "Monitor:"
echo "  tail -f logs/batch/*.log"
echo "  watch -n 5 'ps aux | grep python3 | grep -v grep'"
echo ""
echo "Check GPU utilization:"
echo "  watch -n 2 rocm-smi"
echo ""
echo "PIDs running:"
echo "  Job 1 (NTEE):     $JOB1"
echo "  Job 2 (990 Gap):  $JOB2"
echo "  Job 3 (Cleanup):  $JOB3"
echo "  Job 4 (GPU LLM):  $JOB4"
echo "=========================================="

# Save PID tracker
cat > logs/batch/pids.txt << EOF
$(date)
NTEE_CROSSWALK: $JOB1
990_GAP: $JOB2
CATEGORY_CLEANUP: $JOB3
GPU_LLM: $JOB4
EOF
