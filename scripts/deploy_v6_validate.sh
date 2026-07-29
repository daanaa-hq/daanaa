#!/usr/bin/env bash
set -Eeuo pipefail

# Validation-first v6 rollout gate. No activation, service restart, archive
# transfer, or production deployment occurs unless explicitly requested.

APP_DIR="${APP_DIR:-/opt/daanaa}"
DB_PATH="${DB_PATH:-$APP_DIR/merit_registry.db}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
RUN_ID="${RUN_ID:-}"
ACTIVATE="${ACTIVATE:-false}"
REQUIRE_FULL_ASSIGNMENTS="${REQUIRE_FULL_ASSIGNMENTS:-true}"
REQUIRE_PHASE3_ARTIFACTS="${REQUIRE_PHASE3_ARTIFACTS:-true}"
PHASE3_ROOT="${PHASE3_ROOT:-$APP_DIR/.deploy_scratch/clean_precompute}"
PHASE3_EXPECTED_COUNT="${PHASE3_EXPECTED_COUNT:-}"
PACKAGE_PHASE3="${PACKAGE_PHASE3:-false}"
PHASE3_SHARDS="${PHASE3_SHARDS:-32}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

die() { echo "FAIL: $*" >&2; exit 1; }
require_cmd() { command -v "$1" >/dev/null 2>&1 || die "missing command: $1"; }

[[ "$ACTIVATE" == "true" || "$ACTIVATE" == "false" ]] || die "ACTIVATE must be true or false"
[[ "$REQUIRE_FULL_ASSIGNMENTS" == "true" || "$REQUIRE_FULL_ASSIGNMENTS" == "false" ]] || die "REQUIRE_FULL_ASSIGNMENTS must be true or false"
[[ "$REQUIRE_PHASE3_ARTIFACTS" == "true" || "$REQUIRE_PHASE3_ARTIFACTS" == "false" ]] || die "REQUIRE_PHASE3_ARTIFACTS must be true or false"
[[ "$PACKAGE_PHASE3" == "true" || "$PACKAGE_PHASE3" == "false" ]] || die "PACKAGE_PHASE3 must be true or false"
[[ "$RUN_ID" =~ ^[A-Za-z0-9_.:-]*$ ]] || die "RUN_ID contains unsafe characters"

cd "$APP_DIR"
require_cmd sqlite3
require_cmd python3
require_cmd curl

[[ -f "$DB_PATH" ]] || die "missing database: $DB_PATH"
[[ -f "$SCRIPT_DIR/v6_validate_run.py" ]] || die "missing v6 validator"
[[ -f "$SCRIPT_DIR/v6_revocation_verify_and_block.py" ]] || die "missing revocation validator"
[[ -f "$SCRIPT_DIR/phase3_artifact_tools.py" ]] || die "missing Phase 3 artifact validator"

echo "== Daanaa v6 + Phase 3 rollout validation =="
echo "Application: $APP_DIR"
echo "Database: $DB_PATH"

BACKUP_DIR="$APP_DIR/data/backups/v6"
mkdir -p "$BACKUP_DIR"
BACKUP_PATH="$BACKUP_DIR/merit_registry-pre-v6-$(date -u +%Y%m%dT%H%M%SZ).db"

echo "Creating and verifying database backup..."
sqlite3 "$DB_PATH" ".backup '$BACKUP_PATH'"
[[ -s "$BACKUP_PATH" ]] || die "backup was not created: $BACKUP_PATH"
[[ "$(sqlite3 "$BACKUP_PATH" 'PRAGMA integrity_check;')" == "ok" ]] || die "backup integrity check failed"
echo "Backup verified: $BACKUP_PATH"

echo "Checking required v6 tables..."
for table in registry_enriched v6_scoring_runs v6_peer_context_assignments; do
  count="$(sqlite3 -noheader "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='$table';")"
  [[ "$count" == "1" ]] || die "missing required table: $table"
done

if [[ -z "$RUN_ID" ]]; then
  RUN_ID="$(sqlite3 -noheader "$DB_PATH" "
    SELECT run_id FROM v6_scoring_runs
    WHERE status IN ('candidate','active')
    ORDER BY started_at DESC LIMIT 1;
  ")"
fi
[[ -n "$RUN_ID" ]] || die "no candidate or active v6 run found"

RUN_STATUS="$(sqlite3 -noheader "$DB_PATH" "SELECT status FROM v6_scoring_runs WHERE run_id='$RUN_ID';")"
[[ "$RUN_STATUS" == "candidate" || "$RUN_STATUS" == "active" ]] || die "run must be candidate or active: $RUN_ID"
echo "Run: $RUN_ID"
echo "Status: $RUN_STATUS"

