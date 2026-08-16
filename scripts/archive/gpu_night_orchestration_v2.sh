#!/bin/bash
# FIXED: GPU Night Work Orchestrator (10pm-6am)
# Now calls real discovery_daemon (not mock data)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/../logs"
mkdir -p "$LOG_DIR"

NIGHT_LOG="$LOG_DIR/gpu_night_$(date +%Y%m%d).log"
HEALTH_FILE="/tmp/gpu_night_health.json"
WATCHDOG_TIMEOUT=28800  # 8 hours

echo ">>> GPU Night Work Starting at $(date)" | tee "$NIGHT_LOG"

# 1. Check GPU availability and load
echo "Checking GPU..." | tee -a "$NIGHT_LOG"
if ! command -v rocm-smi &> /dev/null; then
    echo "❌ ROCm not available" | tee -a "$NIGHT_LOG"
    echo "{\"status\": \"error\", \"reason\": \"rocm-smi not found\"}" > "$HEALTH_FILE"
    exit 1
fi

GPU_LOAD=$(rocm-smi --load 2>/dev/null | grep -oP '\d+(?=%)' | head -1)
if [ -z "$GPU_LOAD" ]; then
    GPU_LOAD=0
fi

echo "✓ GPU available (current load: ${GPU_LOAD}%)" | tee -a "$NIGHT_LOG"

# 2. Check if GPU is too busy (skip if >90% loaded)
if [ "$GPU_LOAD" -gt 90 ]; then
    echo "⚠️  GPU too busy (${GPU_LOAD}% load), skipping night work" | tee -a "$NIGHT_LOG"
    echo "{\"status\": \"skipped\", \"reason\": \"GPU load >90%\", \"gpu_load\": $GPU_LOAD}" > "$HEALTH_FILE"
    exit 0
fi

# 3. Report health at startup
echo "{\"status\": \"running\", \"started_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"gpu_load\": $GPU_LOAD, \"watchdog_timeout\": $WATCHDOG_TIMEOUT}" > "$HEALTH_FILE"

# 4. Run parallelized discovery batches
# FIXED: Now calls real discovery_daemon.py (not mock calculation)
BATCH_COUNT=4
WORKER_COUNT=32
BATCH_SIZE=1500

echo "Starting $BATCH_COUNT parallel batches × $WORKER_COUNT workers" | tee -a "$NIGHT_LOG"
echo "Target: +3,500 websites/night" | tee -a "$NIGHT_LOG"

# Array to track batch PIDs
declare -a BATCH_PIDS

# Launch 4 parallel batch discovery jobs
for BATCH_NUM in {1..4}; do
    (
        echo "▶ Batch $BATCH_NUM starting at $(date)" >> "$NIGHT_LOG"
        
        # FIXED: Call real discovery_daemon (not mock)
        # discovery_daemon.py coordinates org discovery and website validation
        timeout $WATCHDOG_TIMEOUT python3 "$SCRIPT_DIR/discovery_daemon.py" \
            --batch-num $BATCH_NUM \
            --batch-size $BATCH_SIZE \
            --workers $WORKER_COUNT \
            --log "$LOG_DIR/discovery_batch_${BATCH_NUM}.log" \
            2>> "$NIGHT_LOG"
        
        BATCH_RESULT=$?
        if [ $BATCH_RESULT -eq 0 ]; then
            echo "✓ Batch $BATCH_NUM completed successfully" >> "$NIGHT_LOG"
        elif [ $BATCH_RESULT -eq 124 ]; then
            echo "⚠️  Batch $BATCH_NUM timed out (>$((WATCHDOG_TIMEOUT/3600))h)" >> "$NIGHT_LOG"
        else
            echo "❌ Batch $BATCH_NUM failed with code $BATCH_RESULT" >> "$NIGHT_LOG"
        fi
    ) &
    
    BATCH_PIDS[$BATCH_NUM]=$!
    echo "Batch $BATCH_NUM launched (PID: ${BATCH_PIDS[$BATCH_NUM]})" | tee -a "$NIGHT_LOG"
done

# 5. Wait for all batches with timeout watchdog
echo "Waiting for all batches to complete..." | tee -a "$NIGHT_LOG"
FAILED_BATCHES=0

for BATCH_NUM in {1..4}; do
    PID=${BATCH_PIDS[$BATCH_NUM]}
    if wait $PID 2>/dev/null; then
        echo "✓ Batch $BATCH_NUM completed" >> "$NIGHT_LOG"
    else
        FAILED_BATCHES=$((FAILED_BATCHES + 1))
        echo "❌ Batch $BATCH_NUM failed" >> "$NIGHT_LOG"
    fi
done

# 6. Aggregate results from batch logs
TOTAL_DISCOVERED=0
for BATCH_NUM in {1..4}; do
    BATCH_LOG="$LOG_DIR/discovery_batch_${BATCH_NUM}.log"
    if [ -f "$BATCH_LOG" ]; then
        # Extract discovered count from batch log
        BATCH_COUNT=$(grep -o "discovered [0-9]*" "$BATCH_LOG" | tail -1 | awk '{print $2}')
        if [ -n "$BATCH_COUNT" ]; then
            TOTAL_DISCOVERED=$((TOTAL_DISCOVERED + BATCH_COUNT))
        fi
    fi
done

# 7. Verify results
EXPECTED=3500
STATUS="PASS"

if [ "$FAILED_BATCHES" -gt 0 ]; then
    echo "⚠️  $FAILED_BATCHES batch(es) failed" | tee -a "$NIGHT_LOG"
    STATUS="PARTIAL"
fi

if [ "$TOTAL_DISCOVERED" -lt "$EXPECTED" ]; then
    SHORTFALL=$((EXPECTED - TOTAL_DISCOVERED))
    echo "⚠️  Below target: $TOTAL_DISCOVERED discovered, $SHORTFALL short of $EXPECTED" | tee -a "$NIGHT_LOG"
    STATUS="RETRY"
else
    SURPLUS=$((TOTAL_DISCOVERED - EXPECTED))
    echo "✅ Above target: $TOTAL_DISCOVERED discovered (+$SURPLUS over target)" | tee -a "$NIGHT_LOG"
    STATUS="PASS"
fi

# 8. Report final health
echo "{\"status\": \"complete\", \"discovered\": $TOTAL_DISCOVERED, \"target\": $EXPECTED, \"failed_batches\": $FAILED_BATCHES, \"status_final\": \"$STATUS\", \"completed_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > "$HEALTH_FILE"

echo "Night work complete at $(date)" | tee -a "$NIGHT_LOG"
echo "Results: $TOTAL_DISCOVERED websites discovered (target: $EXPECTED)" | tee -a "$NIGHT_LOG"

if [ "$STATUS" = "PASS" ]; then
    exit 0
else
    exit 1
fi
