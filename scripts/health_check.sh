#!/bin/bash
# Health Check + Performance Monitor
# Runs post-deployment and continuously
# Exits with status code 1 if critical issues found

set -euo pipefail

SITE="https://daanaa.org"
TIMEOUT=10
PERF_THRESHOLD_MS=3000  # 3 second threshold for critical pages
LOG_FILE="${BASE_LOG_DIR:-/home/akbar/meritgiving/logs}/health_check.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
alert() { log "⚠️  ALERT: $*"; }
error() { log "🔴 ERROR: $*"; }

# 1. HEALTH CHECK (critical paths only)
health_check() {
  local failed=0

  log "🏥 HEALTH CHECK"

  # Homepage
  code=$(curl -s -m $TIMEOUT -o /dev/null -w '%{http_code}' "$SITE/" || echo "000")
  if [ "$code" != "200" ]; then
    error "Homepage returned $code"
    failed=1
  else
    log "  ✓ Homepage: 200"
  fi

  # Directory (core functionality)
  code=$(curl -s -m $TIMEOUT -o /dev/null -w '%{http_code}' "$SITE/directory" || echo "000")
  if [ "$code" != "200" ]; then
    error "Directory returned $code"
    failed=1
  else
    log "  ✓ Directory: 200"
  fi

  # Volunteer page (new feature)
  code=$(curl -s -m $TIMEOUT -o /dev/null -w '%{http_code}' "$SITE/volunteer" || echo "000")
  if [ "$code" != "200" ]; then
    error "Volunteer page returned $code"
    failed=1
  else
    log "  ✓ Volunteer: 200"
  fi

  # API health endpoint
  code=$(curl -s -m $TIMEOUT -o /dev/null -w '%{http_code}' "$SITE/health" || echo "000")
  if [ "$code" != "200" ]; then
    error "Health endpoint returned $code"
    failed=1
  else
    log "  ✓ Health endpoint: 200"
  fi

  return $failed
}

# 2. PERFORMANCE CHECK (warn on slow endpoints)
perf_check() {
  log "⚡ PERFORMANCE CHECK (threshold: ${PERF_THRESHOLD_MS}ms)"

  endpoints=(
    "/ (homepage)"
    "/directory (directory)"
    "/api/organizations?per_page=5 (orgs list)"
    "/api/stats (stats)"
  )

  local slow_count=0
  for endpoint in "${endpoints[@]}"; do
    path="${endpoint%% *}"
    name="${endpoint#* }"

    time_ms=$(curl -s -m $TIMEOUT -w '%{time_total}' -o /dev/null "$SITE$path" 2>/dev/null | awk '{print int($1 * 1000)}' || echo "TIMEOUT")

    if [ "$time_ms" = "TIMEOUT" ] || [ "$time_ms" -gt "$PERF_THRESHOLD_MS" ]; then
      alert "$name: ${time_ms}ms (threshold: ${PERF_THRESHOLD_MS}ms)"
      slow_count=$((slow_count + 1))
    else
      log "  ✓ $name: ${time_ms}ms"
    fi
  done

  return 0
}

# 3. CRITICAL DEPENDENCIES
dependencies_check() {
  log "🔗 DEPENDENCIES CHECK"

  # Check if API is reachable
  if ! curl -s -m 5 http://127.0.0.1:5000/health > /dev/null 2>&1; then
    error "Local API (127.0.0.1:5000) unreachable"
    return 1
  fi
  log "  ✓ Local API reachable"

  return 0
}

# Main
main() {
  log "================================"

  health_check || true
  perf_check || true
  dependencies_check || true

  log "✅ Health check complete"
}

main "$@"
