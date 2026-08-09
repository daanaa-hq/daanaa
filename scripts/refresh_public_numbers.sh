#!/usr/bin/env bash
#
# refresh_public_numbers.sh — keep the live public numbers in sync with the DB.
#
# Regenerates the derived content artifacts (homepage stats, sector health,
# research snapshot), refuses to ship unless every public count agrees, then
# deploys to the droplet, restarts the service, and verifies the live API.
#
# This is the automation that closes the "stale homepage.json.gz" trap: nothing
# ships unless the numbers match, and the service is RESTARTED (not HUP'd, which
# does not reliably cycle all gunicorn workers).
#
#   bash scripts/refresh_public_numbers.sh            # regenerate + deploy + verify
#   bash scripts/refresh_public_numbers.sh --check    # regenerate + consistency only, NO deploy
#
set -euo pipefail

ROOT="/home/akbar/meritgiving"
PY="$ROOT/venv/bin/python3"
DROPLET="root@107.170.26.8"
SSH=(ssh -o ServerAliveInterval=10 -o ConnectTimeout=20 -o BatchMode=yes "$DROPLET")
RSYNC_RSH="ssh -o ServerAliveInterval=10 -o ConnectTimeout=20 -o BatchMode=yes"

CONTENT_OUT="$ROOT/precompute_output/content"
SNAPSHOT="$ROOT/frontend/public/research-snapshot.json"
REMOTE_CONTENT="/data/precompute/v1/content"
REMOTE_DIST="/opt/daanaa/frontend/dist"

CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1

log() { echo "[$(date -u +%H:%M:%S)] $*"; }
fail() { echo "[$(date -u +%H:%M:%S)] ERROR: $*" >&2; exit 1; }

cd "$ROOT"

# 1. Regenerate derived artifacts from the current DB ------------------------
log "Regenerating content artifacts (homepage, sector health, …)…"
PRECOMPUTE_OUT="$ROOT/precompute_output" "$PY" scripts/precompute_content.py >/dev/null \
  || fail "precompute_content.py failed"

log "Regenerating research snapshot…"
"$PY" scripts/export_research_snapshot.py >/dev/null \
  || fail "export_research_snapshot.py failed"

# 2. Consistency gate — DB == homepage == snapshot --------------------------
log "Consistency gate…"
"$PY" scripts/check_number_consistency.py \
  --homepage "$CONTENT_OUT/homepage.json.gz" \
  --snapshot "$SNAPSHOT" \
  || fail "consistency gate failed — numbers disagree, refusing to deploy"

if [ "$CHECK_ONLY" = "1" ]; then
  log "--check mode: regenerated and verified locally. No deploy."
  exit 0
fi

# 3. Deploy the artifacts to the droplet ------------------------------------
log "Backing up remote homepage.json.gz…"
"${SSH[@]}" "cp $REMOTE_CONTENT/homepage.json.gz $REMOTE_CONTENT/homepage.json.gz.bak 2>/dev/null || true"

log "Pushing content artifacts → $REMOTE_CONTENT …"
rsync -az -e "$RSYNC_RSH" "$CONTENT_OUT"/*.json.gz "$DROPLET:$REMOTE_CONTENT/" \
  || fail "content rsync failed"

log "Pushing research snapshot → $REMOTE_DIST …"
rsync -az -e "$RSYNC_RSH" "$SNAPSHOT" "$DROPLET:$REMOTE_DIST/research-snapshot.json" \
  || fail "snapshot rsync failed"

# 4. Restart the service so all workers re-read the new files ----------------
log "Restarting daanaa service…"
"${SSH[@]}" "systemctl restart daanaa-api" || fail "service restart failed"
sleep 5

# 5. Verify the live API matches the DB -------------------------------------
log "Verifying live /api/stats…"
DB_COUNT="$("$PY" -c "import sqlite3,sys; sys.path.insert(0,'scripts'); from registry_filters import canonical_active_count; c=sqlite3.connect('$ROOT/data/merit_registry.db'); print(canonical_active_count(c))")"
LIVE_COUNT="$(curl -s --max-time 20 https://daanaa.org/api/stats | "$PY" -c 'import sys,json; print(json.load(sys.stdin).get("total_organizations",""))')"

log "  DB:   $DB_COUNT"
log "  live: $LIVE_COUNT"
if [ "$DB_COUNT" != "$LIVE_COUNT" ]; then
  fail "live /api/stats ($LIVE_COUNT) != DB ($DB_COUNT) after deploy"
fi

log "✅ Public numbers refreshed and verified live: $LIVE_COUNT"
