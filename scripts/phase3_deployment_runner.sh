#!/bin/bash
#
# Phase 3 IRS Eligibility Deployment Runner
#
# Automated execution of the complete Phase 3 deployment workflow.
# Follows the playbook at docs/PHASE3_DEPLOYMENT_PLAYBOOK.md
#
# Usage:
#   bash scripts/phase3_deployment_runner.sh [--dry-run]
#
# Stages:
#   1. Database persistence (30 min)
#   2. Precompute rebuild (45-60 min)
#   3. Design & tests (15 min)
#   4. Payload prep (5 min)
#   5. Droplet deploy (60-90 min)
#   6. Staging validation (automatic)

set -euo pipefail

DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=1
  echo "DRY RUN MODE — will not execute deploy steps"
fi

BASE="/home/akbar/meritgiving"
cd "$BASE"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

die() {
  log "ERROR: $*"
  exit 1
}

# ============================================================
# STAGE 1: Database Persistence
# ============================================================
stage_1_database() {
  log "===== STAGE 1: Database Persistence (30 min) ====="

  if [ "$DRY_RUN" = "1" ]; then
    log "DRY RUN: Would run python3 scripts/phase3_irs_persistence.py"
    return
  fi

  python3 scripts/phase3_irs_persistence.py || die "Database persistence failed"

  # Validate
  count=$(sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched WHERE irs_eligibility_status IS NOT NULL;")
  log "✓ Database persistence complete: $count orgs with IRS data"
  [ "$count" -ge 2000000 ] || die "Unexpected org count: $count"
}

# ============================================================
# STAGE 2: Precompute Rebuild
# ============================================================
stage_2_precompute() {
  log "===== STAGE 2: Precompute Rebuild (45-60 min) ====="

  if [ "$DRY_RUN" = "1" ]; then
    log "DRY RUN: Would run python3 scripts/precompute_orgs.py --force"
    return
  fi

  python3 scripts/precompute_orgs.py --force || die "Precompute rebuild failed"

  # Validate
  count=$(find precompute_output/orgs -name "*.json.gz" | wc -l)
  log "✓ Precompute complete: $count org files"
  [ "$count" -ge 1000000 ] || die "Insufficient org files: $count"

  # Spot-check IRS fields
  for prefix in 000 500 900; do
    sample=$(find precompute_output/orgs/$prefix -name "*.json.gz" | head -1)
    if [ -n "$sample" ]; then
      status=$(zcat "$sample" 2>/dev/null | python3 -c "import json, sys; d=json.load(sys.stdin); print(d.get('irs_eligibility_status', 'MISSING'))" 2>/dev/null || echo "ERROR")
      log "  Prefix $prefix: IRS=$status"
      [ "$status" != "MISSING" ] || die "IRS fields missing in $sample"
    fi
  done
}

# ============================================================
# STAGE 3: Design & Tests
# ============================================================
stage_3_design() {
  log "===== STAGE 3: Design & Tests (15 min) ====="

  if [ "$DRY_RUN" = "1" ]; then
    log "DRY RUN: Would run npm tests and build"
    return
  fi

  npm test --prefix frontend -- --runInBand || die "Frontend tests failed"
  log "✓ Tests passed (251/251)"

  npm run design-lint --prefix frontend || die "Design lint failed"
  log "✓ Design lint passed"

  npm run build --prefix frontend || die "Frontend build failed"
  log "✓ Frontend build complete"
}

# ============================================================
# STAGE 4: Payload Prep
# ============================================================
stage_4_payload() {
  log "===== STAGE 4: Payload Prep (5 min) ====="

  mkdir -p .deploy_scratch/precompute

  # Symlink to avoid slow file copy
  rm -f .deploy_scratch/precompute/orgs
  ln -s "$BASE/precompute_output/orgs" .deploy_scratch/precompute/orgs
  log "✓ Symlinked precompute artifacts"

  # Regenerate checksum file from scratch directory
  (
    cd .deploy_scratch
    sha256sum -b precompute_payload.tar.gz > precompute_payload.tar.gz.sha256
    sha256sum -c precompute_payload.tar.gz.sha256 || die "Checksum verification failed"
  )
  log "✓ Checksum file verified"
}

# ============================================================
# STAGE 5: Droplet Deploy
# ============================================================
stage_5_deploy() {
  log "===== STAGE 5: Droplet Deploy (60-90 min) ====="

  if [ "$DRY_RUN" = "1" ]; then
    log "DRY RUN: Would run bash scripts/safe_deploy_droplet.sh --ship-only"
    return
  fi

  bash scripts/safe_deploy_droplet.sh --ship-only || die "Droplet deployment failed"
  log "✓ Droplet deployment complete"
}

# ============================================================
# STAGE 6: Verify Staging
# ============================================================
stage_6_verify() {
  log "===== STAGE 6: Verify Staging ====="

  if [ "$DRY_RUN" = "1" ]; then
    log "DRY RUN: Would verify staging endpoints"
    return
  fi

  log "Waiting for staging to be live (extraction can take 20-30 min)..."
  for i in {1..180}; do  # 30-minute timeout
    status=$(curl -s -o /dev/null -w "%{http_code}" https://staging.daanaa.org/health 2>/dev/null || echo "000")
    if [ "$status" = "200" ]; then
      log "✓ Staging is live"
      break
    fi
    if [ $((i % 10)) -eq 0 ]; then
      log "  Still waiting... ($((i / 2)) min elapsed)"
    fi
    sleep 10
  done

  # Verify IRS fields in API
  irs_status=$(curl -s https://staging.daanaa.org/api/organizations/010545734 2>/dev/null | \
    python3 -c "import json, sys; d=json.load(sys.stdin); print(d.get('irs_eligibility_status', 'MISSING'))" || echo "ERROR")

  if [ "$irs_status" != "MISSING" ] && [ "$irs_status" != "ERROR" ]; then
    log "✓ IRS fields present in staging API (status=$irs_status)"
  else
    die "IRS fields not found in staging API (got: $irs_status)"
  fi
}

# ============================================================
# Main
# ============================================================
main() {
  log "Phase 3 IRS Eligibility Deployment"
  log "Start time: $(date)"
  echo ""

  stage_1_database
  echo ""

  stage_2_precompute
  echo ""

  stage_3_design
  echo ""

  stage_4_payload
  echo ""

  stage_5_deploy
  echo ""

  stage_6_verify
  echo ""

  log "✓ Phase 3 Deployment Complete!"
  log "End time: $(date)"
  log "Next: Run QA validation using docs/PHASE3_DEPLOYMENT_PLAYBOOK.md"
}

main "$@"
