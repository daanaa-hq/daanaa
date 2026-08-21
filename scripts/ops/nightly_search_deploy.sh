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
#   4.5. Post-deploy verification: EXPLAIN QUERY PLAN + live search-latency check
#        (alert-only, added 2026-08-21 — see LESSONS.md 2026-07-18/2026-08-21)
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
DROPLET="root@107.170.26.8"
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
# Path fixed 2026-08-21: was scripts/build_fts_index.py (pre-2026-08-12
# folder-migration location). This had silently FATAL'd every single night
# since at least 2026-08-14 (confirmed via logs/nightly_search_deploy.log --
# "Step 1/6" then immediately "FATAL: FTS rebuild failed", every night, no
# exceptions) -- production search.db had not actually been rebuilt in over
# a week. Found while checking whether new IRS data had come in; see
# LESSONS.md 2026-08-21.
log "Step 1/6: Rebuilding FTS5 index..."
python3 scripts/search/build_fts_index.py --rebuild >> "$LOG" 2>&1 \
    || die "FTS rebuild failed"
log "FTS rebuild done."

# ── Step 2: Build search.db ─────────────────────────────────────────────────
# Path fixed 2026-08-21, same cause as Step 1 above.
log "Step 2/6: Building search.db..."
OUT="/tmp/search_new_$(date +%Y%m%d).db"
python3 scripts/search/build_search_db.py --out "$OUT" >> "$LOG" 2>&1 \
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

# ── Step 4.5: Post-deploy verification (added 2026-08-21) ──────────────────
# This job ships a fresh SQLite file every night. SQLite's query planner picks
# join order from table statistics, which get refreshed by every rebuild —
# so a planner flip (the exact bug class fixed today, commit 44b4bb9e0ac; see
# LESSONS.md 2026-07-18 and 2026-08-21) could in principle recur purely from
# data changes even with correct code. Alert-only, never blocks/rolls back
# this step: a search.db rollback is riskier and less validated than the
# code-file .prev pattern in sync_droplet_api.sh, so this is detection, not
# an automatic revert.
log "Step 4.5/6: Verifying query plan + live search latency..."
PLAN=$($SSH "sqlite3 /data/precompute/v1/search.db \"
EXPLAIN QUERY PLAN
WITH fts_candidates AS MATERIALIZED (
  SELECT ein, bm25(org_fts, 10, 5, 1, 1) AS rel FROM org_fts
  WHERE org_fts MATCH 'health' ORDER BY rel LIMIT 2000
)
SELECT r.EIN FROM fts_candidates fts
CROSS JOIN registry_enriched r ON r.EIN = fts.ein
WHERE subsection = '3' AND deductibility = '1'
LIMIT 24;\"" 2>>"$LOG" || echo "PLAN_CHECK_FAILED")
if ! echo "$PLAN" | grep -q "MATERIALIZE fts_candidates"; then
    log "WARN: query plan does not show MATERIALIZE fts_candidates as the first step:"
    log "$PLAN"
    send_alert "nightly_search_deploy: query plan looks wrong after tonight's rebuild (join-order regression class, LESSONS.md 2026-07-18/2026-08-21). Plan seen:\n\n$PLAN\n\nsearch.db was still deployed — this is a warning, not a block. Check EXPLAIN QUERY PLAN by hand before assuming search is fine."
else
    log "Query plan OK (MATERIALIZE fts_candidates first)."
fi

# Real search-latency check against the live public site, cache-busted (this
# job's own deploy doesn't wait for it — daanaa_watchdog.py catches ongoing
# regressions every 5 min separately; this is a same-night, deploy-time
# tripwire so a bad rebuild doesn't sit undetected until the next cron tick).
LAT_START=$(date +%s%N)
LAT_CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 \
    "https://daanaa.org/api/organizations?q=health&per_page=24&_cb=$(date +%s%N)" 2>>"$LOG" || echo "000")
LAT_MS=$(( ($(date +%s%N) - LAT_START) / 1000000 ))
if [ "$LAT_CODE" != "200" ] || [ "$LAT_MS" -gt 3000 ]; then
    log "WARN: post-deploy search latency check failed (HTTP $LAT_CODE, ${LAT_MS}ms)"
    send_alert "nightly_search_deploy: post-deploy search latency check failed — HTTP $LAT_CODE, ${LAT_MS}ms (SLO 3000ms). search.db was still deployed. daanaa_watchdog.py will keep monitoring every 5 min."
else
    log "Search latency OK: ${LAT_MS}ms"
fi

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
    $SSH "systemctl restart daanaa-api" 2>>"$LOG" && log "API restarted." \
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
