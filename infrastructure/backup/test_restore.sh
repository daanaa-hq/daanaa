#!/bin/bash
# Test restore from backup — run monthly (1st of month, 10 AM via cron).
# Validates the REAL backups produced by scripts/ops/daanaa_backup.sh:
#   ~/meritgiving/backups/full/full_YYYYMMDD.db.gz  (online .backup snapshot, gzipped)
# These are the copies that also ship offsite to Google Drive (rclone daanaa-backup:).
#
# 2026-07-03: repointed from the retired infrastructure/backup/daily_backup.sh
# output (~/backups/merit_registry/*.tar.gz), which was stale (last good Jun 20)
# because that script's live-DB integrity check false-failed under gunicorn load.
# Testing the stale dir gave false "PASS" confidence. This validates the fresh,
# offsited snapshots instead.

set -e

BACKUP_DIR="$HOME/meritgiving/backups/full"
TEMP_RESTORE="/tmp/merit_registry_restore_test.db"

echo "═══════════════════════════════════════════════════════════"
echo "  Backup Restore Test"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Find most recent full snapshot
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/full_*.db.gz 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
  echo "ERROR: No full backups found in $BACKUP_DIR"
  echo "       (full snapshots run weekly on Sundays via daanaa_backup.sh)"
  exit 1
fi

echo "[*] Testing restore from: $(basename "$LATEST_BACKUP")"

# Decompress the snapshot to a temp DB
echo "[*] Decompressing..."
START=$(date +%s%N)
gunzip -c "$LATEST_BACKUP" > "$TEMP_RESTORE"
EXTRACT_TIME=$(($(date +%s%N) - START))
EXTRACT_MS=$((EXTRACT_TIME / 1000000))

# Verify integrity of the restored copy (static file — safe to run full check)
echo "[*] Verifying integrity..."
if ! sqlite3 "$TEMP_RESTORE" "PRAGMA integrity_check;" | grep -q "ok"; then
  echo "ERROR: Restored database failed integrity check"
  rm -f "$TEMP_RESTORE"
  exit 1
fi

# Count orgs as a sanity check that the schema + data are intact
ORG_COUNT=$(sqlite3 "$TEMP_RESTORE" "SELECT COUNT(*) FROM registry_enriched")
echo "[✓] Database valid, $ORG_COUNT orgs"

# Cleanup
rm -f "$TEMP_RESTORE"

BACKUP_AGE_H=$(( ($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")) / 3600 ))

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Test Results"
echo "═══════════════════════════════════════════════════════════"
echo "Backup file:  $(basename "$LATEST_BACKUP")"
echo "Backup age:   ${BACKUP_AGE_H} hours"
echo "Restore time: ${EXTRACT_MS}ms (target RTO: 10 min)"
# Full snapshots are weekly; warn if the newest is older than ~9 days (a missed run)
if [ "$BACKUP_AGE_H" -gt 216 ]; then
  echo "Status:       ⚠ PASS (but newest full snapshot is >9 days old — check Sunday cron)"
else
  echo "Status:       ✓ PASS"
fi
echo ""
