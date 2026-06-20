#!/bin/bash
# Daanaa nightly backup — cron 02:30.
# Critical tables (claims, activity, feedback, waitlist): nightly SQL dump, 30-day retention.
# Full registry: weekly online snapshot (Sundays), 2 deep.
# Offsite: rclone to Google Drive (daanaa-backup: remote), max-age 2d on critical.
set -euo pipefail

DB="$HOME/meritgiving/data/merit_registry.db"
OUT="$HOME/meritgiving/backups"
STAMP=$(date +%Y%m%d)
CRITICAL_MIN_BYTES=400   # anything smaller than this means the dump failed
STATUS="ok"

mkdir -p "$OUT/critical" "$OUT/full"

# ── Nightly: critical tables dump ──────────────────────────────────────────
DUMP_TMP=$(mktemp)
sqlite3 "file:$DB?mode=ro" ".dump org_claims org_activity feedback waitlist" 2>&1 > "$DUMP_TMP" || true

# Detect I/O errors sqlite3 reports inline (it exits 0 even on error)
if grep -q 'ERROR' "$DUMP_TMP"; then
  echo "$(date '+%F %T') WARN critical dump contained errors — check DB integrity"
  STATUS="warn"
fi

gzip -c "$DUMP_TMP" > "$OUT/critical/critical_$STAMP.sql.gz"
rm -f "$DUMP_TMP"

CRIT_SIZE=$(stat -c%s "$OUT/critical/critical_$STAMP.sql.gz")
if [ "$CRIT_SIZE" -lt "$CRITICAL_MIN_BYTES" ]; then
  echo "$(date '+%F %T') WARN critical backup suspiciously small: ${CRIT_SIZE}B"
  STATUS="warn"
fi

find "$OUT/critical" -name 'critical_*.sql.gz' -mtime +30 -delete

# ── Weekly (Sunday): full online snapshot ──────────────────────────────────
if [ "$(date +%u)" = "7" ]; then
  TMP=$(mktemp -p "$OUT/full" full_XXXX.db)
  sqlite3 "$DB" ".backup $TMP"
  gzip -f "$TMP"
  mv "$TMP.gz" "$OUT/full/full_$STAMP.db.gz"
  gzip -t "$OUT/full/full_$STAMP.db.gz" || { echo "$(date '+%F %T') ERROR full backup gzip invalid"; STATUS="error"; }
  ls -t "$OUT/full"/full_*.db.gz 2>/dev/null | tail -n +3 | xargs -r rm
fi

# ── Offsite push (rclone → Google Drive) ───────────────────────────────────
if command -v rclone >/dev/null 2>&1 && rclone listremotes 2>/dev/null | grep -q '^daanaa-backup:'; then
  rclone copy "$OUT/critical" daanaa-backup:daanaa-backups/critical --max-age 2d -q
  rclone copy "$OUT/full" daanaa-backup:daanaa-backups/full -q
fi

CRIT_HUMAN=$(ls -lh "$OUT/critical/critical_$STAMP.sql.gz" | awk '{print $5}')
echo "$(date '+%F %T') backup $STATUS: critical=${CRIT_HUMAN}"