if [[ "$RUN_STATUS" == "candidate" ]]; then
  python3 "$SCRIPT_DIR/v6_validate_run.py" "$RUN_ID" "$DB_PATH"
fi
python3 "$SCRIPT_DIR/v6_revocation_verify_and_block.py" "$RUN_ID" "$DB_PATH"

if [[ "$REQUIRE_PHASE3_ARTIFACTS" == "true" ]]; then
  [[ -d "$PHASE3_ROOT" ]] || die "missing clean Phase 3 artifact root: $PHASE3_ROOT"
  [[ -n "$PHASE3_EXPECTED_COUNT" ]] || die "set PHASE3_EXPECTED_COUNT after confirming the clean rebuild count"
  python3 "$SCRIPT_DIR/phase3_artifact_tools.py" validate-org-layout \
    --root "$PHASE3_ROOT" --expected-count "$PHASE3_EXPECTED_COUNT"
  python3 "$SCRIPT_DIR/phase3_artifact_tools.py" inventory \
    --root "$PHASE3_ROOT" --output "$PHASE3_ROOT.manifest.json"
  if [[ "$PACKAGE_PHASE3" == "true" ]]; then
    python3 "$SCRIPT_DIR/phase3_artifact_tools.py" package-org-shards \
      --root "$PHASE3_ROOT" \
      --output-dir "$APP_DIR/.deploy_scratch/precompute_shards" \
      --shards "$PHASE3_SHARDS"
  fi
fi

ACTIVE_COUNT="$(sqlite3 -noheader "$DB_PATH" "
  SELECT COUNT(*) FROM registry_enriched
  WHERE org_status='active' AND COALESCE(irs_revoked,0)=0;
")"
ASSIGNED_COUNT="$(sqlite3 -noheader "$DB_PATH" "
  SELECT COUNT(DISTINCT ein) FROM v6_peer_context_assignments WHERE run_id='$RUN_ID';
")"
[[ "$ACTIVE_COUNT" =~ ^[0-9]+$ && "$ASSIGNED_COUNT" =~ ^[0-9]+$ ]] || die "invalid assignment counts"
(( ASSIGNED_COUNT <= ACTIVE_COUNT )) || die "assignments exceed active organization count"
MISSING_COUNT=$((ACTIVE_COUNT - ASSIGNED_COUNT))

echo "Active organizations: $ACTIVE_COUNT"
echo "Organizations assigned in v6: $ASSIGNED_COUNT"
echo "Unassigned organizations: $MISSING_COUNT"
if [[ "$REQUIRE_FULL_ASSIGNMENTS" == "true" && "$MISSING_COUNT" -gt 0 ]]; then
  die "v6 does not have full assignment coverage"
fi

echo "Tier distribution:"
sqlite3 -header -column "$DB_PATH" "
  SELECT selected_tier, COUNT(*) AS organizations
  FROM v6_peer_context_assignments
  WHERE run_id='$RUN_ID'
  GROUP BY selected_tier ORDER BY selected_tier;
"

echo "Peer-group count:"
sqlite3 "$DB_PATH" "
  SELECT COUNT(DISTINCT peer_group_key)
  FROM v6_peer_context_assignments
  WHERE run_id='$RUN_ID' AND peer_group_key IS NOT NULL;
"

echo "API smoke test (existing service only):"
curl -fsS --max-time 15 "$BASE_URL/api/organizations/000000000/financial-context" | head -c 500 || true
echo

if [[ "$ACTIVATE" == "true" ]]; then
  [[ "$RUN_STATUS" == "candidate" ]] || die "ACTIVATE=true requires a candidate run"
  echo "Activating approved v6 run..."
  sqlite3 "$DB_PATH" "
    BEGIN IMMEDIATE;
    UPDATE v6_scoring_runs SET status='archived'
      WHERE status='active' AND run_id <> '$RUN_ID';
    UPDATE v6_scoring_runs SET status='active' WHERE run_id='$RUN_ID';
    COMMIT;
  "
  [[ "$(sqlite3 -noheader "$DB_PATH" "SELECT status FROM v6_scoring_runs WHERE run_id='$RUN_ID';")" == "active" ]] || die "activation verification failed"
  echo "v6 run activated: $RUN_ID"
else
  echo "Validation complete. No database activation performed."
fi

echo "API environment values for the service configuration:"
echo "ENABLE_V6_FINANCIAL_CONTEXT=true"
echo "V6_CANDIDATE_RUN_ID=$RUN_ID"
echo "Note: exporting variables in this shell does not reconfigure an already-running service."
echo "Next: QA review, methodology/research checks, direct/missing-financial-data checks, and design audit."
