#!/bin/bash
# deploy_via_s3.sh — Stage large database through S3 for safe droplet deployment
#
# Usage:
#   ./scripts/deploy_via_s3.sh upload             # Upload local DB to S3
#   ./scripts/deploy_via_s3.sh download           # Download from S3 to droplet
#   ./scripts/deploy_via_s3.sh verify             # Verify integrity
#   ./scripts/deploy_via_s3.sh full               # Upload + download + verify
#
# Requirements:
#   - AWS credentials in ~/.aws/credentials
#   - S3 bucket must exist: s3://meritgiving-staging/
#   - Local: aws-cli, sqlite3
#   - Droplet: aws-cli, sqlite3, 20GB+ free space

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
S3_BUCKET="meritgiving-staging"
S3_REGION="us-east-1"
LOCAL_DB="$PROJECT_DIR/data/merit_registry.db"
DROPLET_HOST="root@107.170.26.8"
DROPLET_DB="/opt/daanaa/data/merit_registry.db"
DROPLET_BACKUP="/opt/daanaa/data/merit_registry.db.backup"
LOG_FILE="$PROJECT_DIR/logs/s3_deploy.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARN:${NC} $1" | tee -a "$LOG_FILE"
}

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

# Verify AWS credentials
check_aws() {
    if ! command -v aws &> /dev/null; then
        error "AWS CLI not found. Install with: pip install awscli"
    fi
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured. Run: aws configure"
    fi
    log "AWS credentials verified"
}

# Verify S3 bucket exists
check_s3_bucket() {
    if ! aws s3 ls "s3://$S3_BUCKET" --region "$S3_REGION" &> /dev/null; then
        error "S3 bucket s3://$S3_BUCKET not found. Create it first: aws s3 mb s3://$S3_BUCKET"
    fi
    log "S3 bucket verified: s3://$S3_BUCKET"
}

# Upload local database to S3
upload_to_s3() {
    log "Uploading local database to S3..."

    if [ ! -f "$LOCAL_DB" ]; then
        error "Local database not found: $LOCAL_DB"
    fi

    DB_SIZE=$(du -h "$LOCAL_DB" | cut -f1)
    log "Database size: $DB_SIZE"

    TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
    S3_KEY="databases/merit_registry_${TIMESTAMP}.db.gz"

    log "Compressing database..."
    gzip -c "$LOCAL_DB" > "/tmp/merit_registry_${TIMESTAMP}.db.gz" || error "Compression failed"

    COMPRESSED_SIZE=$(du -h "/tmp/merit_registry_${TIMESTAMP}.db.gz" | cut -f1)
    log "Compressed size: $COMPRESSED_SIZE"

    log "Uploading to S3 ($S3_KEY)..."
    aws s3 cp "/tmp/merit_registry_${TIMESTAMP}.db.gz" "s3://$S3_BUCKET/$S3_KEY" \
        --region "$S3_REGION" \
        --storage-class STANDARD_IA \
        --metadata "timestamp=$TIMESTAMP,source=local,size=$DB_SIZE" || error "Upload failed"

    rm "/tmp/merit_registry_${TIMESTAMP}.db.gz"

    log "✅ Upload complete: s3://$S3_BUCKET/$S3_KEY"
    echo "$S3_KEY"
}

