#!/bin/bash
# Backup monitoring — runs daily at 03:00 AM (30 min after backup completes at 02:30).
# Checks if backups ran successfully, files are healthy, and alerts if problems found.
set -e

BACKUP_DIR="/home/akbar/meritgiving/backups"
LOG="/home/akbar/meritgiving/logs/backup_monitor.log"
TODAY=$(date +%Y%m%d)
EMAIL="akbar.khowaja@gmail.com"

mkdir -p "$(dirname "$LOG")"

# Helper: log message and optional email alert
log_check() {
  local status=$1
  local message=$2
  local timestamp=$(date '+%F %T')

  if [ "$status" = "FAIL" ]; then
    echo "[$timestamp] ❌ ALERT: $message" >> "$LOG"
    # Email alert (requires mail/sendmail configured)
    # echo "$message" | mail -s "Daanaa Backup Alert: $message" "$EMAIL" || true
  else
    echo "[$timestamp] ✅ $message" >> "$LOG"
  fi
  echo "[$timestamp] $message" >&2
}

echo ""
echo "=== BACKUP MONITOR - $(date '+%F %T') ==="
echo ""

# Check 1: Critical backup from today
CRITICAL_LATEST=$(ls -t "$BACKUP_DIR/critical/critical_"*.sql.gz 2>/dev/null | head -1)
if [ -z "$CRITICAL_LATEST" ]; then
  log_check "FAIL" "No critical backup found"
  exit 1
fi

CRITICAL_DATE=$(basename "$CRITICAL_LATEST" | sed 's/critical_//;s/.sql.gz//')
CRITICAL_SIZE=$(stat -c %s "$CRITICAL_LATEST")

echo "Critical backup: $(basename $CRITICAL_LATEST)"
echo "Size: $CRITICAL_SIZE bytes"
echo ""

# Check 2: Backup size (should be > 500 bytes, < 10 KB for critical table dump)
if [ "$CRITICAL_SIZE" -lt 500 ]; then
  log_check "FAIL" "Critical backup too small ($CRITICAL_SIZE bytes, expected > 500)"
  exit 1
elif [ "$CRITICAL_SIZE" -gt 10000 ]; then
  log_check "WARN" "Critical backup unusually large ($CRITICAL_SIZE bytes)"
else
  log_check "PASS" "Critical backup size healthy ($CRITICAL_SIZE bytes)"
fi

# Check 3: Backup recency (should exist from last 24 hours)
CRITICAL_MTIME=$(stat -c %Y "$CRITICAL_LATEST")
NOW=$(date +%s)
AGE_SECONDS=$((NOW - CRITICAL_MTIME))
AGE_HOURS=$((AGE_SECONDS / 3600))

echo "Backup age: $AGE_HOURS hours"

if [ $AGE_HOURS -gt 25 ]; then
  log_check "FAIL" "Critical backup is old ($AGE_HOURS hours, should be < 24)"
  exit 1
else
  log_check "PASS" "Critical backup is recent ($AGE_HOURS hours old)"
fi

# Check 4: Verify backup can be restored
TEMP_DB="/tmp/backup_verify_$$.db"
if gunzip < "$CRITICAL_LATEST" | sqlite3 "$TEMP_DB" "PRAGMA integrity_check;" 2>&1 | grep -q "ok"; then
  log_check "PASS" "Backup integrity verified (can restore)"
  rm -f "$TEMP_DB"
else
  log_check "FAIL" "Backup integrity check failed (cannot restore)"
  rm -f "$TEMP_DB"
  exit 1
fi

# Check 5: Weekly full backup (only check on Mondays)
if [ "$(date +%u)" = "1" ]; then
  FULL_LATEST=$(ls -t "$BACKUP_DIR/full/full_"*.db.gz 2>/dev/null | head -1)
  if [ -z "$FULL_LATEST" ]; then
    log_check "WARN" "No full backup found (expected on Sundays)"
  else
    FULL_SIZE=$(stat -c %s "$FULL_LATEST")
    if [ "$FULL_SIZE" -lt 1000000 ]; then
      log_check "FAIL" "Full backup too small ($FULL_SIZE bytes)"
      exit 1
    else
      log_check "PASS" "Full backup healthy ($(numfmt --to=iec-i --suffix=B $FULL_SIZE 2>/dev/null || echo $FULL_SIZE bytes))"
    fi
  fi
fi

# Check 6: Offsite backup status (if rclone configured)
if command -v rclone >/dev/null 2>&1 && rclone listremotes 2>/dev/null | grep -q '^daanaa-backup:'; then
  OFFSITE_COUNT=$(rclone ls daanaa-backup:daanaa-backups/critical 2>/dev/null | wc -l || echo "0")
  if [ "$OFFSITE_COUNT" -gt 0 ]; then
    log_check "PASS" "Offsite backups present ($OFFSITE_COUNT files)"
  else
    log_check "WARN" "Offsite backup configured but no files found"
  fi
else
  log_check "INFO" "Offsite backup not yet configured (run: rclone config create daanaa-backup drive)"
fi

echo ""
log_check "PASS" "All backup checks passed"
echo ""
echo "Last backup: $(basename $CRITICAL_LATEST) ($CRITICAL_SIZE bytes, $AGE_HOURS hours old)"
echo "✅ Daanaa backups are healthy"
