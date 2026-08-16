#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# MERIT Worker A — ProPublica Scraper Launcher
# Usage:
#   chmod +x run_scraper.sh
#   ./run_scraper.sh                # Interactive run
#   nohup ./run_scraper.sh &        # Background / overnight
#   nohup ./run_scraper.sh full &   # Full 50-state + all terms run
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Paths ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_DIR/data/logs"
RUN_LOG="$LOG_DIR/scraper_run_$(date +%Y%m%d_%H%M%S).log"
PID_FILE="$LOG_DIR/scraper.pid"

# ── Defaults ──
LIMIT="${LIMIT:-5000}"
RESUME_FLAG="${RESUME_FLAG:---resume}"
SEARCH_PAGES="${SEARCH_PAGES:-5}"

# ── Ensure directories ──
mkdir -p "$LOG_DIR"

# ── Usage ──
usage() {
  cat <<EOF
Usage: $(basename "$0") [MODE] [OPTIONS]

MODES:
  quick      Fast run, small limit (good for testing)
  full       Comprehensive: all states + all search terms
  resume     Resume from existing data only
  force      Force re-download everything
  state      State-filtered run (set STATE env var, e.g., STATE=CA)

OPTIONS (environment variables):
  LIMIT=N          Max organizations to process (default: 5000)
  STATE=ST         Comma-separated state filter
  SEARCH_TERMS=t   Override search terms
  SEARCH_PAGES=N   Pages per search term (default: 5)
  NO_RESUME=1      Disable resume flag

EXAMPLES:
  # Quick test run
  ./run_scraper.sh quick

  # Full overnight run
  nohup ./run_scraper.sh full > /dev/null 2>&1 &

  # California only
  STATE=CA ./run_scraper.sh state

  # Custom limit with no resume
  LIMIT=1000 NO_RESUME=1 ./run_scraper.sh quick
EOF
  exit 0
}

# ── Mode detection ──
MODE="${1:-default}"
shift 2>/dev/null || true

case "$MODE" in
  -h|--help|help)
    usage
    ;;
  quick)
    LIMIT="${LIMIT:-500}"
    SEARCH_PAGES="${SEARCH_PAGES:-2}"
    ;;
  full)
    LIMIT="${LIMIT:-50000}"
    SEARCH_PAGES="${SEARCH_PAGES:-10}"
    ;;
  resume)
    LIMIT="${LIMIT:-10000}"
    RESUME_FLAG="--resume"
    ;;
  force)
    LIMIT="${LIMIT:-5000}"
    RESUME_FLAG=""
    EXTRA_ARGS="--force"
    ;;
  state)
    if [[ -z "${STATE:-}" ]]; then
      echo "ERROR: STATE env var required for 'state' mode. Example: STATE=CA"
      exit 1
    fi
    ;;
  *)
    # Default / custom args passed through
    ;;
esac

# ── Build argument list ──
ARGS=(
  --limit "$LIMIT"
  --search-pages "$SEARCH_PAGES"
)

if [[ -z "${NO_RESUME:-}" && -n "$RESUME_FLAG" ]]; then
  ARGS+=("$RESUME_FLAG")
fi

if [[ -n "${STATE:-}" ]]; then
  ARGS+=(--state-filter "$STATE")
fi

if [[ -n "${SEARCH_TERMS:-}" ]]; then
  ARGS+=(--search-terms "$SEARCH_TERMS")
fi

if [[ -n "${EXTRA_ARGS:-}" ]]; then
  # shellcheck disable=SC2206
  ARGS+=($EXTRA_ARGS)
fi

# ── Launch ──
echo "═══════════════════════════════════════════════════════════════"
echo "  MERIT Worker A — ProPublica Scraper"
echo "  Started: $(date -Iseconds)"
echo "  Mode:    $MODE"
echo "  Args:    ${ARGS[*]}"
echo "  Log:     $RUN_LOG"
echo "═══════════════════════════════════════════════════════════════"

# Save PID for monitoring
echo $$ > "$PID_FILE"

# Trap cleanup on exit
cleanup() {
  rm -f "$PID_FILE"
  echo ""
  echo "Scraper finished at $(date -Iseconds)"
  echo "Log saved: $RUN_LOG"
}
trap cleanup EXIT

# Run with unbuffered output and tee to log
exec python3 -u "$SCRIPT_DIR/propublica_scraper.py" "${ARGS[@]}" 2>&1 | tee "$RUN_LOG"
