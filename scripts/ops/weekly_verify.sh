#!/usr/bin/env bash
# =============================================================================
# weekly_verify.sh - Weekly IRS Verification Automation Wrapper
# =============================================================================
# Usage:
#   ./weekly_verify.sh [--dry-run] [--force-download] [--setup-cron]
#
# Environment Variables:
#   IRS_DATA_DIR         - Base directory for IRS data
#   MASTER_ORGS_CSV      - Path to master_orgs.csv
#   REPORTS_DIR          - Directory for verification reports
#   IRS_VERIFY_LOG       - Log file path (default: /var/log/merit/irs_verify.log)
#   IRS_PYTHON           - Python interpreter path (auto-detected)
#   IRS_VERIFY_SCRIPT    - Path to irs_verify.py (default: same dir as this script)
#   SLACK_WEBHOOK_URL    - Slack webhook for notifications
#   NOTIFY_EMAIL         - Email address for notifications
#
# Cron Setup:
#   Add to crontab: 0 2 * * 0 /path/to/weekly_verify.sh
#   (Runs every Sunday at 2:00 AM)
# =============================================================================

set -euo pipefail
IFS=$'\n\t'

# ── Configuration ───────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename "$0")"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE_HUMAN=$(date +"%Y-%m-%d %H:%M:%S %Z")

# Paths (overridable via environment)
IRS_DATA_DIR="${IRS_DATA_DIR:-/home/akbar/meritgiving/data/raw/irs_authority}"
MASTER_ORGS_CSV="${MASTER_ORGS_CSV:-/home/akbar/meritgiving/data/master_orgs.csv}"
REPORTS_DIR="${REPORTS_DIR:-/home/akbar/meritgiving/data/reports}"
IRS_VERIFY_LOG="${IRS_VERIFY_LOG:-/var/log/merit/irs_verify.log}"
LOCK_FILE="${IRS_DATA_DIR}/.weekly_verify.lock"

# Python interpreter (auto-detect)
IRS_PYTHON="${IRS_PYTHON:-$(command -v python3 || command -v python || echo "python3")}"
IRS_VERIFY_SCRIPT="${IRS_VERIFY_SCRIPT:-${SCRIPT_DIR}/irs_verify.py}"

# Flags
DRY_RUN=false
FORCE_DOWNLOAD=false
SETUP_CRON=false

# ── Utility Functions ───────────────────────────────────────────────────────

log() {
    local level="$1"
    shift
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] ${SCRIPT_NAME}: $*"
    echo "$msg"
    # Also write to log file if directory exists
    if [[ -d "$(dirname "$IRS_VERIFY_LOG")" ]]; then
        echo "$msg" >> "$IRS_VERIFY_LOG" 2>/dev/null || true
    fi
}

die() {
    log "ERROR" "$@"
    exit 1
}

cleanup() {
    local rc=$?
    if [[ -f "$LOCK_FILE" ]]; then
        rm -f "$LOCK_FILE"
        log "INFO" "Lock file released"
    fi
    if [[ $rc -ne 0 ]]; then
        log "ERROR" "Script exited with code $rc"
    fi
    exit $rc
}

trap cleanup EXIT INT TERM

acquire_lock() {
    if [[ -f "$LOCK_FILE" ]]; then
        local pid
        pid=$(cat "$LOCK_FILE" 2>/dev/null) || pid="unknown"
        if kill -0 "$pid" 2>/dev/null; then
            die "Another instance is already running (PID: $pid). Exiting."
        else
            log "WARN" "Stale lock file found (PID: $pid). Removing."
            rm -f "$LOCK_FILE"
        fi
    fi
    echo $$ > "$LOCK_FILE"
    log "INFO" "Lock acquired (PID: $$)"
}

