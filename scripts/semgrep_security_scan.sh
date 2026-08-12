#!/bin/bash
#
# Semgrep Security Scan — Daanaa Privacy & Security Automated Checks
#
# Run BEFORE code review: finds common patterns that violate privacy or security.
# Designed to reduce Codex security review by 50% (eliminates known-good patterns).
#
# Usage:
#   ./scripts/semgrep_security_scan.sh [--format json|text|sarif] [paths...]
#
# Default: scan frontend/src, scripts/daanaa_api.py, tests/ and output text
# Exit code: 0 if no findings, 1 if findings found, 2 if scan failed
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="/tmp/semgrep_scan_$(date +%s).log"
FORMAT="${1:-text}"
PATHS=("${@:2}")

if [[ ${#PATHS[@]} -eq 0 ]]; then
    PATHS=(
        "frontend/src"
        "scripts/daanaa_api.py"
        "tests/"
    )
fi

main() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Semgrep security scan..."
    echo "  Paths: ${PATHS[*]}"
    echo "  Format: $FORMAT"
    echo "  Log: $LOG_FILE"
    echo ""

    # Activate venv if available
    if [[ -f "$SCRIPT_DIR/venv/bin/activate" ]]; then
        source "$SCRIPT_DIR/venv/bin/activate"
    fi

    # Verify semgrep is installed
    if ! command -v semgrep &> /dev/null; then
        echo "ERROR: semgrep not found. Install with: pip install semgrep"
        exit 2
    fi

    echo "Semgrep version: $(semgrep --version)"
    echo ""

    # Run scan
    cd "$SCRIPT_DIR"
    local exit_code=0

    if [[ "$FORMAT" == "json" ]]; then
        semgrep --config .semgrep.yaml "${PATHS[@]}" --json > "$LOG_FILE" 2>&1 || exit_code=$?
        cat "$LOG_FILE" | python3 -m json.tool 2>/dev/null || cat "$LOG_FILE"
    else
        semgrep --config .semgrep.yaml "${PATHS[@]}" --text 2>&1 | tee "$LOG_FILE" || exit_code=$?
    fi

    echo ""
    echo "Scan complete. Log: $LOG_FILE"

    if [[ $exit_code -eq 0 ]]; then
        echo "✅ No security findings."
    else
        echo "⚠️  Findings detected. Review log for details."
    fi

    return $exit_code
}

main "$@"
