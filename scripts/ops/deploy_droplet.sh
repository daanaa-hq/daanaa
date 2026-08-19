#!/bin/bash
#
# Droplet deployment script for pre-computed results.
# Receives archive, verifies, extracts, health checks, and performs atomic swap.
# Run on droplet as: bash /opt/daanaa/scripts/deploy_droplet.sh /opt/daanaa/staging/precompute_*.tar.gz
#

set -e

ARCHIVE="$1"
CHECKSUM="${ARCHIVE}.sha256"
DATA_DIR="/data/precompute"
BACKUP_DIR="/data/backups"
API_SERVICE="daanaa-api"

if [ -z "$ARCHIVE" ] || [ ! -f "$ARCHIVE" ]; then
    echo "ERROR: Archive not found: $ARCHIVE"
    echo "Usage: $0 /path/to/precompute_*.tar.gz"
    exit 1
fi

if [ ! -f "$CHECKSUM" ]; then
    echo "ERROR: Checksum file not found: $CHECKSUM"
    exit 1
fi

echo "========== DROPLET DEPLOYMENT START =========="
echo "Started at: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. Verify checksum
echo "Step 1/5: Verifying checksum..."
cd "$(dirname "$ARCHIVE")"
if ! sha256sum -c "$(basename "$CHECKSUM")"; then
    echo "ERROR: Checksum verification failed"
    exit 1
fi
echo "✓ Checksum verified"
echo ""

# 2. Extract to staging
echo "Step 2/5: Extracting archive..."
STAGING_DIR="$(mktemp -d)"
tar -xzf "$ARCHIVE" -C "$STAGING_DIR"
echo "✓ Extracted to $STAGING_DIR"
echo ""

# 3. Health check
echo "Step 3/5: Running health checks..."
# Check required files exist
for file in browse content faiss_index.bin ein_map.json.gz; do
    if [ ! -e "$STAGING_DIR/$file" ]; then
        echo "ERROR: Missing $file"
        rm -rf "$STAGING_DIR"
        exit 1
    fi
done

# Try to load a few browse files
if ! python3 -c "
import gzip, json
import random
import os
categories = os.listdir('$STAGING_DIR/browse')
random.shuffle(categories)
for cat in categories[:3]:
    states = os.listdir('$STAGING_DIR/browse/' + cat)
    if states:
        f = '$STAGING_DIR/browse/' + cat + '/' + states[0]
        with gzip.open(f, 'rt') as fp:
            data = json.load(fp)
            print(f'✓ {cat}/{states[0]}: {len(data[\"organizations\"])} orgs')
"; then
    echo "ERROR: Browse file validation failed"
    rm -rf "$STAGING_DIR"
    exit 1
fi

# Try to load FAISS index (optional if faiss not installed)
if [ -f "$STAGING_DIR/faiss_index.bin" ]; then
    python3 -c "
try:
    import faiss
    try:
        index = faiss.read_index('$STAGING_DIR/faiss_index.bin')
        print(f'✓ FAISS index loaded: {index.ntotal} vectors')
    except Exception as e:
        print(f'ERROR: Failed to load FAISS index: {e}')
        exit(1)
except ImportError:
    print('⚠️  FAISS not installed (optional); skipping index validation')
" || {
        # Non-zero exit only if FAISS is available and validation failed
        if python3 -c "import faiss" 2>/dev/null; then
            echo "ERROR: FAISS validation failed"
            rm -rf "$STAGING_DIR"
            exit 1
        fi
    }
fi

echo "✓ All health checks passed"
echo ""

# 4. Atomic swap
echo "Step 4/5: Performing atomic swap..."

# Stop API
echo "  Stopping API service..."
sudo systemctl stop $API_SERVICE || true

# Create backup directory if needed
mkdir -p "$BACKUP_DIR"

# Swap directories: v1 → v0 (backup), v2 (staging) → v1 (live)
if [ -d "$DATA_DIR/v1" ]; then
    echo "  Backing up v1 → v0..."
    rm -rf "$DATA_DIR/v0" 2>/dev/null || true
    mv "$DATA_DIR/v1" "$DATA_DIR/v0"
fi

echo "  Promoting v2 (staging) → v1 (live)..."
mv "$STAGING_DIR" "$DATA_DIR/v1"

# Preserve search.db: the precompute payload does not include it (it is built
# and shipped separately by rebuild_droplet_search_db.py). Without this step
# every deploy silently killed keyword search until someone re-shipped the DB.
if [ ! -f "$DATA_DIR/v1/search.db" ] && [ -f "$DATA_DIR/v0/search.db" ]; then
    echo "  Carrying search.db forward from v0 (payload ships none)..."
    cp "$DATA_DIR/v0/search.db" "$DATA_DIR/v1/search.db"
fi

echo "✓ Atomic swap complete"
echo ""

# 5. Restart and verify
echo "Step 5/5: Restarting API..."
sudo systemctl start $API_SERVICE

# Wait for service to be ready
sleep 3

if ! curl -s http://localhost:5000/health | grep -q '"status"'; then
    echo "ERROR: API health check failed after restart"
    echo "Rolling back..."
    sudo systemctl stop $API_SERVICE
    rm -rf "$DATA_DIR/v1"
    mv "$DATA_DIR/v0" "$DATA_DIR/v1"
    sudo systemctl start $API_SERVICE
    exit 1
fi

echo "✓ API restarted successfully"
echo ""

# Summary
echo "========== DEPLOYMENT COMPLETE =========="
echo "Completed at: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "Status:"
echo "  Live data: $DATA_DIR/v1"
echo "  Backup: $DATA_DIR/v0 (7 days old)"
echo "  Archive: $ARCHIVE"
echo ""
echo "Rollback command (if needed):"
echo "  systemctl stop $API_SERVICE && rm -rf $DATA_DIR/v1 && mv $DATA_DIR/v0 $DATA_DIR/v1 && systemctl start $API_SERVICE"
echo ""
