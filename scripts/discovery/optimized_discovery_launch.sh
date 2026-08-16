#!/bin/bash

# Optimized 12-hour discovery blitz
# 4 parallel daemons, 500 orgs/batch, minimal rate limiting
# Target: 111K+ new links in 12 hours

cd /home/akbar/meritgiving
source venv/bin/activate

BATCH_SIZE=500
SLEEP_BETWEEN_ORGS=0.1   # Was 0.5s, now 100ms (safe rate limit)
SLEEP_BETWEEN_BATCHES=1   # Was 5s, now 1s
NUM_INSTANCES=4

# Calculate expected throughput
# Each batch: 500 orgs * 0.1s = 50s + 1s batch sleep = 51s/batch
# Throughput: 500 orgs/51s ≈ 10 orgs/s per instance
# 4 instances = 40 orgs/s total
# Assuming 50% yield (2 links/org) = 40 orgs/s * 2 = 80 links/sec
# 12 hours = 43,200s ≈ 3.4M link discovery attempts
# Conservative estimate: 1.7M verified new links in 12 hours (but capped by remaining 111K orgs)
echo "Expected throughput:"
echo "  - Per instance: ~10 orgs/sec"
echo "  - Total (4x): ~40 orgs/sec"
echo "  - If 50% yield: ~80 links/sec"
echo "  - Coverage: 111K remaining orgs in ~45 minutes (best case)"

echo "========================================="
echo "🚀 OPTIMIZED DISCOVERY BLITZ (12 HOURS)"
echo "========================================="
echo "Batch size: $BATCH_SIZE orgs"
echo "Rate limit: ${SLEEP_BETWEEN_ORGS}s/org, ${SLEEP_BETWEEN_BATCHES}s/batch"
echo "Instances: $NUM_INSTANCES (parallel)"
echo "Expected capacity: ~${BATCH_SIZE}K+ links in 12h"
echo "========================================="

# Start N parallel daemons
for i in $(seq 1 $NUM_INSTANCES); do
  echo "[Instance $i] Starting daemon..."

  python3 -u scripts/discovery_daemon.py $BATCH_SIZE $SLEEP_BETWEEN_ORGS $SLEEP_BETWEEN_BATCHES \
    2>&1 | sed "s/^/[D$i] /" >> logs/discovery_daemon_blitz.log &

  PIDS[$i]=$!
  echo "[Instance $i] PID ${PIDS[$i]}"

  # Stagger startup to avoid thundering herd
  sleep 0.5
done

echo ""
echo "All instances started. Monitoring progress..."
echo ""

# Monitor function
monitor_progress() {
  while true; do
    sleep 30

    echo "=== Progress Check ($(date '+%H:%M:%S')) ==="

    # Count discovered links in last 30s from logs
    discovered=$(tail -100 logs/discovery_daemon_blitz.log | grep -c "verified")

    # Total in database
    total_links=$(sqlite3 data/merit_registry.db \
      "SELECT COUNT(*) FROM registry_enriched WHERE donate_url IS NOT NULL OR volunteer_url IS NOT NULL;")

    # Remaining to discover
    remaining=$(sqlite3 data/merit_registry.db \
      "SELECT COUNT(*) FROM registry_enriched WHERE website IS NOT NULL AND website != '' AND (donate_url IS NULL OR volunteer_url IS NULL);")

    echo "Database: $total_links links total | $remaining orgs needing discovery"
    echo "Recent activity: ~$discovered verifications/30s"
    echo ""
  done
}

# Start monitor in background
monitor_progress &
MONITOR_PID=$!

# Wait for all daemons to complete (they won't — they run continuously)
# User can Ctrl+C to stop all instances
trap "echo ''; echo 'Stopping all instances...'; kill ${PIDS[@]} $MONITOR_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait ${PIDS[@]}