check_dependencies() {
    log "INFO" "Checking dependencies..."

    # Python
    if ! command -v "$IRS_PYTHON" &>/dev/null; then
        die "Python interpreter not found: $IRS_PYTHON. Install Python 3.8+."
    fi
    local py_version
    py_version=$($IRS_PYTHON --version 2>&1 | awk '{print $2}')
    log "INFO" "Python version: $py_version"

    # Python packages
    if ! $IRS_PYTHON -c "import requests" 2>/dev/null; then
        log "WARN" "Python 'requests' library not found. Attempting install..."
        $IRS_PYTHON -m pip install --user requests || die "Failed to install 'requests'"
    fi

    # Required directories
    for d in "$IRS_DATA_DIR" "$(dirname "$MASTER_ORGS_CSV")" "$REPORTS_DIR"; do
        if [[ ! -d "$d" ]]; then
            log "INFO" "Creating directory: $d"
            mkdir -p "$d" || die "Cannot create directory: $d"
        fi
    done

    # Master CSV exists (or create stub for first run)
    if [[ ! -f "$MASTER_ORGS_CSV" ]]; then
        log "WARN" "Master CSV not found at $MASTER_ORGS_CSV"
        log "WARN" "Creating stub file with required headers"
        cat > "$MASTER_ORGS_CSV" <<'EOF'
EIN,organization_name,record_status,pub78_verified_date,irs_revocation_date,irs_reinstatement_date,irs_deductibility_code,irs_exemption_type
EOF
        log "INFO" "Stub master CSV created. Populate with your organization records."
    fi

    # Verify script exists
    if [[ ! -f "$IRS_VERIFY_SCRIPT" ]]; then
        die "irs_verify.py not found at: $IRS_VERIFY_SCRIPT"
    fi

    # Log directory
    local log_dir
    log_dir=$(dirname "$IRS_VERIFY_LOG")
    if [[ ! -d "$log_dir" ]]; then
        log "INFO" "Creating log directory: $log_dir"
        mkdir -p "$log_dir" || IRS_VERIFY_LOG="${IRS_DATA_DIR}/irs_verify.log"
    fi

    log "INFO" "All dependencies satisfied"
}

rotate_logs() {
    if [[ -f "$IRS_VERIFY_LOG" ]]; then
        local size
        size=$(stat -c%s "$IRS_VERIFY_LOG" 2>/dev/null || stat -f%z "$IRS_VERIFY_LOG" 2>/dev/null || echo "0")
        if [[ "$size" -gt 52428800 ]]; then  # 50 MB
            local archived="${IRS_VERIFY_LOG}.${TIMESTAMP}"
            mv "$IRS_VERIFY_LOG" "$archived"
            gzip -f "$archived" &>/dev/null || true
            log "INFO" "Log rotated: ${archived}.gz"
        fi
    fi
}

setup_cron_job() {
    log "INFO" "Setting up weekly cron job..."

    local cron_entry="0 2 * * 0 ${SCRIPT_DIR}/${SCRIPT_NAME} # MERIT IRS Weekly Verification"
    local cron_file="/tmp/merit_irs_cron.$$"

    # Export current crontab
    crontab -l 2>/dev/null > "$cron_file" || true

    # Check if already exists
    if grep -qF "${SCRIPT_DIR}/${SCRIPT_NAME}" "$cron_file" 2>/dev/null; then
        log "INFO" "Cron job already exists. Skipping."
        rm -f "$cron_file"
        return 0
    fi

    # Add new entry
    echo "$cron_entry" >> "$cron_file"
    crontab "$cron_file" || die "Failed to install crontab"
    rm -f "$cron_file"

    log "INFO" "Cron job installed: $cron_entry"
    log "INFO" "Schedule: Every Sunday at 2:00 AM"
    log "INFO" "Verify with: crontab -l"
}

send_notification() {
    local status="$1"
    local report_file="$2"

    # If Slack webhook is configured
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local payload
        payload=$(cat <<EOF
{
    "text": "MERIT IRS Weekly Verification Complete",
    "attachments": [{
        "color": "$([[ "$status" == "SUCCESS" ]] && echo "good" || echo "danger")",
        "fields": [
            {"title": "Status", "value": "$status", "short": true},
            {"title": "Date", "value": "$DATE_HUMAN", "short": true},
            {"title": "Report", "value": "$report_file", "short": false}
        ]
    }]
}
EOF
)
        curl -s -X POST -H "Content-type: application/json" \
            --data "$payload" "$SLACK_WEBHOOK_URL" &>/dev/null || true
    fi

    # If email is configured
    if [[ -n "${NOTIFY_EMAIL:-}" ]] && command -v mail &>/dev/null; then
        local subject="MERIT IRS Verification - $status - $DATE_HUMAN"
        echo "Weekly IRS verification completed with status: $status" | \
            mail -s "$subject" "$NOTIFY_EMAIL" || true
    fi
}

