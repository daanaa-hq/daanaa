#!/usr/bin/env bash
set -Eeuo pipefail

# Server-first release gate.
#
# This script validates the server/staging implementation first. It does not
# deploy to a droplet unless DEPLOY_DROPLET=true and an explicit deployment
# script is supplied. It does not invent or silently skip reference, language,
# page-consolidation, or Impeccable work: each is a required named gate.

APP_DIR="${APP_DIR:-/opt/daanaa}"
FRONTEND_DIR="${FRONTEND_DIR:-$APP_DIR/frontend}"
DB_PATH="${DB_PATH:-$APP_DIR/data/merit_registry.db}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
RUN_ID="${RUN_ID:-}"
PHASE3_ROOT="${PHASE3_ROOT:-$APP_DIR/.deploy_scratch/clean_precompute}"
PHASE3_EXPECTED_COUNT="${PHASE3_EXPECTED_COUNT:-}"
IMPECCABLE_APPROVAL_FILE="${IMPECCABLE_APPROVAL_FILE:-$APP_DIR/reports/impeccable/FINAL_APPROVAL.md}"
DEPLOY_DROPLET="${DEPLOY_DROPLET:-false}"
ACTIVATE_V6="${ACTIVATE_V6:-false}"
DROPLET_DEPLOY_SCRIPT="${DROPLET_DEPLOY_SCRIPT:-}"

# These must be supplied by the team because the repository has no single
# canonical command for these workstreams.
REFERENCE_GATE_CMD="${REFERENCE_GATE_CMD:-}"
LANGUAGE_GATE_CMD="${LANGUAGE_GATE_CMD:-}"
PAGE_CONSOLIDATION_GATE_CMD="${PAGE_CONSOLIDATION_GATE_CMD:-}"
IMPECCABLE_AUDIT_CMD="${IMPECCABLE_AUDIT_CMD:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

die() { echo "FAIL: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "missing command: $1"; }
run_gate() { local name="$1"; local command_text="$2"; [[ -n "$command_text" ]] || die "$name command was not supplied"; echo "== $name =="; bash -lc "$command_text"; }

[[ "$DEPLOY_DROPLET" == "true" || "$DEPLOY_DROPLET" == "false" ]] || die "DEPLOY_DROPLET must be true or false"
[[ "$ACTIVATE_V6" == "true" || "$ACTIVATE_V6" == "false" ]] || die "ACTIVATE_V6 must be true or false"
[[ -f "$SCRIPT_DIR/deploy_v6_validate.sh" ]] || die "missing deploy_v6_validate.sh"
[[ -f "$SCRIPT_DIR/phase3_artifact_tools.py" ]] || die "missing phase3_artifact_tools.py"
[[ -d "$FRONTEND_DIR" ]] || die "missing frontend directory: $FRONTEND_DIR"

need bash
need python3
need git
need npm

cd "$APP_DIR"
echo "== Server-first v6 release gate =="
echo "App: $APP_DIR"
echo "Frontend: $FRONTEND_DIR"
echo "No droplet deployment will occur unless DEPLOY_DROPLET=true."

echo "== Source integrity =="
git diff --check
git status --short

echo "== v6 + IRS + Phase 3 validation =="
APP_DIR="$APP_DIR" \
DB_PATH="$DB_PATH" \
BASE_URL="$BASE_URL" \
RUN_ID="$RUN_ID" \
PHASE3_ROOT="$PHASE3_ROOT" \
PHASE3_EXPECTED_COUNT="$PHASE3_EXPECTED_COUNT" \
REQUIRE_PHASE3_ARTIFACTS=true \
REQUIRE_FULL_ASSIGNMENTS=true \
ACTIVATE="$ACTIVATE_V6" \
bash "$SCRIPT_DIR/deploy_v6_validate.sh"

run_gate "References and source citations" "$REFERENCE_GATE_CMD"
run_gate "Language and stewardship copy" "$LANGUAGE_GATE_CMD"
run_gate "Page and route consolidation" "$PAGE_CONSOLIDATION_GATE_CMD"

echo "== Frontend automated checks =="
cd "$FRONTEND_DIR"
npm run lint
npm run design-lint
npm test -- --runInBand
npm run build
cd "$APP_DIR"

echo "== Impeccable design audit =="
run_gate "Impeccable audit and polish" "$IMPECCABLE_AUDIT_CMD"
[[ -s "$IMPECCABLE_APPROVAL_FILE" ]] || die "missing Impeccable approval report: $IMPECCABLE_APPROVAL_FILE"
rg -q -i 'PASS|approved|no blocking' "$IMPECCABLE_APPROVAL_FILE" || die "Impeccable report does not contain an approval marker"
echo "Impeccable approval report: $IMPECCABLE_APPROVAL_FILE"

echo "== Final server smoke test =="
curl -fsS --max-time 15 "$BASE_URL/health" >/dev/null
curl -fsS --max-time 15 "$BASE_URL/api/organizations/000000000/financial-context" | head -c 500 || true
echo

if [[ "$DEPLOY_DROPLET" == "true" ]]; then
  [[ -n "$DROPLET_DEPLOY_SCRIPT" ]] || die "DROPLET_DEPLOY_SCRIPT is required when DEPLOY_DROPLET=true"
  [[ -f "$DROPLET_DEPLOY_SCRIPT" ]] || die "droplet deployment script not found: $DROPLET_DEPLOY_SCRIPT"
  echo "== Droplet deployment =="
  echo "All server-first gates passed. Executing: $DROPLET_DEPLOY_SCRIPT"
  bash "$DROPLET_DEPLOY_SCRIPT"
else
  echo "== Droplet deployment skipped =="
  echo "All server-first gates passed. Set DEPLOY_DROPLET=true only after QA/founder approval."
fi

echo "Release gate complete."
