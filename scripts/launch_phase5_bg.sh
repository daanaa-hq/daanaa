#!/bin/bash
#
# launch_phase5_bg.sh — Launch Phase 5 Mission & Cause Backfill in background.
#
# Health checks:
# 1. Verify Qwen2.5-32B is healthy on port 11437
# 2. Verify Phase 4 is complete (semantic_match column exists + count > 0)
# 3. Verify database is accessible
# 4. Start phase5_mission_backfill.py in background
# 5. Monitor for crashes (auto-restart with backoff)
#
# Usage:
#     bash scripts/launch_phase5_bg.sh               # Start fresh
#     bash scripts/launch_phase5_bg.sh --resume      # Resume from checkpoint
#     bash scripts/launch_phase5_bg.sh --dry-run     # Test mode
#     bash scripts/launch_phase5_bg.sh --stop        # Stop monitoring
#
# Output:
#     - /tmp/phase5_progress.log (detailed progress)
#     - /home/akbar/meritgiving/logs/phase5_monitor.log (health checks)
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
DB_PATH="$BASE_DIR/data/merit_registry.db"
PROGRESS_LOG="/tmp/phase5_progress.log"
MONITOR_LOG="$BASE_DIR/logs/phase5_monitor.log"
PID_FILE="/tmp/phase5_mission_backfill.pid"
CHECKPOINT_PATH="$BASE_DIR/logs/phase5_checkpoint.json"

PYTHON="${PYTHON:-python3}"
LLM_PORT=11437
LLM_HEALTH_URL="http://127.0.0.1:$LLM_PORT/health"

# Colors for output
RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
BLUE='\033[94m'
RESET='\033[0m'

# Config
CRASH_BACKOFF_SECS=30
MAX_RETRIES=5

# Ensure logs directory exists
mkdir -p "$(dirname "$MONITOR_LOG")"
touch "$PROGRESS_LOG"

log() {
    local ts=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    echo "[$ts] $*" | tee -a "$MONITOR_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${RESET} $*" | tee -a "$MONITOR_LOG"
}

log_success() {
    echo -e "${GREEN}[OK]${RESET} $*" | tee -a "$MONITOR_LOG"
}

log_info() {
    echo -e "${BLUE}[INFO]${RESET} $*" | tee -a "$MONITOR_LOG"
}

