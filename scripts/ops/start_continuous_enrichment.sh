#!/bin/bash
# Start continuous enrichment services on home server (not droplet).
#
# Architecture:
#   - Phase 1 (nightly 8pm-8am): GPU missions + scoring (existing overnight_pipeline.py)
#   - Phase 2 (24/7): Website discovery service (continuous_website_scraper.py)
#   - Phase 3 (24/7): Cascading link scraper (cascading_link_scraper.py)
#
# All three run on home server. Only precomputed outputs sync to droplet.

set -e
cd "$(dirname "$0")/../.."

source ~/meritgiving/venv/bin/activate

PROJECT_DIR="$(pwd)"
LOG_DIR="$PROJECT_DIR/logs/enrichment"
mkdir -p "$LOG_DIR"

echo "=== Starting Continuous Enrichment Services ==="
echo "Server: Home (Ryzen 9 7900X, 30GB RAM, GPU)"
echo "Log directory: $LOG_DIR"
echo ""

# Phase 2: Continuous Website Discovery
echo "[Phase 2] Starting website discovery service (24/7)..."
nohup python3 scripts/continuous_website_scraper.py \
  --workers 8 \
  --delay 5 \
  > "$LOG_DIR/continuous_website_scraper.log" 2>&1 &
PHASE2_PID=$!
echo "  PID: $PHASE2_PID"

# Phase 3: Cascading Link Scraper
echo "[Phase 3] Starting cascading link discovery service (24/7)..."
nohup python3 scripts/cascading_link_scraper.py \
  --workers 4 \
  --delay 10 \
  > "$LOG_DIR/cascading_link_scraper.log" 2>&1 &
PHASE3_PID=$!
echo "  PID: $PHASE3_PID"

echo ""
echo "=== Services Started ==="
echo "Phase 2 (website discovery): PID $PHASE2_PID"
echo "Phase 3 (cascading links): PID $PHASE3_PID"
echo ""
echo "Logs:"
echo "  tail -f $LOG_DIR/continuous_website_scraper.log"
echo "  tail -f $LOG_DIR/cascading_link_scraper.log"
echo ""
echo "To stop services:"
echo "  kill $PHASE2_PID $PHASE3_PID"
echo "  pkill -f continuous_website_scraper.py"
echo "  pkill -f cascading_link_scraper.py"
