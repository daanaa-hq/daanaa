#!/bin/bash
# Daanaa nightly backup — cron 02:30 (founder ruling 2026-07-11: fail loudly).
# Critical tables (claims, activity, feedback, waitlist): nightly SQL dump, 30-day retention.
# Full registry: weekly online snapshot (Sundays), 2 deep.
# Offsite: rclone to Google Drive (daanaa-backup: remote), max-age 2d on critical.
#
# GOVERNANCE: This script must FAIL LOUDLY on any error. Silent backup failures are unacceptable.
# Returns 0 only if ALL backup stages (local critical, local weekly if Sunday, offsite push) complete successfully.
# Returns nonzero on any error with descriptive logging.

set -Eeuo pipefail

DB="$HOME/meritgiving/data/merit_registry.db"
OUT="$HOME/meritgiving/backups"
ERRORLOG="$OUT/.backup_errors"
STAMP=$(date +%Y%m%d)
TIMESTAMP=$(date '+%F %T')
CRITICAL_MIN_BYTES=400   # anything smaller than this means the dump failed

trap 'on_error' ERR
on_error() {
  local line=$1
  local exit_code=$?
  echo "$TIMESTAMP ERROR backup failed at line $line (exit code $exit_code)" | tee -a "$ERRORLOG"
  exit "$exit_code"
}

mkdir -p "$OUT/critical" "$OUT/full"

# ── Nightly: critical tables dump ──────────────────────────────────────────
echo "$TIMESTAMP INFO starting critical backup..."
DUMP_TMP=$(mktemp)
trap "rm -f '$DUMP_TMP'" RETURN

sqlite3 "file:$DB?mode=ro" ".dump org_claims org_activity feedback waitlist" 2>&1 > "$DUMP_TMP" || {
  echo "$TIMESTAMP ERROR sqlite3 failed to dump critical tables" | tee -a "$ERRORLOG"
  exit 1
}

# Detect I/O errors sqlite3 reports inline (it exits 0 even on error)
if grep -q 'ERROR' "$DUMP_TMP"; then
  echo "$TIMESTAMP ERROR critical dump contained SQL errors — check DB integrity" | tee -a "$ERRORLOG"
  exit 1
fi

gzip -c "$DUMP_TMP" > "$OUT/critical/critical_$STAMP.sql.gz" || {
  echo "$TIMESTAMP ERROR gzip failed on critical dump" | tee -a "$ERRORLOG"
  exit 1
}

CRIT_SIZE=$(stat -c%s "$OUT/critical/critical_$STAMP.sql.gz")
if [ "$CRIT_SIZE" -lt "$CRITICAL_MIN_BYTES" ]; then
  echo "$TIMESTAMP ERROR critical backup suspiciously small: ${CRIT_SIZE}B" | tee -a "$ERRORLOG"
  exit 1
fi

echo "$TIMESTAMP INFO critical backup successful: $(ls -lh "$OUT/critical/critical_$STAMP.sql.gz" | awk '{print $5}')"
find "$OUT/critical" -name 'critical_*.sql.gz' -mtime +30 -delete

# ── Weekly (Sunday): full online snapshot ──────────────────────────────────
if [ "$(date +%u)" = "7" ]; then
  echo "$TIMESTAMP INFO starting full weekly backup..."
  TMP=$(mktemp -p "$OUT/full" full_XXXX.db)

  sqlite3 "$DB" ".backup $TMP" || {
    echo "$TIMESTAMP ERROR sqlite3 full backup failed" | tee -a "$ERRORLOG"
    rm -f "$TMP"
    exit 1
  }

  gzip -f "$TMP" || {
    echo "$TIMESTAMP ERROR gzip failed on full backup" | tee -a "$ERRORLOG"
    rm -f "$TMP" "$TMP.gz"
    exit 1
  }

  mv "$TMP.gz" "$OUT/full/full_$STAMP.db.gz" || {
    echo "$TIMESTAMP ERROR failed to move full backup to final location" | tee -a "$ERRORLOG"
    exit 1
  }

  # Verify integrity
  gzip -t "$OUT/full/full_$STAMP.db.gz" || {
    echo "$TIMESTAMP ERROR full backup gzip invalid (integrity check failed)" | tee -a "$ERRORLOG"
    exit 1
  }

  echo "$TIMESTAMP INFO full backup successful: $(ls -lh "$OUT/full/full_$STAMP.db.gz" | awk '{print $5}')"
  ls -t "$OUT/full"/full_*.db.gz 2>/dev/null | tail -n +3 | xargs -r rm
fi

# ── Offsite push (rclone → Google Drive) ───────────────────────────────────
# GOVERNANCE: These checks must not be silent.
echo "$TIMESTAMP INFO verifying offsite backup prerequisites..."

if ! command -v rclone >/dev/null 2>&1; then
  echo "$TIMESTAMP ERROR rclone is not installed (offsite backup cannot proceed)" | tee -a "$ERRORLOG"
  echo "ACTION: install rclone (apt install rclone) or disable offsite backup" | tee -a "$ERRORLOG"
  exit 1
fi

if ! rclone listremotes 2>&1 | grep -q '^daanaa-backup:'; then
  echo "$TIMESTAMP ERROR rclone remote 'daanaa-backup:' is not configured" | tee -a "$ERRORLOG"
  echo "ACTION: run 'rclone config' and configure the daanaa-backup remote" | tee -a "$ERRORLOG"
  exit 1
fi

# Test offsite connectivity before pushing data
echo "$TIMESTAMP INFO testing offsite connectivity..."
if ! rclone about daanaa-backup: >/dev/null 2>&1; then
  echo "$TIMESTAMP ERROR offsite authentication or connectivity failed (rclone about daanaa-backup: failed)" | tee -a "$ERRORLOG"
  echo "ACTION: verify Google Drive credentials (rclone config) and network access" | tee -a "$ERRORLOG"
  exit 1
fi

# Push critical backups
echo "$TIMESTAMP INFO pushing critical backups to Google Drive..."
if ! rclone copy "$OUT/critical" daanaa-backup:daanaa-backups/critical --max-age 2d -q 2>&1 | tee -a "$ERRORLOG"; then
  echo "$TIMESTAMP ERROR rclone failed to push critical backups" | tee -a "$ERRORLOG"
  exit 1
fi

# Push full backups (if they exist)
if [ -n "$(ls -1 "$OUT/full" 2>/dev/null)" ]; then
  echo "$TIMESTAMP INFO pushing full backups to Google Drive..."
  if ! rclone copy "$OUT/full" daanaa-backup:daanaa-backups/full -q 2>&1 | tee -a "$ERRORLOG"; then
    echo "$TIMESTAMP ERROR rclone failed to push full backups" | tee -a "$ERRORLOG"
    exit 1
  fi
fi

# Verify offsite files actually exist
echo "$TIMESTAMP INFO verifying offsite backup files exist..."
OFFSITE_FILES=$(rclone ls daanaa-backup:daanaa-backups/ 2>&1 | wc -l)
if [ "$OFFSITE_FILES" -lt 1 ]; then
  echo "$TIMESTAMP ERROR no backup files found on offsite after push" | tee -a "$ERRORLOG"
  exit 1
fi

echo "$TIMESTAMP INFO offsite push verified ($OFFSITE_FILES files on Google Drive)"

# ── Success ────────────────────────────────────────────────────────────────
CRIT_HUMAN=$(ls -lh "$OUT/critical/critical_$STAMP.sql.gz" | awk '{print $5}')
echo "$TIMESTAMP SUCCESS backup complete: critical=${CRIT_HUMAN}, offsite=pushed, all verifications passed"
exit 0