check_db() {
    log_info "Checking database..."
    if [[ ! -f "$DB_PATH" ]]; then
        log_error "Database not found: $DB_PATH"
        return 1
    fi

    # Check if website_status column exists (Phase 4 uses this)
    if ! $PYTHON -c "
import sqlite3
conn = sqlite3.connect('$DB_PATH', timeout=5)
cursor = conn.execute('PRAGMA table_info(registry_enriched)')
cols = [row[1] for row in cursor.fetchall()]
if 'website_status' not in cols:
    print('website_status column not found')
    exit(1)
conn.close()
" 2>/dev/null; then
        log_error "Database schema incomplete: website_status column missing"
        return 1
    fi

    # Check org count available for mission generation (deductible + active)
    count=$($PYTHON -c "
import sqlite3
conn = sqlite3.connect('$DB_PATH', timeout=5)
cursor = conn.execute('SELECT COUNT(*) FROM registry_enriched WHERE deductibility=1 AND org_status=\"active\"')
count = cursor.fetchone()[0]
conn.close()
print(count)
")

    if (( count == 0 )); then
        log_error "No eligible orgs found (need deductible=1 AND org_status='active')"
        return 1
    fi

    log_success "Database OK ($count verified orgs)"
    return 0
}

check_llm() {
    log_info "Checking Qwen2.5-32B on port $LLM_PORT..."

    # Try health endpoint first
    if curl -s "$LLM_HEALTH_URL" > /dev/null 2>&1; then
        log_success "LLM health OK"
        return 0
    fi

    # Fallback: try a simple request
    if curl -s -X POST http://127.0.0.1:$LLM_PORT/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{"model":"test","messages":[{"role":"user","content":"hi"}],"max_tokens":1}' \
        > /dev/null 2>&1; then
        log_success "LLM responding"
        return 0
    fi

    log_error "Qwen2.5-32B not responding on port $LLM_PORT"
    log_error "Start with: llama-server -m /mnt/models/Qwen2.5-32B-Instruct-Q4_K_M.gguf -ngl 80 -t 8 -c 4096 --port $LLM_PORT"
    return 1
}

start_phase5() {
    local args="$@"
    log_info "Starting Phase 5 mission backfill..."
    log_info "Command: $PYTHON $SCRIPT_DIR/phase5_mission_backfill.py $args"

    # Activate venv if exists
    if [[ -f "$BASE_DIR/venv/bin/activate" ]]; then
        source "$BASE_DIR/venv/bin/activate"
    fi

    # Start process in background
    nohup $PYTHON "$SCRIPT_DIR/phase5_mission_backfill.py" $args \
        >> "$PROGRESS_LOG" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_FILE"

    log_success "Started with PID $pid"
    log_info "Progress: tail -f $PROGRESS_LOG"
    log_info "Monitor: tail -f $MONITOR_LOG"

    return 0
}

monitor_process() {
    log_info "Monitoring Phase 5 process..."
    local retry_count=0

    while true; do
        if [[ ! -f "$PID_FILE" ]]; then
            log_error "PID file missing, exiting monitor"
            break
        fi

        local pid=$(cat "$PID_FILE")

        # Check if process is still running
        if ! kill -0 "$pid" 2>/dev/null; then
            log_error "Process $pid died unexpectedly"
            rm -f "$PID_FILE"

            retry_count=$((retry_count + 1))
            if (( retry_count >= MAX_RETRIES )); then
                log_error "Max retries ($MAX_RETRIES) exceeded. Giving up."
                break
            fi

            log_info "Restarting in ${CRASH_BACKOFF_SECS}s (attempt $retry_count/$MAX_RETRIES)..."
            sleep "$CRASH_BACKOFF_SECS"

            # Check health again before restart
            if ! check_llm; then
                log_error "LLM still not healthy, skipping restart"
                sleep 60
                continue
            fi

            # Restart with --resume
            start_phase5 --resume
            continue
        fi

        # Process still running - check progress every minute
        local lines=$(wc -l < "$PROGRESS_LOG")
        local last_line=$(tail -1 "$PROGRESS_LOG" 2>/dev/null || echo "")
        log_info "Process $pid running. Log lines: $lines. Last: ${last_line:0:80}..."

        sleep 60
    done
}

handle_stop() {
    log_info "Stopping Phase 5..."
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log_info "Sending SIGTERM to process $pid..."
            kill -TERM "$pid"
            sleep 5
            if kill -0 "$pid" 2>/dev/null; then
                log_info "Process still running, sending SIGKILL..."
                kill -KILL "$pid"
            fi
        fi
        rm -f "$PID_FILE"
        log_success "Process stopped"
    else
        log_info "No process running"
    fi
}

# Main entry point
main() {
    local args=""
    local resume=false
    local dry_run=false
    local stop=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --resume)
                resume=true
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --stop)
                stop=true
                shift
                ;;
            *)
                args="$args $1"
                shift
                ;;
        esac
    done

    # Handle --stop
    if [[ "$stop" == "true" ]]; then
        handle_stop
        exit 0
    fi

    # Run health checks
    log "Phase 5 Launcher — $(date -u)"
    log "========================================"

    if ! check_db; then
        log_error "Database check failed. Cannot proceed."
        exit 1
    fi

    if ! check_llm; then
        log_error "LLM check failed. Cannot proceed."
        exit 1
    fi

    log_success "All health checks passed"
    log ""

    # Build arguments
    if [[ "$resume" == "true" ]]; then
        args="--resume $args"
    fi
    if [[ "$dry_run" == "true" ]]; then
        args="--dry-run $args"
    fi

    # Check if already running
    if [[ -f "$PID_FILE" ]]; then
        local old_pid=$(cat "$PID_FILE")
        if kill -0 "$old_pid" 2>/dev/null; then
            log_error "Phase 5 already running with PID $old_pid"
            log_error "Use --stop to stop, or --resume to continue"
            exit 1
        fi
    fi

    # Start and monitor
    start_phase5 $args
    monitor_process
}

# Run main
main "$@"
