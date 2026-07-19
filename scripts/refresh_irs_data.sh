#!/bin/bash
# Automated weekly IRS Exempt Organizations data refresh
# Downloads latest EO data and delta-loads new organizations

set -e
source ~/meritgiving/venv/bin/activate
cd ~/meritgiving

LOG_FILE="logs/irs_refresh.log"
mkdir -p logs

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "========== IRS DATA REFRESH (Weekly) =========="
START_TIME=$(date +%s)

# Step 1: Count current EINs
BEFORE=$(sqlite3 data/merit_registry.db "SELECT COUNT(DISTINCT EIN) FROM registry_enriched WHERE EIN IS NOT NULL;")
log "Before: $BEFORE organizations in registry"

# Step 2: Sync latest IRS data (leveraging existing sync_irs_revocations pattern)
log "Syncing latest IRS Exempt Organizations data..."
python3 scripts/sync_irs_data.py --mode delta --log-file "$LOG_FILE" 2>&1 || {
  log "ERROR: IRS data sync failed"
  exit 1
}

# Step 3: Count after refresh
AFTER=$(sqlite3 data/merit_registry.db "SELECT COUNT(DISTINCT EIN) FROM registry_enriched WHERE EIN IS NOT NULL;")
ADDED=$((AFTER - BEFORE))
log "After: $AFTER organizations (+$ADDED new)"

# Step 4: Trigger discovery daemon to pick up new orgs
if [ "$ADDED" -gt 0 ]; then
  log "New organizations detected. Signaling discovery daemon to prioritize them..."
  # Discovery daemon monitors queue automatically; no signal needed
  log "Discovery daemon will automatically start processing new orgs"
fi

# Step 5: Make new orgs searchable + prove each findable (founder rule
# 2026-07-19: every org entering the registry is indexed and verified at
# ingestion time, never left waiting for the next full FTS rebuild).
log "Delta search-index sync + findability verification..."
python3 scripts/search_index_delta.py 2>&1 | tee -a "$LOG_FILE" || {
  log "WARNING: search index delta failed — new orgs may be unsearchable until nightly rebuild"
}

ELAPSED=$(($(date +%s) - START_TIME))
log "========== IRS DATA REFRESH COMPLETE ($ELAPSED seconds) =========="
