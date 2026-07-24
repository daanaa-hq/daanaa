#!/bin/bash
# Continuous Site Health Monitor
# Runs every 5 minutes; alerts on critical issues
# Auto-recovery actions on failures

set -euo pipefail

SITE="https://daanaa.org"
CHECK_INTERVAL=300  # 5 minutes
BASE_LOG_DIR="${BASE_LOG_DIR:-/home/akbar/meritgiving/logs}"
LOG_FILE="$BASE_LOG_DIR/monitor.log"
ALERT_LOG="$BASE_LOG_DIR/alerts.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"; }
alert() {
  msg="[ALERT] $*"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $msg" | tee -a "$ALERT_LOG"
  # TODO: Send to Slack, PagerDuty, or email here
}

check_site_status() {
  # Quick check: homepage should return 200 within 5 seconds
  local code=$(curl -s -m 5 -o /dev/null -w '%{http_code}' "$SITE/" 2>/dev/null || echo "000")

  if [ "$code" != "200" ]; then
    log "❌ Site returned $code"
    return 1
  fi

  log "✓ Site healthy (200)"
  return 0
}

check_search_performance() {
  # Search is a known slow endpoint; monitor separately
  local start=$(date +%s%N)
  curl -s -m 10 -o /dev/null "https://daanaa.org/api/search?q=test&per_page=1" 2>/dev/null || true
  local end=$(date +%s%N)
  local duration_ms=$(( (end - start) / 1000000 ))

  if [ $duration_ms -gt 5000 ]; then
    alert "Search endpoint slow: ${duration_ms}ms (threshold: 5000ms)"
    return 1
  fi

  log "✓ Search performance OK: ${duration_ms}ms"
  return 0
}

check_api_health() {
  # Check local API
  local code=$(curl -s -m 5 -o /dev/null -w '%{http_code}' "http://127.0.0.1:5000/health" 2>/dev/null || echo "000")

  if [ "$code" != "200" ]; then
    alert "Local API unhealthy: $code"
    return 1
  fi

  log "✓ API healthy"
  return 0
}

recover_on_failure() {
  log "🔧 Attempting recovery..."

  # Try to restart the service
  if systemctl restart daanaa 2>/dev/null; then
    log "✓ Service restarted"
    sleep 5

    # Verify recovery
    if check_site_status; then
      log "✓ Recovery successful"
      return 0
    fi
  fi

  alert "Recovery failed — manual intervention needed"
  return 1
}

main() {
  log "Monitor started"

  while true; do
    failed=0

    check_site_status || failed=1
    check_api_health || failed=1

    if [ $failed -eq 1 ]; then
      alert "Health check failed — initiating recovery"
      recover_on_failure || true
    fi

    sleep $CHECK_INTERVAL
  done
}

main "$@"
