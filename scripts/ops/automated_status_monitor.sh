#!/bin/bash
# Automated Status Monitor — Daanaa Autonomous Operations
# Runs continuously, logs system health, updates status reports
# Invoke: ./automated_status_monitor.sh &

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATUS_FILE="$PROJECT_ROOT/institution/DAILY_STATUS_REPORT.md"
HEALTH_LOG="$PROJECT_ROOT/logs/health_monitor.log"
API_URL="http://localhost:5000"

# Ensure logs directory exists
mkdir -p "$PROJECT_ROOT/logs"

log_status() {
    local timestamp=$(date -u '+%Y-%m-%d %H:%M:%S UTC')
    local message="$1"
    echo "[$timestamp] $message" >> "$HEALTH_LOG"
    echo "$message"
}

check_api_health() {
    local health=$(curl -s "$API_URL/api/health" 2>/dev/null || echo "OFFLINE")
    if [ "$health" = "OK" ]; then
        echo "✅"
    else
        echo "❌"
    fi
}

check_database() {
    # Quick database connectivity check
    if sqlite3 "$PROJECT_ROOT/data/merit_registry.db" "SELECT 1" >/dev/null 2>&1; then
        echo "✅"
    else
        echo "❌"
    fi
}

check_git_status() {
    # Check for uncommitted changes
    if [ -z "$(cd "$PROJECT_ROOT" && git status --porcelain)" ]; then
        echo "✅"
    else
        echo "⚠️"
    fi
}

count_endpoints() {
    grep -c "^@app.route" "$PROJECT_ROOT/daanaa_api.py" || echo "?"
}

update_status_report() {
    cat > "$STATUS_FILE" << EOF
# Daily Status Report — Daanaa Operations
**Generated:** $(date -u '+%Y-%m-%d %H:%M:%S UTC')
**Report Period:** Last 24 hours
**Authority:** Autonomous system monitoring

---

## 🟢 System Status

| Component | Status | Last Check |
|-----------|--------|-----------|
| **API Server** | $(check_api_health) | $(date -u '+%H:%M UTC') |
| **Database** | $(check_database) | $(date -u '+%H:%M UTC') |
| **Git Status** | $(check_git_status) | $(date -u '+%H:%M UTC') |

---

## 📊 Code Metrics

- **Total Endpoints:** $(count_endpoints)
- **Migrations:** $(ls -1 "$PROJECT_ROOT/migrations/"*.sql 2>/dev/null | wc -l)
- **Last Commit:** $(cd "$PROJECT_ROOT" && git log -1 --format='%h %s' 2>/dev/null || echo "Unknown")

---

## 🔄 Autonomous Work Queue

1. **Data Pipeline Population** — Financial health scoring
   - Status: QUEUED
   - ETA: 2-3 days

2. **Integration Testing** — End-to-end validation
   - Status: QUEUED
   - ETA: 4 hours

3. **Automated Monitoring** — Health checks
   - Status: ACTIVE
   - Check interval: 15 min

---

**Next Update:** $(date -u -d '+15 minutes' '+%Y-%m-%d %H:%M:%S UTC')
**Monitor Log:** $HEALTH_LOG

EOF
}

# Main monitoring loop
log_status "=== Autonomous Status Monitor Started ==="
log_status "Project: $PROJECT_ROOT"
log_status "API URL: $API_URL"
log_status "Check interval: 15 minutes"

while true; do
    log_status "Health check in progress..."

    # Run checks
    api_health=$(check_api_health)
    db_health=$(check_database)
    git_status=$(check_git_status)

    log_status "API: $api_health | Database: $db_health | Git: $git_status"

    # Sample endpoint queries
    if [ "$api_health" = "✅" ]; then
        org_test=$(curl -s "$API_URL/api/nonprofit/123456789/financial-health" 2>/dev/null | grep -c "ein" || echo "0")
        log_status "Phase 11 sample query: $org_test records"
    fi

    # Update status report
    update_status_report
    log_status "Status report updated: $STATUS_FILE"

    # Wait before next check
    log_status "Sleeping 15 minutes..."
    sleep 900

done
