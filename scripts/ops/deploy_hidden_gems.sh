#!/bin/bash
# Deploy hidden gems feature to droplet
#
# Steps:
# 1. Export gem EINs from home server (WHERE is_hidden_gem=1 AND deductibility=1 AND org_status='active')
# 2. Generate SQL patch for droplet search.db (batch UPDATE by EIN)
# 3. SCP the EIN list to droplet
# 4. SSH into droplet, run the SQL patch, verify
# 5. SCP the precomputed gem files
# 6. Restart API if needed

set -e

DROPLET_IP="107.170.26.8"
DROPLET_USER="root"
DB_PATH="data/merit_registry.db"
DROPLET_DB_PATH="/data/precompute/v1/search.db"
PRECOMPUTE_DIR="/data/precompute/v1/browse/hidden_gems"
EIN_EXPORT_FILE="/tmp/hidden_gems_eins.txt"
SQL_PATCH_FILE="/tmp/hidden_gems_patch.sql"

echo "═══════════════════════════════════════════════════════════════════"
echo "  Hidden Gems Deployment"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Step 1: Export gem EINs
echo "[1/5] Exporting hidden gem EINs from home server..."
python3 - <<'PYTHON' > "$EIN_EXPORT_FILE"
import sqlite3
conn = sqlite3.connect('data/merit_registry.db')
rows = conn.execute(
    "SELECT DISTINCT EIN FROM registry_enriched "
    "WHERE is_hidden_gem=1 AND deductibility=1 AND org_status='active' "
    "ORDER BY EIN"
).fetchall()
for (ein,) in rows:
    print(ein)
conn.close()
PYTHON

GEM_COUNT=$(wc -l < "$EIN_EXPORT_FILE")
echo "  ✓ Exported $GEM_COUNT gem EINs"
echo ""

# Step 2: Generate SQL patch (batched to avoid huge single query)
echo "[2/5] Generating SQL patch for droplet search.db..."
cat > "$SQL_PATCH_FILE" <<'SQL'
-- Hidden gems feature deployment: set is_hidden_gem=1 for qualified EINs
-- Batched UPDATE to avoid massive IN clause; SQLite executes this in a transaction
BEGIN TRANSACTION;

-- Create temporary table for the EIN list (avoids huge IN clause)
CREATE TEMP TABLE gem_eins (ein TEXT PRIMARY KEY);

SQL

# Insert EINs in batches of 100
while IFS= read -r ein; do
    echo "INSERT OR IGNORE INTO gem_eins VALUES ('$ein');" >> "$SQL_PATCH_FILE"
done < "$EIN_EXPORT_FILE"

cat >> "$SQL_PATCH_FILE" <<'SQL'

-- Update orgs table
UPDATE orgs SET is_hidden_gem = 1 WHERE EIN IN (SELECT ein FROM gem_eins);

-- Verify the update
SELECT COUNT(*) as gems_set FROM orgs WHERE is_hidden_gem = 1;
SELECT COUNT(*) as expected FROM gem_eins;

COMMIT;
SQL

echo "  ✓ Generated SQL patch"
echo ""

# Step 3: Display patch preview
echo "[3/5] Patch preview:"
echo "  Total INSERTs: $GEM_COUNT"
echo "  First few EINs:"
head -5 "$EIN_EXPORT_FILE" | sed 's/^/    /'
echo "    ... ($GEM_COUNT total)"
echo ""

# Step 4: Apply patch to droplet
echo "[4/5] Applying patch to droplet $DROPLET_IP..."
scp "$SQL_PATCH_FILE" "$DROPLET_USER@$DROPLET_IP:/tmp/hidden_gems_patch.sql" > /dev/null
ssh "$DROPLET_USER@$DROPLET_IP" "sqlite3 $DROPLET_DB_PATH < /tmp/hidden_gems_patch.sql"
echo "  ✓ Patch applied"
echo ""

# Step 5: Verify droplet has correct count
echo "[5/5] Verifying gem count on droplet..."
DROPLET_GEM_COUNT=$(ssh "$DROPLET_USER@$DROPLET_IP" "sqlite3 $DROPLET_DB_PATH 'SELECT COUNT(*) FROM orgs WHERE is_hidden_gem=1;'")
echo "  Home server gems: $GEM_COUNT"
echo "  Droplet gems: $DROPLET_GEM_COUNT"
if [ "$GEM_COUNT" -eq "$DROPLET_GEM_COUNT" ]; then
    echo "  ✓ Counts match!"
else
    echo "  ⚠ Counts differ! Check the patch."
    exit 1
fi
echo ""

# Optional: Sync precomputed files
read -p "Sync precomputed gem files to droplet? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Syncing precomputed files..."
    rsync -avz --delete precompute_output/browse/hidden_gems/ \
        "$DROPLET_USER@$DROPLET_IP:$PRECOMPUTE_DIR/" \
        --exclude='*.tmp'
    echo "✓ Sync complete"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "  ✓ Hidden gems deployment complete!"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "Next: Monitor the droplet API for proper gem serving:"
echo "  curl 'https://daanaa.org/api/organizations?hidden_gem=1&page=1'"
echo ""

# Cleanup
rm "$EIN_EXPORT_FILE" "$SQL_PATCH_FILE"
