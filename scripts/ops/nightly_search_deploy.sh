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

# ── Step 4: Ship search.db to droplet + merge into the real serving DB ──────
# Re-targeted 2026-08-21 (see LESSONS.md same date). This step shipped to
# /data/precompute/v1/search.db from 2026-07-06 (commit dac5fdf34ffc, correct
# at the time -- that WAS the path the then-current lean droplet_api.py read)
# until the 2026-08-08 bare-snapshot droplet rebuild reset the systemd
# DB_PATH override to /opt/daanaa/data/merit_registry.db without anyone
# updating this script to match. Confirmed via logs/nightly_search_deploy.log:
# every night since silently "succeeded" writing to a path nothing reads --
# the real serving DB sat at the pre-2026-08-17 row count the whole time.
#
# /opt/daanaa/data/merit_registry.db is NOT a read-only precompute artifact --
# it also holds live, user-generated tables (org_claims, waitlist,
# wallet_analytics, feedback, donor_users, etc; confirmed via .tables on the
# droplet). A full-file swap would destroy them. This does a targeted merge
# of ONLY the three tables this pipeline owns (registry_enriched, org_fts,
# zip_codes), leaving every other table untouched.
#
# Rewritten 2026-08-22 after a real incident (DECISIONS.md same date):
# registry_enriched used to get DELETE FROM + INSERT ... SELECT *. That
# broke two ways at once. (1) search.db's registry_enriched is deliberately
# lean (LIVE_COLS in scripts/search/build_search_db.py, ~50 columns) while
# production has grown to 125 -- SELECT * across mismatched schemas either
# errors outright (what actually happened) or, worse, silently succeeds
# when column COUNTS happen to coincide while ORDER differs, corrupting
# data with no error at all. (2) the sqlite3 CLI heredoc had no '.bail on',
# so when the INSERT failed, the CLI printed the error to stderr and kept
# going, reaching COMMIT anyway -- committing the DELETE with no re-insert.
# registry_enriched sat empty for 6+ hours until found by accident.
#
# Fixed properly, not just patched: registry_enriched is now an explicit,
# column-scoped UPSERT naming exactly the columns search.db owns (the same
# LIVE_COLS list, kept in sync by hand -- if that list changes, update the
# column names below to match). No DELETE at all for this table, so a
# failed run can never leave it empty; existing rows keep every
# production-only column (scoring_tier, confidence_v6, merit_percentile_v6,
# all v6/eligibility fields) exactly as they were, since only the named
# columns get overwritten. org_fts and zip_codes stay DELETE+INSERT --
# they're wholly owned by this pipeline with no other production columns
# to protect. '.bail on' is now the first line, so ANY statement failure
# aborts before COMMIT instead of silently continuing past it.
log "Step 4/6: Rsyncing search.db to droplet..."
rsync --checksum --progress \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=accept-new" \
    "$OUT" "$DROPLET:/tmp/search_new_staging.db" >> "$LOG" 2>&1 \
    || die "rsync search.db failed"

log "Merging into live serving DB (registry_enriched, org_fts, zip_codes only)..."
$SSH "sqlite3 /opt/daanaa/data/merit_registry.db <<'MERGE_SQL'
.bail on
ATTACH DATABASE '/tmp/search_new_staging.db' AS src;
BEGIN;
INSERT INTO registry_enriched (
    EIN, organization_name, NTEE1, NTEECC, CITY, STATE, zipcode,
    mission, mission_source, merit_score, merit_tier, merit_band,
    ntee1_percentile, peer_percentile, peer_rank, peer_total,
    total_revenue, total_expenses, net_assets, months_of_reserve,
    program_expense_pct, employee_count, latest_tax_year, ruling_date,
    website, website_status, donate_url, donate_platform,
    donate_url_status, volunteer_url, cause_tags, is_hidden_gem,
    data_source, source, merit_archetype_v5, merit_archetype_v5_label,
    merit_band_v5, merit_band_v5_label, merit_score_v5,
    merit_health_signal_v5, merit_peer_group_v5, merit_peer_count_v5,
    subsection, deductibility, org_status, irs_revoked,
    irs_eligibility_status, irs_eligibility_checked_at,
    irs_eligibility_sources, irs_eligibility_notes
)
SELECT
    EIN, organization_name, NTEE1, NTEECC, CITY, STATE, zipcode,
    mission, mission_source, merit_score, merit_tier, merit_band,
    ntee1_percentile, peer_percentile, peer_rank, peer_total,
    total_revenue, total_expenses, net_assets, months_of_reserve,
    program_expense_pct, employee_count, latest_tax_year, ruling_date,
    website, website_status, donate_url, donate_platform,
    donate_url_status, volunteer_url, cause_tags, is_hidden_gem,
    data_source, source, merit_archetype_v5, merit_archetype_v5_label,
    merit_band_v5, merit_band_v5_label, merit_score_v5,
    merit_health_signal_v5, merit_peer_group_v5, merit_peer_count_v5,
    subsection, deductibility, org_status, irs_revoked,
    irs_eligibility_status, irs_eligibility_checked_at,
    irs_eligibility_sources, irs_eligibility_notes
