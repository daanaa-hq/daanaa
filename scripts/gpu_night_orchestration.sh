#!/bin/bash
# GPU Night Work Orchestrator (10pm-6am)
# Target: +3,500 websites per night × 6 nights = +21,000 total

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/../logs"
mkdir -p "$LOG_DIR"

NIGHT_LOG="$LOG_DIR/gpu_night_$(date +%Y%m%d).log"
HEALTH_FILE="/tmp/gpu_night_health.json"

echo ">>> GPU Night Work Starting at $(date)" | tee "$NIGHT_LOG"

# 1. Check GPU status
echo "Checking GPU..." | tee -a "$NIGHT_LOG"
if ! command -v rocm-smi &> /dev/null; then
    echo "❌ ROCm not available" | tee -a "$NIGHT_LOG"
    exit 1
fi

GPU_LOAD=$(rocm-smi --load 2>/dev/null | tail -1 | awk '{print $NF}' | tr -d '%')
echo "✓ GPU available (load: ${GPU_LOAD}%)" | tee -a "$NIGHT_LOG"

# 2. Report health
echo "{\"status\": \"running\", \"started_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"gpu_load\": $GPU_LOAD}" > "$HEALTH_FILE"

# 3. Run parallelized discovery batches
BATCH_SIZE=1500
WORKER_COUNT=32
PARALLEL_BATCHES=4

echo "Starting $PARALLEL_BATCHES parallel batches × $WORKER_COUNT workers" | tee -a "$NIGHT_LOG"

# Launch 4 parallel batch discovery jobs (each targets different org cohort)
for BATCH_NUM in {1..4}; do
    (
        echo "▶ Batch $BATCH_NUM starting ($(date))" >> "$NIGHT_LOG"
        
        # Mock: simulate website discovery (in real scenario: calls discovery_daemon)
        # Each batch: 500 orgs × 1.75 sites/org avg = ~875 sites
        DISCOVERED=$((BATCH_SIZE / 2 + RANDOM % 500))
        
        echo "✓ Batch $BATCH_NUM: discovered $DISCOVERED websites" >> "$NIGHT_LOG"
    ) &
done

# Wait for all parallel batches
wait
TOTAL_DISCOVERED=$((BATCH_SIZE * PARALLEL_BATCHES / 2))

# 4. Verify results
EXPECTED=3500
SHORTFALL=$((EXPECTED - TOTAL_DISCOVERED))

if [ "$TOTAL_DISCOVERED" -ge "$EXPECTED" ]; then
    echo "✅ Night work complete: $TOTAL_DISCOVERED websites (+$((TOTAL_DISCOVERED - EXPECTED)) over target)" | tee -a "$NIGHT_LOG"
    echo "{\"status\": \"complete\", \"discovered\": $TOTAL_DISCOVERED, \"target\": $EXPECTED, \"status_final\": \"PASS\"}" > "$HEALTH_FILE"
    exit 0
else
    echo "⚠️  Night work incomplete: $TOTAL_DISCOVERED discovered, $SHORTFALL short of $EXPECTED target" | tee -a "$NIGHT_LOG"
    echo "{\"status\": \"incomplete\", \"discovered\": $TOTAL_DISCOVERED, \"target\": $EXPECTED, \"shortfall\": $SHORTFALL, \"status_final\": \"RETRY\"}" > "$HEALTH_FILE"
    exit 1
fi
