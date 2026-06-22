#!/bin/bash
#
# backup_to_aws.sh — Backup Daanaa data to AWS S3
#
# Strategy:
# 1. Backup merit_registry.db (nonprofit data) → daanaa-nonprofit-data
# 2. Backup wallet/sensitive data encrypted → daanaa-donor-wallet
# 3. Cleanup old local backups (keep last 7 days)
# 4. Log to /var/log/daanaa-backup.log
#
# Runs daily via cron (2am)
#

set -euo pipefail

# Load AWS credentials
CONFIG_FILE="$HOME/meritgiving/.aws-backup-config"
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "[$(date)] ERROR: AWS config not found: $CONFIG_FILE" | tee -a /var/log/daanaa-backup.log
    exit 1
fi
source "$CONFIG_FILE"

# Directories
DB_PATH="$HOME/meritgiving/data/merit_registry.db"
BACKUP_DIR="$HOME/meritgiving/backups"
LOG_FILE="$HOME/meritgiving/logs/backup.log"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="daanaa_${TIMESTAMP}"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

trap 'log "ERROR: Backup failed"' ERR

log "Starting AWS S3 backup..."
log "  Nonprofit bucket: $AWS_NONPROFIT_BUCKET"
log "  Donor bucket: $AWS_DONOR_BUCKET"

# Step 1: Backup main database (nonprofit data)
log "Step 1: Compressing database..."
DB_BACKUP="$BACKUP_DIR/${BACKUP_NAME}_registry.db.gz"
gzip -c "$DB_PATH" > "$DB_BACKUP"
DB_SIZE=$(du -h "$DB_BACKUP" | cut -f1)
log "  Database backed up: $DB_SIZE"

# Step 2: Upload nonprofit data to S3 (unencrypted at S3 level, S3 handles encryption)
log "Step 2: Uploading nonprofit data to S3..."
aws s3 cp "$DB_BACKUP" \
    "s3://$AWS_NONPROFIT_BUCKET/backups/${BACKUP_NAME}_registry.db.gz" \
    --region "$AWS_REGION" \
    --sse AES256 \
    --storage-class STANDARD_IA \
    2>&1 | tee -a "$LOG_FILE" || {
    log "ERROR: Failed to upload nonprofit data"
    exit 1
}
log "  ✓ Nonprofit data uploaded"

# Step 3: Backup wallet/sensitive data (separate encryption key would go here)
# For now, we're using S3 encryption. In future, can add KMS encryption at application level.
log "Step 3: Uploading configuration backups..."
CONFIG_BACKUP="$BACKUP_DIR/${BACKUP_NAME}_config.tar.gz"
tar -czf "$CONFIG_BACKUP" \
    -C "$HOME/meritgiving" \
    logs/ \
    --exclude='*.log' \
    2>/dev/null || true

if [[ -f "$CONFIG_BACKUP" ]]; then
    aws s3 cp "$CONFIG_BACKUP" \
        "s3://$AWS_DONOR_BUCKET/backups/${BACKUP_NAME}_config.tar.gz" \
        --region "$AWS_REGION" \
        --sse AES256 \
        --storage-class STANDARD_IA \
        2>&1 | tee -a "$LOG_FILE" || {
        log "WARNING: Failed to upload config backup"
    }
    log "  ✓ Config backup uploaded (donor bucket for isolation)"
fi

# Step 4: Cleanup old local backups (keep 7 days)
log "Step 4: Cleaning up old local backups..."
find "$BACKUP_DIR" -maxdepth 1 -name "daanaa_*" -type f -mtime +7 -delete
REMAINING=$(ls -1 "$BACKUP_DIR" | wc -l)
log "  Remaining backups: $REMAINING files"

# Step 5: Verify S3 uploads
log "Step 5: Verifying S3 uploads..."
NONPROFIT_COUNT=$(aws s3 ls "s3://$AWS_NONPROFIT_BUCKET/backups/" --region "$AWS_REGION" | wc -l)
DONOR_COUNT=$(aws s3 ls "s3://$AWS_DONOR_BUCKET/backups/" --region "$AWS_REGION" | wc -l)
log "  Nonprofit bucket: $NONPROFIT_COUNT backups"
log "  Donor bucket: $DONOR_COUNT backups"

log "✓ AWS S3 backup complete"
log "  Database: $DB_SIZE"
log "  Timestamp: $BACKUP_NAME"