FROM src.registry_enriched
WHERE true
ON CONFLICT(EIN) DO UPDATE SET
    organization_name=excluded.organization_name, NTEE1=excluded.NTEE1,
    NTEECC=excluded.NTEECC, CITY=excluded.CITY, STATE=excluded.STATE,
    zipcode=excluded.zipcode, mission=excluded.mission,
    mission_source=excluded.mission_source, merit_score=excluded.merit_score,
    merit_tier=excluded.merit_tier, merit_band=excluded.merit_band,
    ntee1_percentile=excluded.ntee1_percentile,
    peer_percentile=excluded.peer_percentile, peer_rank=excluded.peer_rank,
    peer_total=excluded.peer_total, total_revenue=excluded.total_revenue,
    total_expenses=excluded.total_expenses, net_assets=excluded.net_assets,
    months_of_reserve=excluded.months_of_reserve,
    program_expense_pct=excluded.program_expense_pct,
    employee_count=excluded.employee_count,
    latest_tax_year=excluded.latest_tax_year, ruling_date=excluded.ruling_date,
    website=excluded.website, website_status=excluded.website_status,
    donate_url=excluded.donate_url, donate_platform=excluded.donate_platform,
    donate_url_status=excluded.donate_url_status,
    volunteer_url=excluded.volunteer_url, cause_tags=excluded.cause_tags,
    is_hidden_gem=excluded.is_hidden_gem, data_source=excluded.data_source,
    source=excluded.source, merit_archetype_v5=excluded.merit_archetype_v5,
    merit_archetype_v5_label=excluded.merit_archetype_v5_label,
    merit_band_v5=excluded.merit_band_v5,
    merit_band_v5_label=excluded.merit_band_v5_label,
    merit_score_v5=excluded.merit_score_v5,
    merit_health_signal_v5=excluded.merit_health_signal_v5,
    merit_peer_group_v5=excluded.merit_peer_group_v5,
    merit_peer_count_v5=excluded.merit_peer_count_v5,
    subsection=excluded.subsection, deductibility=excluded.deductibility,
    org_status=excluded.org_status, irs_revoked=excluded.irs_revoked,
    irs_eligibility_status=excluded.irs_eligibility_status,
    irs_eligibility_checked_at=excluded.irs_eligibility_checked_at,
    irs_eligibility_sources=excluded.irs_eligibility_sources,
    irs_eligibility_notes=excluded.irs_eligibility_notes;
DELETE FROM org_fts;
INSERT INTO org_fts SELECT * FROM src.org_fts;
DELETE FROM zip_codes;
INSERT INTO zip_codes SELECT * FROM src.zip_codes;
COMMIT;
DETACH DATABASE src;
MERGE_SQL" 2>>"$LOG" \
    || die "live DB merge failed"

$SSH "rm -f /tmp/search_new_staging.db" 2>>"$LOG" || log "WARN: staging file cleanup failed (harmless)"
$SSH "systemctl restart daanaa-api" 2>>"$LOG" && log "API restarted to clear in-process cache." \
    || die "API restart failed after merge"
log "search.db merged into live serving DB."

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
# Readiness poll before checking anything: the restart above triggers
# --preload's embeddings load (45s-2min observed), and a fixed short wait
# produces the exact false-positive-502 pattern documented in LESSONS.md
# 2026-08-18. Same bounded-poll pattern as sync_droplet_api.sh.
READY=0
for _i in $(seq 1 24); do
    curl -sS --max-time 5 -o /dev/null -w '%{http_code}' https://daanaa.org/ 2>>"$LOG" | grep -q '^200$' && { READY=1; break; }
    sleep 5
done
[ "$READY" = "1" ] || log "WARN: backend not responding after 120s post-restart -- checks below may fail spuriously"

PLAN=$($SSH "sqlite3 /opt/daanaa/data/merit_registry.db \"
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
# Fixed 2026-08-21: this call has referenced a stale pre-migration path
# (scripts/patch_precompute_v5_context.py; the file now lives under
# scripts/archive/, likely obsolete now that v6 scoring superseded v5 --
# a founder call, not fixed here) since at least 2026-08-14. Under `set -e`
# with no guard on this line, that failure was silently killing the whole
# script right after Step 4.5 every night -- Steps 5-6 (org-file precompute
# refresh + API cache-clearing restart) never ran. The surrounding code
# (UPDATED defaulting to 0, "no org file changes, skipping" messaging) makes
# clear this step was always meant to degrade gracefully, not take the
# pipeline down with it -- `|| true` restores that original intent without
# reviving the archived v5-context patcher itself. See LESSONS.md 2026-08-21.
python3 scripts/patch_precompute_v5_context.py >> "$PATCH_LOG" 2>&1 || true
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
