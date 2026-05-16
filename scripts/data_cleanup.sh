#!/bin/bash
# =============================================================================
# scripts/data_cleanup.sh
# MeritGiving data deduplication and consolidation
#
# What this does:
#   1. Audits propublica_cache for EIN duplicates (zero-padded vs unpadded)
#   2. Archives data/index/, web_demo/, superseded scored/ versions, and
#      stale progress/enrichment files to /home/akbar/merit_archive/
#   3. Prints a final disk summary
#
# What this does NOT touch:
#   data/propublica_cache/   <- canonical EIN dataset, untouched
#   data/categories/         <- live app serving
#   data/csv/, xml/, bmf/    <- raw IRS source data
#   data/exports/            <- pipeline outputs in active use
#   data/enrichment_v2.json  <- current enrichment reference
#
# Run with --dry-run to see what would move without moving anything.
# =============================================================================

set -euo pipefail

REPO="$HOME/meritgiving"
DATA="$REPO/data"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_ROOT="/home/akbar/merit_archive"
ARCHIVE="$ARCHIVE_ROOT/$TIMESTAMP"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "=== DRY RUN MODE — nothing will be moved ==="
fi

echo ""
echo "=============================================="
echo "  MERIT Data Cleanup — $(date)"
echo "  Archive destination: $ARCHIVE"
echo "=============================================="
echo ""

# ------------------------------------------------------------------------------
# Helper: move a path to archive, creating subdirs as needed
# ------------------------------------------------------------------------------
archive_path() {
    local src="$1"
    local rel="$2"   # relative path under archive root (e.g. "index" or "data_root/enrichment_full.json")
    local dst="$ARCHIVE/$rel"

    if [[ ! -e "$src" ]]; then
        echo "  [SKIP] Not found: $src"
        return
    fi

    local size
    size=$(du -sh "$src" 2>/dev/null | cut -f1)

    if $DRY_RUN; then
        echo "  [DRY-RUN] Would move: $src  ->  $dst  ($size)"
    else
        mkdir -p "$(dirname "$dst")"
        mv "$src" "$dst"
        echo "  [MOVED]   $src  ->  $dst  ($size)"
    fi
}

# ------------------------------------------------------------------------------
# STEP 1 — EIN duplicate audit in propublica_cache
# Checks if both 010018923.json and 10018923.json exist (same EIN, two files).
# Keeps the 9-digit zero-padded version; archives the shorter one.
# ------------------------------------------------------------------------------
echo "--- STEP 1: EIN duplicate audit in propublica_cache/ ---"
CACHE="$DATA/propublica_cache"

python3 - <<'PYEOF'
import os, sys

cache_dir = os.path.expanduser("~/meritgiving/data/propublica_cache")
dry_run   = os.environ.get("MERIT_DRY_RUN", "0") == "1"
archive   = os.environ.get("MERIT_ARCHIVE", "")

seen = {}       # stripped_ein -> canonical_filename (9-digit zero-padded wins)
duplicates = [] # (loser_path, winner_path)

for fname in sorted(os.listdir(cache_dir)):
    if not fname.endswith(".json"):
        continue
    ein_raw  = fname[:-5]                  # strip .json
    ein_norm = ein_raw.lstrip("0") or "0"  # strip leading zeros for comparison

    if ein_norm in seen:
        winner = seen[ein_norm]
        loser  = ein_raw
        # prefer the 9-digit zero-padded form
        if len(winner) < len(ein_raw):
            seen[ein_norm] = ein_raw
            loser = winner
        duplicates.append((os.path.join(cache_dir, loser + ".json"),
                           os.path.join(cache_dir, seen[ein_norm] + ".json")))
    else:
        seen[ein_norm] = ein_raw

print(f"  Unique EINs in propublica_cache: {len(seen):,}")
print(f"  Duplicate pairs found:           {len(duplicates)}")

if duplicates:
    dup_archive = os.path.join(archive, "propublica_cache_dups")
    for loser_path, winner_path in duplicates:
        print(f"  DUP: keep {os.path.basename(winner_path)}  |  archive {os.path.basename(loser_path)}")
        if not dry_run:
            os.makedirs(dup_archive, exist_ok=True)
            os.rename(loser_path, os.path.join(dup_archive, os.path.basename(loser_path)))
else:
    print("  No duplicates — propublica_cache is clean.")
PYEOF

echo ""

# ------------------------------------------------------------------------------
# STEP 2 — Archive data/index/ (913 MB of year-sample pipeline artifacts)
# ------------------------------------------------------------------------------
echo "--- STEP 2: Archive data/index/ (year-sample pipeline artifacts) ---"
archive_path "$DATA/index" "index"
echo ""

# ------------------------------------------------------------------------------
# STEP 3 — Archive superseded data/scored/ versions
# Keep: all_990_scored_v4.json, v3_3_sample_1000.json
# Archive everything else in scored/
# ------------------------------------------------------------------------------
echo "--- STEP 3: Archive superseded data/scored/ versions ---"
SCORED_KEEP=("all_990_scored_v4.json" "v3_3_sample_1000.json")

for f in "$DATA/scored/"*.json; do
    fname=$(basename "$f")
    keep=false
    for k in "${SCORED_KEEP[@]}"; do
        [[ "$fname" == "$k" ]] && keep=true && break
    done
    if $keep; then
        echo "  [KEEP]    $f"
    else
        archive_path "$f" "scored/$fname"
    fi
done
echo ""

# ------------------------------------------------------------------------------
# STEP 4 — Archive web_demo/ (derived simplified lookup, 4.1 MB)
# ------------------------------------------------------------------------------
echo "--- STEP 4: Archive web_demo/ ---"
archive_path "$REPO/web_demo" "web_demo"
echo ""

# ------------------------------------------------------------------------------
# STEP 5 — Archive stale root data files
#   enrichment_full.json  <- superseded by enrichment_v2.json
#   *_progress.json       <- ephemeral build-state trackers
# ------------------------------------------------------------------------------
echo "--- STEP 5: Archive stale data/ root files ---"
archive_path "$DATA/enrichment_full.json"    "data_root/enrichment_full.json"
archive_path "$DATA/enrich_progress.json"    "data_root/enrich_progress.json"
archive_path "$DATA/ingest_progress.json"    "data_root/ingest_progress.json"
archive_path "$DATA/logo_progress.json"      "data_root/logo_progress.json"
archive_path "$DATA/xml_parse_progress.json" "data_root/xml_parse_progress.json"
echo ""

# ------------------------------------------------------------------------------
# STEP 6 — Final report
# ------------------------------------------------------------------------------
echo "--- STEP 6: Final report ---"

CACHE_COUNT=$(ls "$CACHE" | wc -l)
echo "  propublica_cache EINs remaining: $CACHE_COUNT"

if ! $DRY_RUN && [[ -d "$ARCHIVE" ]]; then
    ARCHIVE_SIZE=$(du -sh "$ARCHIVE" 2>/dev/null | cut -f1)
    echo "  Archived to:  $ARCHIVE"
    echo "  Archive size: $ARCHIVE_SIZE"
    echo ""
    echo "  Archive contents:"
    find "$ARCHIVE" -maxdepth 2 | sort | sed 's/^/    /'
fi

DATA_SIZE=$(du -sh "$DATA" 2>/dev/null | cut -f1)
echo ""
echo "  data/ current size: $DATA_SIZE"
echo ""

if $DRY_RUN; then
    echo "=== DRY RUN complete — re-run without --dry-run to apply ==="
else
    echo "=== Cleanup complete ==="
fi
