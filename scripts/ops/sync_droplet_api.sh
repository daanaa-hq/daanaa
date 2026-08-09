#!/bin/bash
# sync_droplet_api.sh — Auto-deploy scripts/droplet_api.py when it diverges from
# what's running on the droplet. Backs up the old version to S3 first.
#
# Runs nightly at 1:30am. Only restarts gunicorn when a change is detected.
# AWS bucket: daanaa-nonprofit-data (consistent with backup_to_aws.sh).
#
# Hardened 2026-07-05 after the SPA-fallback outage: alerts now fire on ANY
# failure (ERR trap, venv mailer), ssh/rsync retry once, and a post-deploy
# smoke test rolls back to the .prev file if real pages stop rendering.

set -euo pipefail

BASE="$HOME/meritgiving"
LOCAL_API="$BASE/scripts/droplet_api.py"
REMOTE_API="/opt/daanaa/droplet_api.py"
SSH_KEY="$HOME/.ssh/daanaa_do_cron"  # passphrase-free automation key (see LESSONS.md 2026-07-05)
DROPLET="root@107.170.26.8"
SSH="ssh -i $SSH_KEY -o ConnectTimeout=15 -o BatchMode=yes -o StrictHostKeyChecking=accept-new $DROPLET"
LOG="$BASE/logs/sync_droplet_api.log"
CONFIG="$BASE/.aws-backup-config"

mkdir -p "$(dirname "$LOG")"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

# Alert that actually delivers: venv python + repo cwd. The old bare-python3
# heredoc failed the mailer import under cron and swallowed stderr, so deploy
# failures were silent for days.
alert() {
    ( cd "$BASE" && ./venv/bin/python3 - "$1" "$2" <<'PYEOF'
import sys
sys.path.insert(0, '.')
from scripts.ops.mailer import send_ops_email
send_ops_email("security@daanaa.org", sys.argv[1], sys.argv[2])
PYEOF
    ) || log "WARN: alert email failed to send"
}

trap 'log "FATAL(trap): failed at line $LINENO"; alert "[Daanaa ALERT] droplet_api deploy FAILED" "sync_droplet_api.sh died at line $LINENO. Log: $LOG"' ERR

# Retry wrapper: the 2026-07-03..05 cron runs died on transient
# publickey/connection errors that succeeded manually minutes later.
retry() {
    "$@" && return 0
    log "Retrying in 30s: $*"
    sleep 30
    "$@"
}

# Load AWS creds
[ -f "$CONFIG" ] && source "$CONFIG"

log "Checking droplet_api.py drift..."

# Wrong-file guard (2026-07-06, second occurrence of this failure): the root
# droplet_api.py / daanaa_api.py home-API variants query v4_scores,
# org_embeddings, and registry_enriched.subsection — schema that exists only in
# the home merit_registry.db, never in the droplet search.db contract. Shipping
# one takes down every DB-backed route. Refuse before anything else runs.
if grep -qE "v4_scores|org_embeddings" "$LOCAL_API"; then
    log "REFUSING DEPLOY: $LOCAL_API references home-only schema (v4_scores/org_embeddings). Wrong file — see LESSONS.md 2026-07-06."
    alert "[Daanaa ALERT] droplet_api deploy REFUSED" "scripts/droplet_api.py references v4_scores/org_embeddings — the home-API variant has overwritten the lean droplet API in the repo. Not deployed. See LESSONS.md 2026-07-06."
    exit 1
fi

LOCAL_MD5=$(md5sum "$LOCAL_API" | awk '{print $1}')
REMOTE_MD5=$(retry $SSH "md5sum $REMOTE_API 2>/dev/null | awk '{print \$1}'" || echo "missing")

if [ "$LOCAL_MD5" = "$REMOTE_MD5" ]; then
    log "No change (md5: $LOCAL_MD5). Nothing to deploy."
    exit 0
fi

log "Change detected. Local=$LOCAL_MD5 Remote=$REMOTE_MD5"

# Backup old version to S3 before overwriting
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
S3_BACKUP="s3://${AWS_NONPROFIT_BUCKET:-daanaa-nonprofit-data}/backups/droplet_api/droplet_api_${TIMESTAMP}.py"

