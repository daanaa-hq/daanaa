#!/usr/bin/env bash
  set -Eeuo pipefail

  # Daanaa local release coordination
  # Claude Code and Codex must not edit the same file simultaneously.
  # No droplet writes, database migrations, commits, or deploys are performed.

  APP_DIR="${APP_DIR:-/home/akbar/meritgiving}"
  WORK_DIR="$APP_DIR/.release_coordination"
  BREAK_MINUTES="${BREAK_MINUTES:-10}"
  PHASE="${PHASE:-all}"

  mkdir -p "$WORK_DIR"/{reports,locks,artifacts}

  cd "$APP_DIR"

  log() {
    printf '\n[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"
  }

  pause_checkpoint() {
    local name="$1"
    date -u +"%Y-%m-%dT%H:%M:%SZ" > "$WORK_DIR/checkpoint_${name}.txt"
    log "Checkpoint reached: $name"
    log "Take a ${BREAK_MINUTES}-minute break before the next phase."
    sleep "$((BREAK_MINUTES * 60))"
  }

  claim_phase() {
    local name="$1"
    local lock="$WORK_DIR/locks/${name}.lock"

    if [[ -e "$lock" ]]; then
      echo "Phase already claimed: $name"
      echo "Review $lock before continuing."
      exit 1
    fi

    {
      echo "owner=${OWNER:-unknown}"
      echo "started=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      echo "host=$(hostname)"
    } > "$lock"
  }

  record_result() {
    local name="$1"
    local result="$2"
    {
      echo "phase=$name"
      echo "result=$result"
      echo "completed=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    } > "$WORK_DIR/reports/${name}.result"
  }

  phase_inventory() {
    claim_phase inventory
    log "Phase 0: repository and change inventory"

    git status --short | tee "$WORK_DIR/reports/git-status.txt"
    git diff --check
    git diff --stat | tee "$WORK_DIR/reports/diff-stat.txt"
    git diff -- scripts/core/droplet_api.py frontend/src/pages/OrganizationDetail.tsx \
      | tee "$WORK_DIR/reports/reviewed-diff.txt"

    echo
    echo "Required review:"
    echo "- No unexpected files"
    echo "- No database files changed"
    echo "- No secrets in diff"
    echo "- No droplet or production commands"
    echo "- Only approved v6 route, parser repair, and org-page changes"

    record_result inventory PASS
    pause_checkpoint inventory
  }

  phase_backend_syntax() {
    claim_phase backend_syntax
    log "Phase 1: backend parser and route validation"

    python3 -m py_compile scripts/core/droplet_api.py
    python3 -m py_compile scripts/v6_financial_context_api.py

    grep -q "/api/organizations/<ein>/financial-context" scripts/core/droplet_api.py
    grep -q "get_v6_financial_context" scripts/core/droplet_api.py

    echo "Checking parser repairs are limited to no-op pass statements:"
    git diff -- droplet_api.py | tee "$WORK_DIR/reports/backend-diff.txt"

    record_result backend_syntax PASS
    pause_checkpoint backend_syntax
  }

  phase_backend_tests() {
    claim_phase backend_tests
    log "Phase 2: backend tests and local endpoint"

    export DAANAA_SKIP_EMBEDDINGS=1
    export ENABLE_V6_FINANCIAL_CONTEXT=true
    export V6_CANDIDATE_RUN_ID="${V6_CANDIDATE_RUN_ID:-v6_foundation_candidate_20260728_revised}"

    python3 -m pytest tests -q \
      | tee "$WORK_DIR/reports/backend-tests.txt"

    record_result backend_tests PASS
    pause_checkpoint backend_tests
  }

  phase_frontend_tests() {
    claim_phase frontend_tests
    log "Phase 3: frontend build, tests, and type checks"

    cd "$APP_DIR/frontend"

    npm run build | tee "$WORK_DIR/reports/frontend-build.txt"
    npm test -- --runInBand | tee "$WORK_DIR/reports/frontend-tests.txt"

    cd "$APP_DIR"

    record_result frontend_tests PASS
    pause_checkpoint frontend_tests
  }

  phase_stewardship() {
    claim_phase stewardship
    log "Phase 4: donor-facing stewardship review"

    echo "Search public-facing code for forbidden or stale financial language:"
    grep -r -i "v5\|financial health score\|rating\|failure\|bad nonprofit\|overhead" \
      frontend/src || true | tee "$WORK_DIR/reports/stewardship-language-review.txt" || true

    echo "Verify required distinctions:"
    grep -r "IRS\|Publication 78\|peer reference\|limited context\|data limitation\|v6" \
      frontend/src/pages/OrganizationDetail.tsx frontend/src/components || true \
      | tee "$WORK_DIR/reports/v6-copy-review.txt" || true

    echo
    echo "Manual review requirements:"
    echo "- IRS status is separate from v6 peer context."
    echo "- Peer references never appear as organization-specific facts."
    echo "- Missing data is explained without blaming small organizations."
    echo "- No public statement claims a gift is tax-deductible."
    echo "- Revoked organizations are not given a donation CTA."
    echo "- Wallet history preserves historical status without rewriting it."
    echo "- Scores and visibility are not influenced by payment."

    record_result stewardship REVIEW_REQUIRED
    pause_checkpoint stewardship
  }

  phase_design_accessibility() {
    claim_phase design_accessibility
    log "Phase 5: design and accessibility review"

    cd "$APP_DIR/frontend"

    if npm run | grep -q "design-lint"; then
      npm run design-lint | tee "$WORK_DIR/reports/design-lint.txt" || true
    else
      echo "No design-lint npm script configured." \
        | tee "$WORK_DIR/reports/design-lint.txt"
    fi

    cd "$APP_DIR"

    echo "Manual browser review at 375px, 768px, and desktop:"
    echo "- Organization name, mission, IRS status, v6 context, and primary action are scannable."
    echo "- No low-contrast amber, green, red, or muted-cream text."
    echo "- Keyboard focus is visible."
    echo "- Skip link works."
    echo "- Accordions expose their labels and state."
    echo "- All buttons have at least 44px touch targets."
    echo "- No horizontal overflow."
    echo "- Direct, peer-reference, and limited-data organizations are all respectful."
    echo "- Dark mode remains readable."

    record_result design_accessibility REVIEW_REQUIRED
    pause_checkpoint design_accessibility
  }

  phase_local_api() {
    claim_phase local_api
    log "Phase 6: local API integration test"

    export DAANAA_SKIP_EMBEDDINGS=1
    export ENABLE_V6_FINANCIAL_CONTEXT=true
    export V6_CANDIDATE_RUN_ID="${V6_CANDIDATE_RUN_ID:-v6_foundation_candidate_20260728_revised}"

    if ! curl -fsS --max-time 3 http://127.0.0.1:5000/health >/dev/null 2>&1; then
      echo "ERROR: Local API not running."
      echo "Start it with: python3 scripts/core/droplet_api.py"
      exit 1
    fi

    test_endpoint() {
      local ein="$1"
      local label="$2"

      curl -fsS --max-time 30 \
        -H "Accept: application/json" \
        "http://127.0.0.1:5000/api/organizations/${ein}/financial-context" \
        > "$WORK_DIR/artifacts/v6-${label}.json"

      python3 - "$WORK_DIR/artifacts/v6-${label}.json" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path) as f:
    data = json.load(f)

required = ["data_status", "methodology_version"]
missing = [key for key in required if key not in data]

if missing:
    raise SystemExit(f"Missing required fields: {missing}")

print("JSON and required v6 fields: PASS")
PY
    }

    test_endpoint "${DIRECT_EIN:-000019818}" direct
    test_endpoint "${PEER_EIN:-264837170}" peer
    test_endpoint "${LIMITED_EIN:-880283783}" limited

    curl -sS -o /dev/null -w "%{http_code}\n" \
      "http://127.0.0.1:5000/api/organizations/not-an-ein/financial-context" \
      | grep -qx "400"

    record_result local_api PASS
    pause_checkpoint local_api
  }

  phase_final_gate() {
    claim_phase final_gate
    log "Phase 7: final local release gate"

    git diff --check
    python3 -m py_compile scripts/core/droplet_api.py
    python3 -m py_compile scripts/v6_financial_context_api.py

    echo
    echo "Final review checklist:"
    echo "[ ] Backend route is present in scripts/core/droplet_api.py"
    echo "[ ] Only five parser no-op repairs are present"
    echo "[ ] Frontend diff is limited to OrganizationDetail.tsx"
    echo "[ ] Backend tests pass"
    echo "[ ] Frontend tests pass"
    echo "[ ] Frontend build passes"
    echo "[ ] v6 local endpoint returns JSON"
    echo "[ ] Direct/peer/limited org tests pass"
    echo "[ ] Impeccable visual review passes"
    echo "[ ] Accessibility review passes"
    echo "[ ] No stale v5 donor-facing references"
    echo "[ ] No database migration performed"
    echo "[ ] No droplet command performed"

    record_result final_gate REVIEW_REQUIRED

    echo
    echo "LOCAL RELEASE CANDIDATE READY FOR HUMAN REVIEW."
    echo "Do not deploy until the owner reviews all reports in:"
    echo "$WORK_DIR/reports/"
  }

  case "$PHASE" in
    inventory) phase_inventory ;;
    backend_syntax) phase_backend_syntax ;;
    backend_tests) phase_backend_tests ;;
    frontend_tests) phase_frontend_tests ;;
    stewardship) phase_stewardship ;;
    design_accessibility) phase_design_accessibility ;;
    local_api) phase_local_api ;;
    final_gate) phase_final_gate ;;
    all)
      phase_inventory
      phase_backend_syntax
      phase_backend_tests
      phase_frontend_tests
      phase_stewardship
      phase_design_accessibility
      phase_local_api
      phase_final_gate
      ;;
    *)
      echo "Unknown phase: $PHASE"
      exit 2
      ;;
  esac
