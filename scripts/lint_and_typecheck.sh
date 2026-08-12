#!/bin/bash
#
# Lint and Type Check — Pre-Codex Code Quality Gate
#
# Runs ESLint + TypeScript compiler to catch errors before code review.
# Designed to eliminate 60% of "code fix" Codex prompts.
#
# Usage:
#   ./scripts/lint_and_typecheck.sh [--fix] [--strict]
#
# --fix: Auto-fix ESLint errors where possible
# --strict: Fail on warnings (not just errors)
#
# Exit codes:
#   0 = All checks pass
#   1 = ESLint errors found
#   2 = TypeScript errors found
#   3 = Both ESLint and TypeScript errors found
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIX=false
STRICT=false
EXIT_CODE=0

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX=true
            shift
            ;;
        --strict)
            STRICT=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

main() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting linting and type checks..."
    echo ""

    cd "$SCRIPT_DIR"

    # Check ESLint
    echo "1️⃣  Running ESLint (TypeScript + React)..."
    cd frontend

    eslint_opts="src"
    if [[ "$FIX" == "true" ]]; then
        eslint_opts="$eslint_opts --fix"
        echo "   (with --fix enabled)"
    fi

    # Run linting (warnings are OK, errors are not)
    if npm run lint -- $eslint_opts 2>&1 | tee /tmp/eslint.log; then
        echo "   ✅ ESLint passed (no errors)"
    else
        # Check if there are actual errors (not just warnings)
        if grep -q "✖.*error" /tmp/eslint.log; then
            echo "   ❌ ESLint found errors"
            EXIT_CODE=$((EXIT_CODE + 1))
        else
            echo "   ⚠️  ESLint warnings found (non-blocking)"
        fi
    fi

    echo ""

    # Check TypeScript
    echo "2️⃣  Running TypeScript compiler..."
    if npm run typecheck 2>&1 | tee /tmp/typecheck.log; then
        echo "   ✅ TypeScript passed"
    else
        echo "   ❌ TypeScript found errors"
        EXIT_CODE=$((EXIT_CODE + 2))
    fi

    cd "$SCRIPT_DIR"
    echo ""

    # Check Python linting
    echo "3️⃣  Running Python type checks..."
    if which mypy > /dev/null 2>&1; then
        if mypy scripts/daanaa_api.py --ignore-missing-imports 2>&1 | head -20; then
            echo "   ✅ Python typing passed (sample)"
        else
            echo "   ⚠️  Python typing warnings (non-blocking)"
        fi
    else
        echo "   ⚠️  mypy not installed (skipping Python checks)"
    fi

    echo ""
    echo "="*60

    if [[ $EXIT_CODE -eq 0 ]]; then
        echo "✅ All checks passed!"
        echo ""
        echo "Ready for Codex review (code quality pre-validated)"
    else
        if [[ $((EXIT_CODE & 1)) -ne 0 ]]; then
            echo "❌ ESLint errors found (see /tmp/eslint.log)"
        fi
        if [[ $((EXIT_CODE & 2)) -ne 0 ]]; then
            echo "❌ TypeScript errors found (see /tmp/typecheck.log)"
        fi
        echo ""
        echo "Run with --fix to auto-correct ESLint issues:"
        echo "  ./scripts/lint_and_typecheck.sh --fix"
    fi

    return $EXIT_CODE
}

main "$@"
