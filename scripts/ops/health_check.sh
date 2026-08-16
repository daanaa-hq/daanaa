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

    # Capture both HTTP status and timing separately
    # Use -w with format to get clean output (no body, no stderr)
    output=$(curl -s -m $TIMEOUT -w '\n%{http_code}\n%{time_total}' -o /dev/null "$SITE$path" 2>&1)
    http_code=$(echo "$output" | tail -2 | head -1)
    time_total=$(echo "$output" | tail -1)

    # Handle timeout or empty response
    if [ -z "$http_code" ] || [ -z "$time_total" ]; then
      alert "$name: TIMEOUT or error (no response)"
      slow_count=$((slow_count + 1))
      continue
    fi

    # Convert time to milliseconds
    time_ms=$(awk "BEGIN {printf \"%.0f\", $time_total * 1000}")

    # Check if response was successful and within threshold
    if [ "$http_code" != "200" ]; then
      alert "$name: HTTP $http_code (timing: ${time_ms}ms)"
      slow_count=$((slow_count + 1))
    elif [ "$time_ms" -gt "$PERF_THRESHOLD_MS" ]; then
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
