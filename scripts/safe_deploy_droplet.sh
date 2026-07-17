#!/bin/bash
#
# safe_deploy_droplet.sh — Sandboxed, corruption-proof droplet deploy.
#
# Design goals (set 2026-06-09, after the 2026-06-06 corruption + 2026-06-09 disk lockup):
#   1. NEVER disturb the live :5000 API. We read a consistent online snapshot
#      via SQLite's .backup API — gunicorn keeps serving the live DB untouched.
#   2. NEVER ship corrupt data. PRAGMA integrity_check gates every deploy.
#      This is the exact failure mode that nuked the DB on 2026-06-06.
#   3. NEVER fill the droplet. Disk is checked BEFORE transfer; abort if it
#      won't fit. This is the exact failure mode that locked the box on 2026-06-09.
#   4. RESUMABLE / sandboxed. All work lands in a scratch dir; precompute stages
#      skip if their output already exists (use --force to rebuild).
#
# The droplet serves PRECOMPUTE STATIC FILES (droplet_api:app from /data/precompute/v1).
# It does NOT use merit_registry.db. We never ship the SQLite DB to it.
#
# Usage:
#   bash scripts/safe_deploy_droplet.sh            # full pipeline, resume where possible
#   bash scripts/safe_deploy_droplet.sh --force    # rebuild all precompute stages
#   bash scripts/safe_deploy_droplet.sh --build-only   # snapshot+precompute, no ship
#   bash scripts/safe_deploy_droplet.sh --ship-only    # ship existing scratch payload
#
set -euo pipefail

# ---- Config ----
DROPLET_IP="162.243.97.179"
DROPLET_USER="root"
SSH_KEY="$HOME/.ssh/daanaa_do_cron"  # passphrase-free automation key (see LESSONS.md 2026-07-05)
SSH="ssh -i $SSH_KEY -o ConnectTimeout=15 -o StrictHostKeyChecking=accept-new ${DROPLET_USER}@${DROPLET_IP}"

BASE="$HOME/meritgiving"
LIVE_DB="$BASE/data/merit_registry.db"
SCRATCH="${DEPLOY_SCRATCH:-$BASE/.deploy_scratch}"   # sandbox; nothing here is served live
SNAPSHOT="$SCRATCH/snapshot.db"
PRECOMPUTE="$SCRATCH/precompute"
PAYLOAD="$SCRATCH/precompute_payload.tar.gz"
LOG="$BASE/logs/safe_deploy.log"
DROPLET_STAGING="/opt/daanaa/staging"
DISK_MARGIN_GB=${DISK_MARGIN_GB:-5}   # keep at least this much free on the droplet after deploy
FRONTEND_LOCAL="$BASE/frontend"
FRONTEND_DROPLET="/opt/daanaa/frontend/dist"   # FRONTEND_DIR that droplet_api serves the SPA from
# Gunicorn imports droplet_api.py from /opt/daanaa/ (WorkingDirectory), NOT from scripts/.
# Always write to the root-level path; keep scripts/ as a reference copy only.
DROPLET_API_LIVE="/opt/daanaa/droplet_api.py"
DROPLET_API_LOCAL="$BASE/scripts/droplet_api.py"

FORCE=0; BUILD_ONLY=0; SHIP_ONLY=0; FRONTEND_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --build-only) BUILD_ONLY=1 ;;
    --ship-only) SHIP_ONLY=1 ;;
    --frontend-only) FRONTEND_ONLY=1 ;;   # SPA-only change: skip DB snapshot/precompute/data ship
    *) echo "Unknown arg: $arg"; exit 2 ;;
  esac
done

mkdir -p "$SCRATCH" "$PRECOMPUTE" "$(dirname "$LOG")"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
die() { log "FATAL: $*"; exit 1; }

cd "$BASE"
source venv/bin/activate 2>/dev/null || die "venv not found"

# ============================================================
# STAGE 0 — Preflight
# ============================================================
preflight() {
  log "===== STAGE 0: Preflight ====="

  # :5000 must be alive — we coexist with it, never disturb it.
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:5000/health || echo 000)
  [ "$code" = "200" ] || die ":5000 not healthy (got $code) — refusing to run while local API is down"
  log "✓ :5000 healthy ($code) — will not be disturbed"

  # Droplet reachable
  $SSH "echo ok" >/dev/null 2>&1 || die "cannot SSH to droplet"
  log "✓ droplet reachable"

  # Local scratch space (need room for snapshot + precompute + payload)
  local db_gb avail_gb
  db_gb=$(du -BG "$LIVE_DB" | awk '{gsub(/G/,"",$1); print $1}')
  avail_gb=$(df -BG "$SCRATCH" | tail -1 | awk '{gsub(/G/,"",$4); print $4}')
  log "Local scratch free: ${avail_gb}G, live DB: ${db_gb}G"
  [ "$avail_gb" -gt $((db_gb * 2 + 20)) ] || die "insufficient local scratch space"
}

