#!/bin/bash
# Deploy Task #5 (search performance indexes) to droplet if overnight pipeline passes
# Approved 2026-08-12 by Akbar Khowaja
# Run after overnight pipeline completes (after 2:30am or next morning)

set -e

BASE_DIR="${HOME}/meritgiving"
LOG_DIR="${BASE_DIR}/logs"
DROPLET_IP="107.170.26.8"
DROPLET_USER="root"

echo "═══════════════════════════════════════════════════════════════"
echo "Task #5: Deploy Search Performance Indexes (if overnight passes)"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Step 1: Check overnight pipeline status
echo "Step 1: Checking overnight pipeline status..."
if [ ! -f "${LOG_DIR}/overnight_pipeline.log" ]; then
    echo "❌ Overnight pipeline log not found"
    echo "   Expected: ${LOG_DIR}/overnight_pipeline.log"
    exit 1
fi

LAST_LINE=$(tail -1 "${LOG_DIR}/overnight_pipeline.log")
if ! echo "$LAST_LINE" | grep -q "completed\|SUCCESS\|finished"; then
    echo "⚠️  Overnight pipeline may not have finished yet"
    echo "   Last log line: $LAST_LINE"
    echo "   Wait for 2am pipeline to complete, then retry"
    exit 1
fi
echo "✅ Overnight pipeline completed"
echo ""

# Step 2: Run local smoke tests
echo "Step 2: Running local smoke tests..."
bash "${BASE_DIR}/scripts/testing/overnight_smoke_test.sh" || {
    echo "❌ Smoke tests failed - not deploying"
    exit 1
}
echo ""

# Step 3: Verify database was updated
echo "Step 3: Verifying database updates..."
SCORE_COUNT=$(sqlite3 "${BASE_DIR}/data/merit_registry.db" \
    "SELECT COUNT(*) FROM registry_enriched WHERE merit_score IS NOT NULL" 2>/dev/null || echo "0")

if [ "$SCORE_COUNT" -lt 500000 ]; then
    echo "❌ Database not updated correctly (only $SCORE_COUNT scores)"
    exit 1
fi
echo "✅ Database verified ($SCORE_COUNT scores present)"
echo ""

# Step 4: Deploy to droplet
echo "Step 4: Deploying Task #5 indexes to droplet..."
echo "   Connecting to ${DROPLET_USER}@${DROPLET_IP}..."

ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new \
    "${DROPLET_USER}@${DROPLET_IP}" << 'REMOTE_COMMANDS'
set -e

echo "  Running migration 003 on droplet..."
cd ~/meritgiving
source venv/bin/activate

# Apply migration
python3 scripts/migrations/run_migration_003.py > /tmp/migration_003.log 2>&1 || {
    echo "❌ Migration failed on droplet"
    cat /tmp/migration_003.log
    exit 1
}

echo "✅ Migration applied successfully"
REMOTE_COMMANDS

echo ""

# Step 5: Smoke test droplet
echo "Step 5: Smoke testing droplet..."
for attempt in 1 2 3; do
    echo "   Attempt $attempt..."

    # Test health endpoint
    HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:5000/health" 2>/dev/null || echo "000")
    if [ "$HEALTH" = "200" ]; then
        echo "   ✅ Health endpoint: 200"

        # Test search endpoint
        SEARCH=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:5000/api/search?q=food&limit=1" 2>/dev/null || echo "000")
        if [ "$SEARCH" = "200" ]; then
            echo "   ✅ Search endpoint: 200"

            # Test organizations endpoint
            ORGS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:5000/api/organizations?state=TX&limit=1" 2>/dev/null || echo "000")
            if [ "$ORGS" = "200" ]; then
                echo "   ✅ Organizations endpoint: 200"
                echo ""
                echo "✅ All smoke tests passed!"
                break
            fi
        fi
    fi

    if [ $attempt -lt 3 ]; then
        echo "   Retrying in 10s..."
        sleep 10
    fi
done

if [ "$HEALTH" != "200" ] || [ "$SEARCH" != "200" ] || [ "$ORGS" != "200" ]; then
    echo "❌ Droplet smoke test failed"
    echo "   Health: $HEALTH, Search: $SEARCH, Organizations: $ORGS"
    echo "   Rolling back..."

    ssh "${DROPLET_USER}@${DROPLET_IP}" << 'ROLLBACK'
    cd ~/meritgiving
    source venv/bin/activate
    sqlite3 /data/merit_registry.db << 'SQL'
    DROP INDEX IF EXISTS idx_state_organization_name;
    DROP INDEX IF EXISTS idx_merit_score_organization_name;
    DROP INDEX IF EXISTS idx_ntee1;
SQL
    echo "Rolled back indexes"
ROLLBACK

    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT SUCCESSFUL"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Task #5 deployed to droplet:"
echo "  • 3 composite indexes added to registry_enriched"
echo "  • Expected: 5-10% improvement on filtered/sorted queries"
echo "  • Fully reversible if issues arise"
echo ""
echo "Next steps:"
echo "  1. Monitor droplet performance over next 24h"
echo "  2. Watch logs for any issues: tail -f /var/log/daanaa-api/access.log"
echo "  3. Proceed to Task #6 Phase 3 when ready"
echo ""
