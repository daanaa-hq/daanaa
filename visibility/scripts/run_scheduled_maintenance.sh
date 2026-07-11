#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MODE="${1:-weekly}"
LOG_DIR="$ROOT/logs/visibility"

mkdir -p "$LOG_DIR"
cd "$ROOT"

run_weekly() {
  python3 visibility/scripts/build_weekly_visibility_monitor.py
  python3 visibility/scripts/submit_search_signals.py
  python3 visibility/scripts/build_growth_opportunity_report.py
  python3 visibility/scripts/build_content_targets.py
  python3 visibility/scripts/build_improvement_loop.py
}

case "$MODE" in
  weekly)
    run_weekly
    ;;
  monthly)
    DEPLOY=0 CHECK_LIVE=1 visibility/scripts/run_visibility_pipeline.sh
    run_weekly
    ;;
  *)
    printf 'Usage: %s [weekly|monthly]\n' "$0" >&2
    exit 2
    ;;
esac