# ============================================================
# STAGE 1 — Online snapshot (NEVER touches the live DB process)
# ============================================================
snapshot() {
  log "===== STAGE 1: Online snapshot ====="
  if [ -f "$SNAPSHOT" ] && [ "$FORCE" = "0" ]; then
    log "snapshot exists, reuse (use --force to refresh)"
  else
    rm -f "$SNAPSHOT" "$SNAPSHOT-wal" "$SNAPSHOT-shm"
    # .backup uses SQLite's online backup API: a consistent copy taken while
    # gunicorn keeps reading/writing the live DB. No locks held against :5000.
    #
    # Write-quiesce (2026-07-17): .backup RESTARTS from page 0 every time a
    # writer commits, and the discovery daemon commits constantly — a 15GB
    # snapshot livelocked for 34 min, then finished in 39 s once writers were
    # paused. SIGSTOP/SIGCONT pauses them in place (no lost work); the trap
    # guarantees resume even if the snapshot dies.
    QUIESCED_PIDS=$(pgrep -f "discovery_daemon.py|reverify_donate_pages.py|enrich_batch.py" || true)
    if [ -n "$QUIESCED_PIDS" ]; then
      log "Pausing DB writers during snapshot: $(echo $QUIESCED_PIDS | tr '\n' ' ')"
      # shellcheck disable=SC2086
      kill -STOP $QUIESCED_PIDS 2>/dev/null || true
      trap 'kill -CONT $QUIESCED_PIDS 2>/dev/null || true' EXIT
    fi
    log "Taking online .backup snapshot (live API undisturbed)..."
    sqlite3 "$LIVE_DB" ".backup '$SNAPSHOT'" || die "snapshot failed"
    log "✓ snapshot written ($(du -h "$SNAPSHOT" | cut -f1))"
    if [ -n "$QUIESCED_PIDS" ]; then
      # shellcheck disable=SC2086
      kill -CONT $QUIESCED_PIDS 2>/dev/null || true
      trap - EXIT
      log "DB writers resumed"
    fi
  fi

  # THE safeguard: never let a corrupt snapshot proceed to precompute/deploy.
  log "Running PRAGMA integrity_check (corruption gate)..."
  local result
  result=$(sqlite3 "$SNAPSHOT" "PRAGMA integrity_check;" | head -1)
  [ "$result" = "ok" ] || die "integrity_check FAILED ($result) — aborting, droplet untouched"
  log "✓ integrity_check: ok — safe to build from this snapshot"
}

# ============================================================
# STAGE 2 — Precompute from the snapshot (sandboxed output)
# ============================================================
precompute() {
  log "===== STAGE 2: Precompute (from snapshot, sandboxed) ====="
  export MERIT_DB_PATH="$SNAPSHOT"
  export PRECOMPUTE_OUT="$PRECOMPUTE"
  export PRECOMPUTE_DIR="$PRECOMPUTE"

  run_stage() {
    local name="$1" check="$2"; shift 2
    if [ -e "$check" ] && [ "$FORCE" = "0" ]; then
      log "  skip $name (exists: $check)"
    else
      log "  building $name ..."
      "$@" >>"$LOG" 2>&1 || die "$name failed (see $LOG)"
      log "  ✓ $name done"
    fi
  }

  # Trust-critical: org files are regenerated CLEAN every deploy so a link that went
  # stale (e.g. donate beta->dead) can never survive via incremental file-skipping.
  # precompute_orgs.py skips files that already exist, so we clear the dir first.
  log "  clearing stale org/browse/content output (link freshness)..."
  rm -rf "$PRECOMPUTE/orgs" "$PRECOMPUTE/browse" "$PRECOMPUTE/content"

  # FAISS first — org precompute depends on the index for similar-orgs.
  # FAISS_PQ=1 is mandatory: IVFPQ (~64B/vector) keeps the index ~150-300M so the
  # payload fits the 33G droplet (decision 2026-06-09). Without it the flat index
  # is ~7G and the disk guard aborts the deploy.
  run_stage "faiss_index"  "$PRECOMPUTE/faiss_index.bin"  env FAISS_PQ=1 python3 scripts/build_faiss_index.py
  python3 scripts/precompute_browse.py  >>"$LOG" 2>&1 || die "browse precompute failed"
  SKIP_FAISS=1 python3 scripts/precompute_orgs.py    >>"$LOG" 2>&1 || die "orgs precompute failed"
  # precompute_orgs.py always writes similar_organizations=[] (its FAISS-based
  # path is dead code, never called from main()) -- this second pass patches
  # real tiered matches into every org file in place. Must run after
  # precompute_orgs.py (needs the full org set on disk to build its buckets)
  # and before content precompute so exports see the final data.
  # Fixed 2026-07-10: every full deploy was shipping empty similar-orgs lists
  # (verified live) because this was only running on a separate, unwired
  # monthly cron that any deploy in between silently wiped out.
  python3 scripts/precompute_similar_orgs.py >>"$LOG" 2>&1 || die "similar-orgs precompute failed"
  python3 scripts/precompute_content.py >>"$LOG" 2>&1 || die "content precompute failed"

  # Required artifacts present?
  for f in browse content faiss_index.bin ein_map.json.gz; do
    [ -e "$PRECOMPUTE/$f" ] || die "missing precompute artifact: $f"
  done
  log "✓ precompute complete: $(du -sh "$PRECOMPUTE" | cut -f1)"

  # LINK-INTEGRITY GATE — donate/website links must match the snapshot exactly (fail closed).
  log "  validating donate/website link integrity..."
  python3 scripts/validate_link_integrity.py >>"$LOG" 2>&1 \
    || die "link-integrity validation FAILED — aborting, droplet untouched (see $LOG)"
  log "✓ link integrity verified — no corrupt or stale donate/website links"
}

