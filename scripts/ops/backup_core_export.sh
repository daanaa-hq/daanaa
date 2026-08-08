#!/bin/bash
# backup_core_export.sh — offsite backup of the data that cannot be cheaply recreated.
#
# WHY THIS IS SMALL (2026-08-08)
# ------------------------------
# merit_registry.db is ~23GB, but almost none of that is irreplaceable:
#   org_embeddings              8.77GB  regenerable on the local GPU
#   page_cache                  3.86GB  pure cache, disposable
#   v6 assignments + indexes    ~5.0GB  scorer output, regenerable
#   FTS / classifications       ~1.5GB  derived
#   truly original human input  7 rows  (5 org_claims, 2 volunteer_interest)
# Public IRS/ProPublica data is re-downloadable. What genuinely costs money and
# time to recreate is CRAWL HOURS and GPU HOURS: 2.06M generated missions,
# 461K discovered websites, 68K verified donate links. That exports to ~80MB.
#
# So this backs up ~80MB nightly instead of 23GB, and the restore story is
# "re-ingest public data, recompute derived tables, reapply this export."
#
# WHY IT VERIFIES ITS OWN OUTPUT
# ------------------------------
# On 2026-08-08 six local backups were found unreadable ("file is not a
# database") having passed a size-only check, and three days had no backup at
# all while the log reported success. A backup that is not verified is a belief,
# not a backup. This script fails loudly rather than reporting a green run.
#
# Usage:
#   bash scripts/ops/backup_core_export.sh            # export, verify, upload, prune
#   bash scripts/ops/backup_core_export.sh --verify-restore   # also re-download and check
set -euo pipefail

BASE="$HOME/meritgiving"
DB="${MERIT_DB_PATH:-$BASE/data/merit_registry.db}"
CONFIG="$BASE/.aws-backup-config"
LOG="$BASE/logs/backup_core_export.log"
STAGE="$(mktemp -d)"
STAMP="$(date +%Y%m%d)"
KEEP_DAILY=30

mkdir -p "$(dirname "$LOG")"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
cleanup() { rm -rf "$STAGE"; }
trap cleanup EXIT
trap 'log "FATAL: failed at line $LINENO"' ERR

[ -f "$CONFIG" ] || { log "FATAL: missing $CONFIG"; exit 1; }
set -a; . "$CONFIG"; set +a
BUCKET="${S3_BUCKET:-daanaa-nonprofit-data}"
PREFIX="backups/core"

PY="$BASE/venv/bin/python3"; [ -x "$PY" ] || PY=python3

log "===== core export start ====="

# ---------------------------------------------------------------- export
EXPORT="$STAGE/daanaa_core_${STAMP}.csv.gz"
MANIFEST="$STAGE/daanaa_core_${STAMP}.manifest.json"

"$PY" - "$DB" "$EXPORT" "$MANIFEST" <<'PYEOF'
import csv, gzip, hashlib, json, sqlite3, sys, datetime

db_path, out_path, man_path = sys.argv[1], sys.argv[2], sys.argv[3]
db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)

# Enrichment that cost crawl/GPU time. EIN is the join key back into a rebuilt DB.
COLS = ["EIN", "mission", "mission_source", "website", "website_status",
        "donate_url", "donate_url_status", "donate_confidence", "volunteer_url"]

rows = 0
with gzip.open(out_path, "wt", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(COLS)
    q = (f"SELECT {','.join(COLS)} FROM registry_enriched "
         "WHERE mission IS NOT NULL OR website IS NOT NULL OR donate_url IS NOT NULL")
    for r in db.execute(q):
        w.writerow(r); rows += 1

# Irreplaceable human input: tiny, but the only data with no other source.
human = {}
for t in ("org_claims", "waitlist", "nonprofit_verifications", "nonprofit_badges",
          "volunteer_interest", "org_feedback"):
    try:
        human[t] = db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    except sqlite3.Error:
        pass

h = hashlib.sha256()
with open(out_path, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 20), b""):
        h.update(chunk)

json.dump({
    "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "source_db": db_path,
    "rows": rows,
    "columns": COLS,
    "sha256": h.hexdigest(),
    "human_input_row_counts": human,
    "note": "Enrichment-only export. Public IRS/ProPublica data and all derived "
            "tables (embeddings, v6 scores, FTS) are intentionally excluded -- "
            "they are re-ingestable or recomputable. See script header.",
}, open(man_path, "w"), indent=2)

print(f"rows={rows} sha256={h.hexdigest()[:16]} human={human}")
PYEOF

ROWS=$("$PY" -c "import json,sys;print(json.load(open('$MANIFEST'))['rows'])")
SIZE=$(stat -c%s "$EXPORT")
log "exported $ROWS rows, $((SIZE/1048576))MB"

