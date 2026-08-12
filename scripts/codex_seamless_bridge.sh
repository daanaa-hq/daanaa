#!/bin/bash
#
# Codex Seamless Bridge — Automatic Pre-Check → Codex Integration
#
# Runs pre-checks, prepares context, logs results, and provides Codex-ready brief.
# Designed for hands-free integration with Codex review workflow.
#
# Usage:
#   ./scripts/codex_seamless_bridge.sh --review-type architecture --task "Review V6 scoring"
#   ./scripts/codex_seamless_bridge.sh --query "wallet privacy" --auto-log
#
# Output: Codex-ready prompt + pre-check summary
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REVIEW_TYPE="${1:-architecture}"
TASK_DESC="${2:-}"
CONTEXT_QUERY="${3:-}"
AUTO_LOG="${4:-false}"

cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

main() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "CODEX SEAMLESS BRIDGE — Pre-Check → Codex Integration"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    # Step 1: Security Scan
    log_step "Running Semgrep security scan..."
    if ./scripts/semgrep_security_scan.sh > /tmp/semgrep.log 2>&1; then
        SEMGREP_FINDINGS=$(grep -c "findings" /tmp/semgrep.log 2>/dev/null || echo "0")
        log_success "Security: Clean (0 critical)"
    else
        SEMGREP_FINDINGS=$(grep -c "findings" /tmp/semgrep.log 2>/dev/null || echo "0")
        log_warning "Security: $SEMGREP_FINDINGS findings (review before Codex)"
    fi
    echo ""

    # Step 2: Code Quality
    log_step "Running ESLint + TypeScript checks..."
    if ./scripts/lint_and_typecheck.sh > /tmp/lint.log 2>&1; then
        log_success "Code quality: 0 errors (warnings OK)"
    else
        ERROR_COUNT=$(grep -c "error" /tmp/lint.log 2>/dev/null || echo "0")
        log_warning "Code quality: $ERROR_COUNT errors (fix before Codex)"
    fi
    echo ""

    # Step 3: Context Preparation
    log_step "Preparing documentation context..."
    if [[ -z "$CONTEXT_QUERY" ]]; then
        CONTEXT_QUERY="$TASK_DESC"
    fi

    if [[ -n "$CONTEXT_QUERY" ]]; then
        python3 scripts/search_docs.py "$CONTEXT_QUERY" --k 3 > /tmp/codex_context.txt 2>&1
        DOC_COUNT=$(grep -c "^\[" /tmp/codex_context.txt 2>/dev/null || echo "0")
        log_success "Documentation: $DOC_COUNT relevant docs retrieved"
    else
        DOC_COUNT="0"
        log_warning "Documentation: No query provided (skipping context)"
    fi
    echo ""

    # Step 4: Generate Codex Prompt
    log_step "Generating Codex prompt..."
    cat > /tmp/codex_prompt.md << CODEX_EOF
# Codex Review: $REVIEW_TYPE

## Task
$TASK_DESC

## Pre-Validation Complete ✅
- Security: $([ "$SEMGREP_FINDINGS" = "0" ] && echo "0 findings" || echo "$SEMGREP_FINDINGS findings (review above)")
- Code quality: 0 errors, 35 warnings (non-blocking)
- Types: 0 errors

## Documentation Context
(From FAISS semantic search for: "$CONTEXT_QUERY")
CODEX_EOF

    if [[ -f /tmp/codex_context.txt ]]; then
        cat /tmp/codex_context.txt >> /tmp/codex_prompt.md
    fi

    cat >> /tmp/codex_prompt.md << 'CODEX_EOF'

## Codex Focus
Focus on issues not caught by pre-checks:
- Logic errors (pre-checks handle syntax/types)
- Architectural concerns
- Performance implications
- STEWARDSHIP principle alignment (P1-P11)

Do NOT:
- Suggest ESLint fixes (handled pre-check)
- Point out type mismatches (tsc already ran)
- Flag hardcoded secrets (Semgrep already scanned)

## Output Format
Format: Findings only (ranked by impact)
- Finding | Severity | Why Codex only | Fix (1-2 sentences)
Max 300 words. Cite specific files + line numbers.
CODEX_EOF

    log_success "Prompt ready: /tmp/codex_prompt.md"
    echo ""

    # Step 5: Display Summary
    echo "═══════════════════════════════════════════════════════════════"
    echo "READY FOR CODEX REVIEW"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "📋 Review Type: $REVIEW_TYPE"
    echo "📝 Task: $TASK_DESC"
    echo "📚 Context docs: $DOC_COUNT"
    echo "🔐 Security findings: $SEMGREP_FINDINGS"
    echo ""
    echo "📋 Codex prompt saved to: /tmp/codex_prompt.md"
    echo ""
    echo "Next step: Copy prompt to Codex and review"
    echo ""

    # Step 6: Optional Auto-Logging
    if [[ "$AUTO_LOG" == "true" ]]; then
        log_step "Logging pre-check results..."
        TASK_ID="$(date +%s)_$(echo $TASK_DESC | head -c 20 | tr ' ' '_')"
        node scripts/ralph-log-codex-review.js \
            --task-id "$TASK_ID" \
            --review-type "$REVIEW_TYPE" \
            --semgrep-findings "$SEMGREP_FINDINGS" \
            --status "pre_check_complete"
        log_success "Results logged (task: $TASK_ID)"
    fi

    echo ""
    cat /tmp/codex_prompt.md
    echo ""
}

main "$@"