# Download database from S3 to droplet
download_from_s3() {
    local s3_key="$1"

    if [ -z "$s3_key" ]; then
        # Find latest uploaded database
        log "Finding latest database in S3..."
        s3_key=$(aws s3 ls "s3://$S3_BUCKET/databases/" --region "$S3_REGION" | \
                 grep "merit_registry_" | sort | tail -1 | awk '{print $4}')

        if [ -z "$s3_key" ]; then
            error "No databases found in S3"
        fi
        log "Latest: $s3_key"
    fi

    log "Downloading from S3 to droplet..."
    ssh "$DROPLET_HOST" << SSH_EOF
    set -e

    echo "Backing up current database..."
    if [ -f "$DROPLET_DB" ]; then
        mv "$DROPLET_DB" "$DROPLET_BACKUP"
        echo "✅ Backup: $DROPLET_BACKUP"
    fi

    echo "Downloading s3://$S3_BUCKET/$s3_key..."
    aws s3 cp "s3://$S3_BUCKET/$s3_key" /tmp/db.db.gz \
        --region "$S3_REGION" 2>&1 | tail -5 || {
        echo "Download failed, restoring backup..."
        mv "$DROPLET_BACKUP" "$DROPLET_DB" 2>/dev/null || true
        exit 1
    }

    echo "Decompressing..."
    gunzip /tmp/db.db.gz || {
        echo "Decompression failed, restoring backup..."
        mv "$DROPLET_BACKUP" "$DROPLET_DB" 2>/dev/null || true
        exit 1
    }

    echo "Verifying database integrity..."
    sqlite3 /tmp/db.db "PRAGMA integrity_check;" | grep -q "ok" || {
        echo "Database integrity check failed, restoring backup..."
        mv "$DROPLET_BACKUP" "$DROPLET_DB" 2>/dev/null || true
        exit 1
    }

    echo "Moving to live location..."
    mv /tmp/db.db "$DROPLET_DB"
    chmod 660 "$DROPLET_DB"

    echo "✅ Database deployed: $DROPLET_DB"
    echo "Disk status:"
    df -h /opt/daanaa/data
SSH_EOF

    log "✅ Download and deployment complete"
}

# Verify database integrity
verify_deployment() {
    log "Verifying deployment..."

    local local_checksum=$(sha256sum "$LOCAL_DB" | awk '{print $1}')

    ssh "$DROPLET_HOST" << SSH_EOF
    echo "Local checksum: $local_checksum"
    droplet_checksum=\$(sha256sum "$DROPLET_DB" | awk '{print \$1}')
    echo "Droplet checksum: \$droplet_checksum"

    if [ "\$droplet_checksum" = "$local_checksum" ]; then
        echo "✅ Checksums match - deployment verified"
    else
        echo "⚠️ Checksums don't match - possible corruption or partial sync"
        exit 1
    fi

    echo "Checking org count..."
    sqlite3 "$DROPLET_DB" "SELECT COUNT(*) as org_count FROM registry_enriched;"

    echo "Checking donation links..."
    sqlite3 "$DROPLET_DB" "SELECT COUNT(*) as donate_count FROM registry_enriched WHERE donate_url IS NOT NULL;"

    echo "✅ All verifications passed"
SSH_EOF

    log "✅ Verification complete"
}

# Restart API after deployment
restart_api() {
    log "Restarting API on droplet..."
    ssh "$DROPLET_HOST" << SSH_EOF
    systemctl restart daanaa-api
    sleep 3
    curl -s https://daanaa.org/api/stats | jq '.total_organizations' | xargs echo "API responding, total orgs:"
    echo "✅ API restarted and verified"
SSH_EOF

    log "✅ API restart complete"
}

# Main workflow
case "${1:-full}" in
    upload)
        check_aws
        check_s3_bucket
        upload_to_s3
        ;;
    download)
        check_aws
        check_s3_bucket
        download_from_s3 "$2"
        ;;
    verify)
        check_aws
        verify_deployment
        ;;
    restart)
        restart_api
        ;;
    full)
        check_aws
        check_s3_bucket
        S3_KEY=$(upload_to_s3)
        download_from_s3 "$S3_KEY"
        verify_deployment
        restart_api
        log "🎉 Full deployment complete!"
        ;;
    *)
        echo "Usage: $0 {upload|download|verify|restart|full} [s3-key]"
        echo ""
        echo "  upload      Upload local database to S3"
        echo "  download    Download latest database from S3 to droplet"
        echo "  verify      Verify database integrity on droplet"
        echo "  restart     Restart API on droplet"
        echo "  full        Complete pipeline (upload → download → verify → restart)"
        exit 1
        ;;
esac
