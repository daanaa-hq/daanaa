#!/usr/bin/env bash
# run_gap_recovery_pipeline.sh — close registry gaps from public filings, in order.
#
# Phases run strictly one at a time in a single process. An earlier attempt
# chained them with `until ! pgrep -f <script>` guards, which deadlocked: the
# waiting shell's own command line contains the script name, so pgrep always
# matched itself and the guard never released. Sequential execution in one
# script is both simpler and correct — SQLite serialises writers anyway, so
# there is nothing to gain from overlapping them.
#
# Usage: bash scripts/run_gap_recovery_pipeline.sh

set -uo pipefail

REPO="$HOME/meritgiving"
cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/venv/bin/activate"

LOG="$REPO/logs/gap_recovery_pipeline_$(date +%Y%m%d-%H%M%S).log"
mkdir -p "$REPO/logs"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

coverage() {
  sqlite3 "$REPO/data/merit_registry.db" \
    "SELECT 'websites=' || COUNT(website) ||
            ' missions_990=' || SUM(mission_source='irs_990') ||
            ' revenue=' || COUNT(revenue_3yr_avg)
     FROM registry_enriched;"
}

phase() {
  local name="$1"; shift
  log "── $name ──"
  if "$@" >>"$LOG" 2>&1; then
    log "$name: OK"
  else
    log "$name: FAILED (exit $?) — continuing to next phase"
  fi
  log "coverage: $(coverage)"
}

log "=== gap recovery pipeline start ==="
log "coverage: $(coverage)"

# 1. Organizations' own mission text supersedes our AI guesses.
phase "missions (all years)" python3 scripts/ingest_990_missions.py

# 2. Websites for the remaining filing years (2023 already harvested).
for y in 2022 2021 2020 2019 2018 2017; do
  phase "websites $y" python3 scripts/harvest_990_websites.py --year "$y" --concurrency 50
done

# 3. Search index must be rebuilt: mission text is indexed and it just moved.
phase "fts rebuild" python3 scripts/build_fts_index.py --rebuild

# 4. Vectors were built from the old mission text and now describe text that no
#    longer exists. Refresh them last, once the source of truth has settled.
phase "re-embed" python3 scripts/build_org_embeddings.py \
  --model mxbai-embed-large --dim 1024 --overwrite --vulkan --all-orgs --workers 16

log "=== pipeline complete ==="
log "final coverage: $(coverage)"