# ── Argument Parsing ────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force-download)
            FORCE_DOWNLOAD=true
            shift
            ;;
        --setup-cron)
            SETUP_CRON=true
            shift
            ;;
        --help|-h)
            cat <<'EOF'
Usage: weekly_verify.sh [OPTIONS]

OPTIONS:
  --dry-run          Simulate without modifying master CSV
  --force-download   Force re-download even if files exist
  --setup-cron       Install weekly cron job and exit
  --help, -h         Show this help message

ENVIRONMENT VARIABLES:
  IRS_DATA_DIR       Base directory for IRS data
  MASTER_ORGS_CSV    Path to master_orgs.csv
  REPORTS_DIR        Directory for verification reports
  IRS_VERIFY_LOG     Log file path
  SLACK_WEBHOOK_URL  Slack webhook for notifications
  NOTIFY_EMAIL       Email address for notifications

EXAMPLES:
  # First run (dry-run to preview)
  ./weekly_verify.sh --dry-run

  # Normal weekly run
  ./weekly_verify.sh

  # Force re-download IRS files
  ./weekly_verify.sh --force-download

  # Install cron job
  ./weekly_verify.sh --setup-cron
EOF
            exit 0
            ;;
        *)
            die "Unknown option: $1 (use --help for usage)"
            ;;
    esac
done

# ── Main Execution ──────────────────────────────────────────────────────────

log "INFO" "========================================"
log "INFO" "MERIT IRS Weekly Verification Starting"
log "INFO" "========================================"

# Setup cron if requested
if [[ "$SETUP_CRON" == true ]]; then
    setup_cron_job
    exit 0
fi

# Pre-flight checks
acquire_lock
check_dependencies
rotate_logs

# Build Python command
PY_ARGS=(
    "$IRS_VERIFY_SCRIPT"
    --timeout 300
    --max-retries 3
)

if [[ "$DRY_RUN" == true ]]; then
    PY_ARGS+=("--dry-run")
    log "INFO" "Mode: DRY RUN (no changes to master CSV)"
fi

if [[ "$FORCE_DOWNLOAD" == true ]]; then
    PY_ARGS+=("--force-download")
    log "INFO" "Mode: Force download enabled"
fi

# Export environment for Python script
export IRS_DATA_DIR
export MASTER_ORGS_CSV
export REPORTS_DIR

log "INFO" "IRS_DATA_DIR    = $IRS_DATA_DIR"
log "INFO" "MASTER_ORGS_CSV = $MASTER_ORGS_CSV"
log "INFO" "REPORTS_DIR     = $REPORTS_DIR"
log "INFO" "Executing: $IRS_PYTHON ${PY_ARGS[*]}"

# Run verification
START_TIME=$(date +%s)

if "$IRS_PYTHON" "${PY_ARGS[@]}" 2>&1 | tee -a "$IRS_VERIFY_LOG"; then
    EXIT_CODE=${PIPESTATUS[0]}
else
    EXIT_CODE=${PIPESTATUS[0]}
fi

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

# Find latest report
LATEST_REPORT=$(find "$REPORTS_DIR" -name "verification_weekly_*.csv" -type f -printf '%T@ %p\n' 2>/dev/null | \
    sort -rn | head -n1 | cut -d' ' -f2- || echo "none")
[[ -z "$LATEST_REPORT" ]] && LATEST_REPORT="none"

# Summary
log "INFO" "========================================"
if [[ $EXIT_CODE -eq 0 ]]; then
    log "INFO" "RESULT: SUCCESS (exit code 0)"
    send_notification "SUCCESS" "$LATEST_REPORT"
else
    log "ERROR" "RESULT: FAILURE (exit code $EXIT_CODE)"
    send_notification "FAILURE" "$LATEST_REPORT"
fi
log "INFO" "Duration: ${ELAPSED}s"
log "INFO" "Latest report: $LATEST_REPORT"
log "INFO" "Log file: $IRS_VERIFY_LOG"
log "INFO" "========================================"

exit $EXIT_CODE