# ============================================================
# STAGE 3 — Package
# ============================================================
package() {
  log "===== STAGE 3: Package ====="
  rm -f "$PAYLOAD" "$PAYLOAD.sha256"
  # Exclude build scratch (FAISS memmap) — never ship it to the droplet.
  tar --exclude='./vectors.f32.memmap' -czf "$PAYLOAD" -C "$PRECOMPUTE" .
  ( cd "$(dirname "$PAYLOAD")" && sha256sum "$(basename "$PAYLOAD")" > "$PAYLOAD.sha256" )
  log "✓ payload: $(du -h "$PAYLOAD" | cut -f1)"
}

# ============================================================
# STAGE 4 — Disk-guarded ship (abort rather than fill the box)
# ============================================================
ship() {
  log "===== STAGE 4: Disk-guarded ship ====="
  # Purge the previous backup (v0) before checking disk — v0 is only a same-deploy
  # rollback aid; once we're about to ship a new payload it's safe to drop.
  $SSH "rm -rf /data/precompute/v0 /opt/daanaa/staging/precompute_payload.tar.gz /tmp/tmp.* 2>/dev/null || true"
  # Uncompressed footprint the droplet must hold transiently (staging extract).
  local need_gb free_gb
  need_gb=$(du -BG "$PRECOMPUTE" | tail -1 | awk '{gsub(/G/,"",$1); print $1}')
  free_gb=$($SSH "df -BG / | tail -1 | awk '{gsub(/G/,\"\",\$4); print \$4}'")
  log "Droplet free: ${free_gb}G, payload needs ~${need_gb}G + ${DISK_MARGIN_GB}G margin"
  if [ "$free_gb" -lt $((need_gb + DISK_MARGIN_GB)) ]; then
    die "INSUFFICIENT DROPLET DISK (${free_gb}G free, need $((need_gb + DISK_MARGIN_GB))G). \
Aborting BEFORE transfer — droplet untouched. Shrink payload (quantize FAISS) or resize droplet."
  fi
  $SSH "mkdir -p $DROPLET_STAGING"
  log "Transferring payload..."
  scp -i "$SSH_KEY" "$PAYLOAD" "$PAYLOAD.sha256" "${DROPLET_USER}@${DROPLET_IP}:$DROPLET_STAGING/" \
    || die "transfer failed — droplet live data untouched (atomic swap not yet run)"
  log "✓ payload on droplet"
}

# ============================================================
# STAGE 5 — Atomic swap (delegates to deploy_droplet.sh: verify→swap→healthcheck→rollback)
# ============================================================
swap() {
  log "===== STAGE 5: Atomic swap ====="
  $SSH "bash /opt/daanaa/scripts/deploy_droplet.sh $DROPLET_STAGING/$(basename "$PAYLOAD")" 2>&1 | tee -a "$LOG" \
    || die "atomic swap failed — deploy_droplet.sh auto-rolled-back to previous version"
  # Public health check
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' https://daanaa.org/health || echo 000)
  log "Public health: $code"
  [ "$code" = "200" ] || log "WARN: public health not 200 ($code) — check droplet"
  # Free the staging tarball now that it's live
  $SSH "rm -f $DROPLET_STAGING/$(basename "$PAYLOAD")*" || true
  log "✓ deploy complete"
}

