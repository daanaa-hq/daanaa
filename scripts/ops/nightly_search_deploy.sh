#!/bin/bash
# nightly_search_deploy.sh — rebuild search.db from nightly scores and ship to droplet.
#
# Runs at 4:30am daily, after overnight_pipeline (2:30am) and FTS rebuild (7:30am → moved
# here so search.db is always built from a fresh FTS index the same night).
#
# Steps:
#   1. Rebuild FTS5 index in merit_registry.db (fast, ~30s)
#   2. Build search.db (copies registry_enriched + org_fts → /tmp/search_new.db)
#   3. Integrity check before shipping
#   4. rsync to droplet (checksum diff — only changed SQLite pages transfer)
#   5. Patch changed org precompute files (v5 context that changed since last run)
#   6. rsync delta org files to droplet
#   7. Restart droplet API to clear in-memory cache
#   8. Alert on failure
#
# AWS note: S3 backup of search.db runs via daanaa_backup.sh (2am) which already
# snapshots merit_registry.db. search.db is a derived artifact — no separate S3 backup.

set -euo pipefail

BASE="$HOME/meritgiving"
SSH_KEY="$HOME/.ssh/daanaa_do_cron"  # passphrase-free automation key (see LESSONS.md 2026-07-05)
DROPLET="root@162.243.97.179"
SSH="ssh -i $SSH_KEY -o ConnectTimeout=20 -o StrictHostKeyChecking=accept-new $DROPLET"
LOG="$BASE/logs/nightly_search_deploy.log"
LOCK="$BASE/logs/.nightly_search_deploy.lock"
CONFIG="$BASE/.aws-backup-config"

mkdir -p "$(dirname "$LOG")"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
die() { log "FATAL: $*"; send_alert "FATAL: $*"; exit 1; }

[ -f "$CONFIG" ] && source "$CONFIG"

# Prevent overlapping runs
if [ -f "$LOCK" ]; then
    LOCK_AGE=$(( $(date +%s) - $(stat -c %Y "$LOCK" 2>/dev/null || echo 0) ))
    [ "$LOCK_AGE" -lt 7200 ] && { log "Already running (lock $LOCK_AGE s old). Skipping."; exit 0; }
    rm -f "$LOCK"
fi
touch "$LOCK"
trap 'rm -f "$LOCK"' EXIT

cd "$BASE"
source venv/bin/activate 2>/dev/null || die "venv not found"

send_alert() {
    # venv python + repo cwd: the old bare `python3` with cwd-relative import
    # failed silently under cron (2>/dev/null), so FATALs never emailed.
    ( cd "$BASE" && ./venv/bin/python3 - "$1" <<'PYEOF'
import sys; sys.path.insert(0, '.')
from scripts.ops.mailer import send_ops_email
send_ops_email("security@daanaa.org", "[Daanaa ALERT] nightly_search_deploy failed", sys.argv[1])
PYEOF
    ) || log "WARN: alert email failed to send"
}

# ── Step 1: Rebuild FTS5 index ──────────────────────────────────────────────
log "Step 1/6: Rebuilding FTS5 index..."
python3 scripts/build_fts_index.py --rebuild >> "$LOG" 2>&1 \
    || die "FTS rebuild failed"
log "FTS rebuild done."

# ── Step 2: Build search.db ─────────────────────────────────────────────────
log "Step 2/6: Building search.db..."
OUT="/tmp/search_new_$(date +%Y%m%d).db"
python3 scripts/build_search_db.py --out "$OUT" >> "$LOG" 2>&1 \
    || die "build_search_db failed"
SIZE=$(du -sh "$OUT" | cut -f1)
log "search.db built: $OUT ($SIZE)"

# ── Step 3: Integrity check ─────────────────────────────────────────────────
log "Step 3/6: Integrity check..."
RESULT=$(sqlite3 "$OUT" "PRAGMA integrity_check;" 2>/dev/null)
[ "$RESULT" = "ok" ] || die "search.db integrity check failed: $RESULT"
ROW_COUNT=$(sqlite3 "$OUT" "SELECT COUNT(*) FROM registry_enriched;" 2>/dev/null)
[ "$ROW_COUNT" -gt 1000000 ] || die "search.db row count too low: $ROW_COUNT"
log "Integrity OK. registry_enriched rows: $ROW_COUNT"

# ── Step 4: Rsync search.db to droplet ──────────────────────────────────────
log "Step 4/6: Rsyncing search.db to droplet..."
rsync --checksum --progress \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=accept-new" \
    "$OUT" "$DROPLET:/data/precompute/v1/search.db.staging" >> "$LOG" 2>&1 \
    || die "rsync search.db failed"
# Atomic swap
# Target is the path the lean API actually reads (DATA_DIR/'search.db', see
# scripts/droplet_api.py:93). Shipping to /data/search.db was a silent no-op —
# the serving catalog never refreshed (found 2026-07-06, see LESSONS.md).
$SSH "mv /data/precompute/v1/search.db.staging /data/precompute/v1/search.db" 2>>"$LOG" \
    || die "atomic swap failed on droplet"
log "search.db deployed."

# ── Step 5: Patch changed org precompute files ──────────────────────────────
log "Step 5/6: Patching changed org precompute files..."
PATCH_LOG="/tmp/precompute_patch_$(date +%Y%m%d).log"
python3 scripts/patch_precompute_v5_context.py >> "$PATCH_LOG" 2>&1
UPDATED=$(grep -oP '(?<=updated=)\d+' "$PATCH_LOG" | tail -1 || echo 0)
log "Precompute patch: $UPDATED files updated."

# ── Step 6: Rsync changed org files to droplet ──────────────────────────────
if [ "${UPDATED:-0}" -gt 0 ]; then
    log "Step 6/6: Rsyncing $UPDATED changed org files..."
    rsync -az --checksum --stats \
        -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=accept-new" \
        precompute_output/orgs/ "$DROPLET:/data/precompute/v1/orgs/" >> "$LOG" 2>&1
    log "Org files synced."

    # Restart API to clear cache
    $SSH "systemctl restart daanaa" 2>>"$LOG" && log "API restarted." \
        || log "WARN: API restart failed (cache may be stale)"
else
    log "Step 6/6: No org file changes. Skipping rsync."
fi

# Clean up old search.db build artifacts (keep last 3)
find /tmp -name "search_new_*.db" -mtime +3 -delete 2>/dev/null || true

log "Done. search.db ($SIZE, $ROW_COUNT rows) live on droplet."

# Success ping
python3 - <<'PYEOF' 2>/dev/null || true
import sys; sys.path.insert(0, '.')
from scripts.ops.mailer import send_ops_email
import os
log = open(os.path.expanduser("~/meritgiving/logs/nightly_search_deploy.log")).readlines()
tail = "".join(log[-10:])
send_ops_email("security@daanaa.org",
    "[Daanaa OK] nightly search.db deployed",
    f"search.db rebuilt and live on droplet.\n\n{tail}")
PYEOF
