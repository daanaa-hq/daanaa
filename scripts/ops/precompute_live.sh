#!/bin/bash
# precompute_live.sh — Run the precompute stages directly against the LIVE DB.
#
# Why this exists (2026-08-08): safe_deploy_droplet.sh Stage 1 takes a SQLite
# .backup of merit_registry.db while Stage 0 *requires* the local API stay up.
# Those two requirements are incompatible: SQLite's online backup restarts from
# page 1 whenever a writer touches the source, and the gunicorn workers hold the
# DB open read-write. Observed 2026-08-08: 505GB read / 441GB written for a 23GB
# source (~20 full passes, ~20GB/min) with the snapshot frozen at 18.2GB. It
# would never have completed.
#
# The precompute stages only READ, and readers do not trigger backup restarts,
# so we skip the snapshot entirely. Costs: no point-in-time consistency (rows
# may shift mid-run). Benefit: it actually finishes, and saves a 23GB copy.
#
# Usage: bash scripts/ops/precompute_live.sh
set -euo pipefail

BASE="$HOME/meritgiving"
cd "$BASE"

export MERIT_DB_PATH="${MERIT_DB_PATH:-$BASE/data/merit_registry.db}"
export PRECOMPUTE_OUT="${PRECOMPUTE_OUT:-$BASE/.deploy_scratch/precompute}"
export PRECOMPUTE_DIR="$PRECOMPUTE_OUT"

LOG="$BASE/logs/precompute_live.log"
mkdir -p "$(dirname "$LOG")" "$PRECOMPUTE_OUT"

PY="$BASE/venv/bin/python3"
[ -x "$PY" ] || PY=python3

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
die() { log "FATAL: $*"; exit 1; }

log "===== precompute_live start ====="
log "  source DB : $MERIT_DB_PATH"
log "  output    : $PRECOMPUTE_OUT"

# Trust-critical: regenerate org/browse/content CLEAN so a link that went stale
# (donate beta -> dead) can never survive via incremental file-skipping.
log "clearing stale org/browse/content output (link freshness)..."
rm -rf "$PRECOMPUTE_OUT/orgs" "$PRECOMPUTE_OUT/browse" "$PRECOMPUTE_OUT/content"

# FAISS_PQ=1 is mandatory: IVFPQ keeps the index ~150-300MB. Without it the flat
# index is ~7GB and the droplet disk guard aborts the deploy (2026-06-09).
if [ ! -e "$PRECOMPUTE_OUT/faiss_index.bin" ]; then
  log "stage: faiss_index ..."
  FAISS_PQ=1 "$PY" scripts/build_faiss_index.py >>"$LOG" 2>&1 || die "faiss_index failed"
  log "  ok faiss_index"
else
  log "skip faiss_index (exists)"
fi

log "stage: browse ..."
"$PY" scripts/precompute_browse.py >>"$LOG" 2>&1 || die "browse failed"
log "  ok browse"

log "stage: orgs ..."
SKIP_FAISS=1 "$PY" scripts/precompute_orgs.py >>"$LOG" 2>&1 || die "orgs failed"
log "  ok orgs"

# precompute_orgs.py always writes similar_organizations=[]; this pass patches
# real tiered matches in place. Must run after orgs, before content.
log "stage: similar_orgs ..."
"$PY" scripts/precompute_similar_orgs.py >>"$LOG" 2>&1 || die "similar_orgs failed"
log "  ok similar_orgs"

log "stage: content ..."
"$PY" scripts/precompute_content.py >>"$LOG" 2>&1 || die "content failed"
log "  ok content"

for f in browse content faiss_index.bin ein_map.json.gz; do
  [ -e "$PRECOMPUTE_OUT/$f" ] || die "missing precompute artifact: $f"
done
log "artifacts present; size: $(du -sh "$PRECOMPUTE_OUT" | cut -f1)"

# LINK-INTEGRITY GATE — donate/website links must match source exactly (fail closed).
log "validating donate/website link integrity..."
"$PY" scripts/validate_link_integrity.py >>"$LOG" 2>&1 \
  || die "link-integrity validation FAILED — droplet untouched"
log "✓ link integrity verified"

log "===== precompute_live complete ====="
