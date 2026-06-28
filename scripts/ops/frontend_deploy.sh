#!/bin/bash
# frontend_deploy.sh — Build and deploy the React frontend to the droplet when
# frontend/src has changed since the last deploy.
#
# Stores a SHA marker on the droplet at /opt/daanaa/.frontend_sha.
# Runs nightly after the overnight pipeline (cron: 5:45am).

set -euo pipefail

BASE="$HOME/meritgiving"
FRONTEND="$BASE/frontend"
SSH_KEY="$HOME/.ssh/daanaa_do"
DROPLET="root@162.243.97.179"
SSH="ssh -i $SSH_KEY -o ConnectTimeout=15 -o StrictHostKeyChecking=accept-new $DROPLET"
REMOTE_SHA_FILE="/opt/daanaa/.frontend_sha"
REMOTE_DIST="/opt/daanaa/frontend/dist"
LOG="$BASE/logs/frontend_deploy.log"
CONFIG="$BASE/.aws-backup-config"

mkdir -p "$(dirname "$LOG")"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

[ -f "$CONFIG" ] && source "$CONFIG"

# Current SHA of frontend/src tree (changes when any source file changes)
cd "$BASE"
CURRENT_SHA=$(git rev-parse HEAD:frontend/src 2>/dev/null || echo "unknown")
if [ "$CURRENT_SHA" = "unknown" ]; then
    log "Could not determine frontend SHA. Skipping."
    exit 0
fi

# SHA deployed on droplet
DEPLOYED_SHA=$($SSH "cat $REMOTE_SHA_FILE 2>/dev/null" 2>/dev/null || echo "")

if [ "$CURRENT_SHA" = "$DEPLOYED_SHA" ]; then
    log "Frontend up to date (SHA: ${CURRENT_SHA:0:12}). Nothing to deploy."
    exit 0
fi

log "Frontend changed. Current=${CURRENT_SHA:0:12} Deployed=${DEPLOYED_SHA:0:12}"
log "Building frontend..."

cd "$FRONTEND"
npm run build >> "$LOG" 2>&1 || { log "ERROR: npm build failed"; exit 1; }

log "Build complete. Syncing to droplet..."

# Backup current dist to S3 before overwriting
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
S3_BACKUP="s3://${AWS_NONPROFIT_BUCKET:-daanaa-nonprofit-data}/backups/frontend/frontend_${TIMESTAMP}.tar.gz"
$SSH "tar -czf - -C /opt/daanaa/frontend dist 2>/dev/null" \
    | aws s3 cp - "$S3_BACKUP" --region "${AWS_REGION:-us-east-1}" 2>>"$LOG" \
    && log "S3 backup OK: $S3_BACKUP" \
    || log "WARN: S3 backup failed (continuing deploy anyway)"

rsync -avz --delete \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=accept-new" \
    "$FRONTEND/dist/" "$DROPLET:$REMOTE_DIST/" >> "$LOG" 2>&1 \
    || { log "ERROR: rsync failed"; exit 1; }

# Store new SHA on droplet (no service restart needed — droplet serves static files)
$SSH "echo '$CURRENT_SHA' > $REMOTE_SHA_FILE" 2>/dev/null

log "Deploy complete. SHA ${CURRENT_SHA:0:12} live on droplet."

# Alert
cd "$BASE"
source venv/bin/activate 2>/dev/null || true
python3 - <<PYEOF
import sys
sys.path.insert(0, '.')
from scripts.ops.mailer import send_ops_email
send_ops_email(
    "security@daanaa.org",
    "[Daanaa OK] Frontend auto-deployed",
    f"Frontend rebuilt and deployed.\n\nSHA: $CURRENT_SHA\nPrev: $DEPLOYED_SHA\nS3: $S3_BACKUP\n"
)
PYEOF
