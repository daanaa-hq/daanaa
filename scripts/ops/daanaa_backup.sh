#!/bin/bash
# Daanaa nightly backup — cron 02:30.
# The irreplaceable data (claims, activity, attestations, feedback, waitlist)
# is tiny; it gets a nightly dump kept 30 days. The full 10GB registry gets a
# weekly online-snapshot (Sundays) kept 2 deep. When the founder authorizes
# rclone -> Google Drive, the push step at the bottom turns on.
set -euo pipefail

DB="$HOME/meritgiving/data/merit_registry.db"
OUT="$HOME/meritgiving/backups"
STAMP=$(date +%Y%m%d)
mkdir -p "$OUT/critical" "$OUT/full"

# Nightly: critical tables only (KB-MB scale). .backup-safe via .dump on a
# read connection; sqlite3 .dump of named tables doesn't block WAL writers.
sqlite3 "file:$DB?mode=ro" ".dump org_claims org_activity feedback waitlist org_fts_meta 2>/dev/null" 2>/dev/null \
  | gzip > "$OUT/critical/critical_$STAMP.sql.gz" || \
sqlite3 "file:$DB?mode=ro" ".dump org_claims org_activity feedback waitlist" \
  | gzip > "$OUT/critical/critical_$STAMP.sql.gz"
find "$OUT/critical" -name 'critical_*.sql.gz' -mtime +30 -delete

# Weekly (Sunday): full online snapshot, compressed, keep 2.
if [ "$(date +%u)" = "7" ]; then
  TMP=$(mktemp -p "$OUT/full" full_XXXX.db)
  sqlite3 "$DB" ".backup '$TMP'"
  gzip -f "$TMP"
  mv "$TMP.gz" "$OUT/full/full_$STAMP.db.gz"
  ls -t "$OUT/full"/full_*.db.gz | tail -n +3 | xargs -r rm
fi

# Offsite push — enabled once rclone is authorized to the founder's Drive:
if command -v rclone >/dev/null 2>&1 && rclone listremotes 2>/dev/null | grep -q '^daanaa-backup:'; then
  rclone copy "$OUT/critical" daanaa-backup:daanaa-backups/critical --max-age 2d -q
  rclone copy "$OUT/full" daanaa-backup:daanaa-backups/full -q
fi

echo "$(date '+%F %T') backup done: $(ls -lh "$OUT/critical/critical_$STAMP.sql.gz" | awk '{print $5}')"
