#!/bin/bash
# Runs after mission gen completes: FTS rebuild → IRS revocations → precompute → droplet sync
# Usage: bash scripts/post_mission_chain.sh &

BASE="$HOME/meritgiving"
LOG="$BASE/logs/post_mission_chain.log"
VENV="$BASE/venv/bin/python3"

ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(ts)] $*" | tee -a "$LOG"; }

log "=== post_mission_chain started ==="
log "Waiting for mission gen to finish..."

# Wait until generate_missions process is gone
until ! pgrep -f "generate_missions" > /dev/null 2>&1; do sleep 30; done
log "Mission gen finished. Starting chain."

# 1. FTS rebuild
log "--- Step 1: FTS rebuild ---"
cd "$BASE" || exit 1
"$VENV" scripts/build_fts_index.py --rebuild >> logs/fts_rebuild.log 2>&1
log "FTS rebuild done (exit $?)"

# 2. IRS revocations (force re-download since it was stale)
log "--- Step 2: IRS revocations sync ---"
"$VENV" scripts/sync_irs_revocations.py --force >> logs/irs_revocations.log 2>&1
log "IRS revocations done (exit $?)"

# 3. Precompute org JSON files with fresh missions + v5_context
log "--- Step 3: precompute_orgs.py ---"
"$VENV" scripts/precompute_orgs.py >> logs/precompute.log 2>&1
log "Precompute done (exit $?)"

# 4. Rebuild FTS again after precompute (catches any mission updates)
log "--- Step 4: FTS rebuild (post-precompute) ---"
"$VENV" scripts/build_fts_index.py --rebuild >> logs/fts_rebuild.log 2>&1
log "Second FTS rebuild done (exit $?)"

# 5. Sync updated org files to droplet
log "--- Step 5: Sync orgs to droplet ---"
rsync -az --inplace \
  -e "ssh -i $HOME/.ssh/daanaa_do -o StrictHostKeyChecking=accept-new" \
  "$BASE/precompute_output/orgs/" \
  root@162.243.97.179:/data/precompute/v1/orgs/ >> "$LOG" 2>&1
log "Droplet orgs sync done (exit $?)"

# 6. Sync frontend (in case it changed)
log "--- Step 6: Sync frontend to droplet ---"
rsync -az --delete \
  -e "ssh -i $HOME/.ssh/daanaa_do -o StrictHostKeyChecking=accept-new" \
  "$BASE/frontend/dist/" \
  root@162.243.97.179:/opt/daanaa/frontend/ >> "$LOG" 2>&1
log "Frontend sync done (exit $?)"

log "=== post_mission_chain complete ==="
