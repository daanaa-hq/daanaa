#!/bin/bash
# sync_droplet_api.sh — Auto-deploy scripts/droplet_api.py when it diverges from
# what's running on the droplet. Backs up the old version to S3 first.
#
# Runs nightly at 1:30am. Only restarts gunicorn when a change is detected.
# AWS bucket: daanaa-nonprofit-data (consistent with backup_to_aws.sh).

set -euo pipefail

BASE="$HOME/meritgiving"
LOCAL_API="$BASE/scripts/droplet_api.py"
REMOTE_API="/opt/daanaa/droplet_api.py"
SSH_KEY="$HOME/.ssh/daanaa_do"
DROPLET="root@162.243.97.179"
SSH="ssh -i $SSH_KEY -o ConnectTimeout=15 -o StrictHostKeyChecking=accept-new $DROPLET"
LOG="$BASE/logs/sync_droplet_api.log"
CONFIG="$BASE/.aws-backup-config"

mkdir -p "$(dirname "$LOG")"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

# Load AWS creds
[ -f "$CONFIG" ] && source "$CONFIG"

log "Checking droplet_api.py drift..."

LOCAL_MD5=$(md5sum "$LOCAL_API" | awk '{print $1}')
REMOTE_MD5=$($SSH "md5sum $REMOTE_API 2>/dev/null | awk '{print \$1}'" 2>/dev/null || echo "missing")

if [ "$LOCAL_MD5" = "$REMOTE_MD5" ]; then
    log "No change (md5: $LOCAL_MD5). Nothing to deploy."
    exit 0
fi

log "Change detected. Local=$LOCAL_MD5 Remote=$REMOTE_MD5"

# Backup old version to S3 before overwriting
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
S3_BACKUP="s3://${AWS_NONPROFIT_BUCKET:-daanaa-nonprofit-data}/backups/droplet_api/droplet_api_${TIMESTAMP}.py"

if $SSH "test -f $REMOTE_API"; then
    log "Backing up old version to $S3_BACKUP..."
    $SSH "cat $REMOTE_API" | aws s3 cp - "$S3_BACKUP" \
        --region "${AWS_REGION:-us-east-1}" 2>>"$LOG" \
        && log "S3 backup OK: $S3_BACKUP" \
        || log "WARN: S3 backup failed (continuing deploy anyway)"
fi

# Deploy new version
log "Deploying new droplet_api.py..."
rsync -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=accept-new" \
    --checksum --backup --suffix=".prev" \
    "$LOCAL_API" "$DROPLET:$REMOTE_API" 2>>"$LOG"

# Restart service
log "Restarting daanaa service..."
$SSH "systemctl restart daanaa" 2>>"$LOG"

# Verify it came back
sleep 3
if $SSH "systemctl is-active daanaa" 2>/dev/null | grep -q "^active$"; then
    STATUS="OK"
    log "Service restarted successfully."
else
    STATUS="FAILED"
    log "ERROR: Service did not restart cleanly."
fi

# Send alert via ops mailer
cd "$BASE"
source venv/bin/activate 2>/dev/null || true
python3 - <<PYEOF
import sys
sys.path.insert(0, '.')
from scripts.ops.mailer import send_ops_email
status = "$STATUS"
subject = f"[Daanaa {'OK' if status=='OK' else 'ALERT'}] droplet_api.py auto-deployed"
body = f"""droplet_api.py was updated and deployed automatically.

Local md5:  $LOCAL_MD5
Remote was: $REMOTE_MD5
S3 backup:  $S3_BACKUP
Service:    {status}

Deploy log: $LOG
"""
send_ops_email("security@daanaa.org", subject, body)
print(f"Alert sent (status={status})")
PYEOF

[ "$STATUS" = "FAILED" ] && exit 1 || exit 0