if ! command -v aws >/dev/null 2>&1; then
    log "WARN: aws CLI not installed — skipping S3 backup (droplet keeps ${REMOTE_API}.prev)"
elif $SSH "test -f $REMOTE_API"; then
    log "Backing up old version to $S3_BACKUP..."
    $SSH "cat $REMOTE_API" | aws s3 cp - "$S3_BACKUP" \
        --region "${AWS_REGION:-us-east-1}" 2>>"$LOG" \
        && log "S3 backup OK: $S3_BACKUP" \
        || log "WARN: S3 backup failed (continuing deploy anyway)"
fi

# Deploy new version
log "Deploying new droplet_api.py..."
retry rsync -e "ssh -i $SSH_KEY -o BatchMode=yes -o StrictHostKeyChecking=accept-new" \
    --checksum --backup --suffix=".prev" \
    "$LOCAL_API" "$DROPLET:$REMOTE_API" 2>>"$LOG"

# Restart service
log "Restarting daanaa service..."
$SSH "systemctl restart daanaa-api" 2>>"$LOG"

# Verify it came back. A single systemctl probe conflates a transient SSH
# refusal with a dead service (false FAILED on 2026-07-13, sshd briefly
# refused connections mid-restart) — retry, then let the public smoke test
# below be the source of truth: users see pages, not systemd units.
STATUS="FAILED"
for _attempt in 1 2 3; do
    sleep 5
    if $SSH "systemctl is-active daanaa-api" 2>/dev/null | grep -q "^active$"; then
        STATUS="OK"
        log "Service restarted successfully."
        break
    fi
    log "is-active probe attempt ${_attempt} inconclusive (service starting or SSH busy)..."
done

# Smoke test what users actually see. The 2026-07-05 outage shipped a build
# where /health was 200 but every page 500'd — service "active" is not "up".
smoke() {
    local home_body
    home_body=$(curl -sS --max-time 20 https://daanaa.org/ 2>>"$LOG" | head -c 300) || return 1
    echo "$home_body" | grep -qi '<!doctype html' || return 1
    curl -sS --max-time 20 -o /dev/null -w '%{http_code}' \
        'https://daanaa.org/api/search?q=food+bank&limit=1' 2>>"$LOG" | grep -q '^200$' || return 1
    # Directory listing route — died independently of /api/search in the
    # 2026-07-06 incident ("no such column: subsection"), so check it too.
    curl -sS --max-time 20 -o /dev/null -w '%{http_code}' \
        'https://daanaa.org/api/organizations?state=TX&limit=1' 2>>"$LOG" | grep -q '^200$'
}

# Smoke runs UNCONDITIONALLY and decides the outcome. Previously a FAILED
# is-active probe skipped smoke AND rollback — a genuinely broken deploy
# would have been left live with only an error email.
if smoke; then
    if [ "$STATUS" != "OK" ]; then
        log "systemctl probe inconclusive but public pages serve — treating as OK."
    fi
    STATUS="OK"
else
    STATUS="FAILED"
    log "SMOKE TEST FAILED: homepage or search not serving. Rolling back to ${REMOTE_API}.prev..."
    if $SSH "test -f ${REMOTE_API}.prev && cp ${REMOTE_API}.prev $REMOTE_API && systemctl restart daanaa-api"; then
        sleep 5
        if smoke; then
            log "Rollback OK — previous version restored and serving."
        else
            log "Rollback restarted but smoke still failing — MANUAL ACTION NEEDED."
        fi
    else
        log "Rollback FAILED — no .prev on droplet or restart failed. MANUAL ACTION NEEDED."
    fi
fi

# Send outcome via ops mailer
alert "[Daanaa $( [ "$STATUS" = OK ] && echo OK || echo ALERT)] droplet_api.py auto-deploy: $STATUS" \
"droplet_api.py deploy finished with status: $STATUS

Local md5:  $LOCAL_MD5
Remote was: $REMOTE_MD5
S3 backup:  $S3_BACKUP
Smoke:      homepage doctype + /api/search 200 $( [ "$STATUS" = OK ] && echo passed || echo 'FAILED (auto-rollback attempted)')

Deploy log: $LOG
"

[ "$STATUS" = "FAILED" ] && exit 1 || exit 0