# ---------------------------------------------------------------- verify locally
[ "$ROWS" -gt 1000000 ] || { log "FATAL: only $ROWS rows — refusing to ship a truncated export"; exit 1; }
gzip -t "$EXPORT" || { log "FATAL: gzip integrity check failed"; exit 1; }
# Parse CSV rows -- do NOT use `wc -l`. Missions contain embedded newlines, so a
# quoted row legitimately spans several physical lines (observed 2026-08-08:
# 2,059,245 lines for 2,056,834 rows). A line-count check fails every night on
# correct data, which trains people to ignore it.
PARSED=$("$PY" - "$EXPORT" <<'PYEOF'
import csv, gzip, sys
csv.field_size_limit(10_000_000)
with gzip.open(sys.argv[1], "rt", encoding="utf-8", newline="") as f:
    r = csv.reader(f); next(r)
    print(sum(1 for _ in r))
PYEOF
)
[ "$PARSED" -eq "$ROWS" ] || { log "FATAL: parsed $PARSED CSV rows != exported $ROWS"; exit 1; }
log "local verification ok (gzip valid, $PARSED CSV rows parsed)"

# ---------------------------------------------------------------- upload
aws s3 cp "$EXPORT"   "s3://$BUCKET/$PREFIX/daily/$(basename "$EXPORT")"   --only-show-errors
aws s3 cp "$MANIFEST" "s3://$BUCKET/$PREFIX/daily/$(basename "$MANIFEST")" --only-show-errors
log "uploaded to s3://$BUCKET/$PREFIX/daily/"

# Monthly copy on the 1st, kept indefinitely.
if [ "$(date +%d)" = "01" ]; then
  aws s3 cp "$EXPORT"   "s3://$BUCKET/$PREFIX/monthly/$(basename "$EXPORT")"   --only-show-errors
  aws s3 cp "$MANIFEST" "s3://$BUCKET/$PREFIX/monthly/$(basename "$MANIFEST")" --only-show-errors
  log "monthly copy retained"
fi

# ---------------------------------------------------------------- verify the REMOTE copy
# Round-trip, not just "upload returned 0": re-download and compare checksums.
RT="$STAGE/roundtrip.csv.gz"
aws s3 cp "s3://$BUCKET/$PREFIX/daily/$(basename "$EXPORT")" "$RT" --only-show-errors
LOCAL_SHA=$("$PY" -c "import json;print(json.load(open('$MANIFEST'))['sha256'])")
REMOTE_SHA=$(sha256sum "$RT" | awk '{print $1}')
[ "$LOCAL_SHA" = "$REMOTE_SHA" ] || { log "FATAL: remote checksum mismatch"; exit 1; }
log "remote round-trip verified (sha256 matches)"

# ---------------------------------------------------------------- prune dailies
aws s3 ls "s3://$BUCKET/$PREFIX/daily/" | awk '{print $4}' | grep -E '\.csv\.gz$' | sort \
  | head -n -"$KEEP_DAILY" | while read -r old; do
      [ -n "$old" ] || continue
      aws s3 rm "s3://$BUCKET/$PREFIX/daily/$old" --only-show-errors
      aws s3 rm "s3://$BUCKET/$PREFIX/daily/${old%.csv.gz}.manifest.json" --only-show-errors 2>/dev/null || true
      log "pruned $old"
    done

# ---------------------------------------------------------------- optional restore drill
if [ "${1:-}" = "--verify-restore" ]; then
  log "restore drill: loading export into a throwaway sqlite db"
  "$PY" - "$RT" <<'PYEOF'
import csv, gzip, sqlite3, sys, tempfile, os
src = sys.argv[1]
tmp = tempfile.mktemp(suffix=".db")
db = sqlite3.connect(tmp)
with gzip.open(src, "rt", encoding="utf-8") as f:
    r = csv.reader(f); cols = next(r)
    db.execute(f"CREATE TABLE core ({','.join(c+' TEXT' for c in cols)})")
    db.executemany(f"INSERT INTO core VALUES ({','.join('?'*len(cols))})", r)
db.commit()
n = db.execute("SELECT COUNT(*) FROM core").fetchone()[0]
miss = db.execute("SELECT COUNT(*) FROM core WHERE mission IS NOT NULL AND mission!=''").fetchone()[0]
web = db.execute("SELECT COUNT(*) FROM core WHERE website IS NOT NULL AND website!=''").fetchone()[0]
print(f"  restored rows={n:,} missions={miss:,} websites={web:,}")
assert n > 1_000_000, "restored row count implausibly low"
db.close(); os.unlink(tmp)
PYEOF
  log "restore drill passed"
fi

log "===== core export complete ====="