# ============================================================
# Frontend build — research snapshot (from the same snapshot DB) + SPA bundle.
# Methodology is a static page in the bundle; research page reads the bundled
# research-snapshot.json. Built locally; shipped in frontend_ship().
# ============================================================
frontend_build() {
  log "===== STAGE 6: Frontend build (research snapshot + SPA) ====="
  log "  regenerating research-snapshot.json from snapshot DB..."
  MERIT_DB_PATH="$SNAPSHOT" python3 scripts/export_research_snapshot.py >>"$LOG" 2>&1 \
    || die "research snapshot export failed"
  log "  npm run build (bundles research snapshot + methodology + all pages)..."
  ( cd "$FRONTEND_LOCAL" && npm run build ) >>"$LOG" 2>&1 || die "frontend build failed"
  [ -f "$FRONTEND_LOCAL/dist/index.html" ] || die "frontend dist/index.html missing after build"
  [ -f "$FRONTEND_LOCAL/dist/research-snapshot.json" ] || die "research-snapshot.json missing from dist"
  log "✓ frontend built ($(du -sh "$FRONTEND_LOCAL/dist" | cut -f1))"
}

# Ship the SPA bundle. droplet_api serves files fresh from FRONTEND_DROPLET, so an
# rsync updates the site with no service restart. Atomic-ish: rsync to a temp dir then swap.
frontend_ship() {
  log "===== STAGE 7: Frontend ship (rsync dist → droplet) ====="
  # No --delete: old hashed chunks stay in .new through the compatibility window so
  # any cached HTML referencing prior chunk names continues to work after the swap.
  rsync -az -e "ssh -i $SSH_KEY -o ConnectTimeout=15" \
    "$FRONTEND_LOCAL/dist/" "${DROPLET_USER}@${DROPLET_IP}:${FRONTEND_DROPLET}.new/" \
    >>"$LOG" 2>&1 || die "frontend rsync failed — live SPA untouched (synced to .new)"
  # Merge prior hashed assets into .new so old JS/CSS URLs remain valid post-swap.
  $SSH "[ -d ${FRONTEND_DROPLET}/assets ] && \
    rsync -a --ignore-existing ${FRONTEND_DROPLET}/assets/ ${FRONTEND_DROPLET}.new/assets/ 2>/dev/null || true" \
    >>"$LOG" 2>&1
  # Atomic swap: promote .new → live, keep .old until smoke tests pass.
  $SSH "( [ -d ${FRONTEND_DROPLET} ] && mv ${FRONTEND_DROPLET} ${FRONTEND_DROPLET}.old || true ) && \
        mv ${FRONTEND_DROPLET}.new ${FRONTEND_DROPLET}" >>"$LOG" 2>&1 \
    || die "frontend swap failed on droplet"
  # Smoke-test SPA routes + one hashed JS chunk (catches asset-404 regressions).
  local ok=1
  for path in "/" "/directory" "/org/264837170" "/about"; do
    local code
    code=$(curl -s -o /dev/null -w '%{http_code}' "https://daanaa.org${path}" || echo 000)
    log "Smoke: ${path} → ${code}"
    [ "$code" = "200" ] || { log "WARN: ${path} returned ${code}"; ok=0; }
  done
  local js_asset
  js_asset=$($SSH "find ${FRONTEND_DROPLET}/assets -name '*.js' -printf '%f\n' 2>/dev/null | head -1" 2>/dev/null || echo "")
  if [ -n "$js_asset" ]; then
    local js_code
    js_code=$(curl -s -o /dev/null -w '%{http_code}' "https://daanaa.org/assets/${js_asset}" || echo 000)
    log "Smoke: /assets/${js_asset} → ${js_code}"
    [ "$js_code" = "200" ] || { log "ERROR: JS asset 404 — will roll back"; ok=0; }
  fi
  if [ "$ok" = "1" ]; then
    $SSH "rm -rf ${FRONTEND_DROPLET}.old" >>"$LOG" 2>&1 || true
    log "✓ frontend live — all smoke checks passed; .old cleaned up"
  else
    # Roll back to previous release; preserve the failed bundle for inspection.
    $SSH "( [ -d ${FRONTEND_DROPLET} ] && mv ${FRONTEND_DROPLET} ${FRONTEND_DROPLET}.failed || true ) && \
          ( [ -d ${FRONTEND_DROPLET}.old ] && mv ${FRONTEND_DROPLET}.old ${FRONTEND_DROPLET} || true )" \
      >>"$LOG" 2>&1 || true
    die "Smoke tests failed — rolled back to previous release (.failed preserved for inspection)"
  fi
}

# ---- Orchestrate ----
preflight
if [ "$FRONTEND_ONLY" = "1" ]; then
  frontend_build
  frontend_ship
  log "===== FRONTEND-ONLY DEPLOY DONE ====="
  exit 0
fi
if [ "$SHIP_ONLY" = "0" ]; then
  snapshot
  precompute
  package
  frontend_build
fi
if [ "$BUILD_ONLY" = "0" ]; then
  ship
  swap
  frontend_ship
fi
log "===== ALL DONE ====="
log "Local :5000 was never disturbed. Snapshot+payload retained in $SCRATCH (resumable)."
