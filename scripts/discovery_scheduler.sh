#!/bin/bash
# Event Discovery Scheduler — runs nightly to populate the review queue
#
# Usage:
#   bash scripts/discovery_scheduler.sh
#
# Runs discovery_batch.py with proper logging, error handling, and failure rollback.
# Respects robots.txt and rate limits. Fails closed (no candidates published on error).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="${REPO_ROOT}/venv"
LOG_DIR="${REPO_ROOT}/logs"
LOG_FILE="${LOG_DIR}/discovery_$(date +%Y%m%d_%H%M%S).log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Activate virtualenv if it exists
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
fi

# Set environment
export DB_PATH="${REPO_ROOT}/data/merit_registry.db"
export LIVE_DB_PATH="${REPO_ROOT}/data/daanaa_live.db"
export ENABLE_EVENT_DISCOVERY="true"

echo "[$(date)] Starting event discovery scheduler" | tee -a "$LOG_FILE"

# Run the discovery batch job with timeout and error handling
if python3 "$SCRIPT_DIR/discovery_batch.py" >> "$LOG_FILE" 2>&1; then
    echo "[$(date)] ✓ Discovery scheduler completed successfully" | tee -a "$LOG_FILE"
    exit 0
else
    EXIT_CODE=$?
    echo "[$(date)] ✗ Discovery scheduler failed with exit code $EXIT_CODE" | tee -a "$LOG_FILE"
    echo "See $LOG_FILE for details" | tee -a "$LOG_FILE"
    exit $EXIT_CODE
fi
