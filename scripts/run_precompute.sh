#!/bin/bash
#
# Master orchestration script for pre-computed results.
# Runs on home server weekly (Sunday ~22:00).
# Outputs compressed files ready to upload to droplet.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MERITGIVING_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_BASE="$MERITGIVING_DIR/precompute_output"
ARCHIVE_DIR="$MERITGIVING_DIR/precompute_archive"

cd "$MERITGIVING_DIR"

echo "========== PRE-COMPUTE ORCHESTRATION START =========="
echo "Started at: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Activate venv
source venv/bin/activate

# Create output directories
mkdir -p "$OUTPUT_BASE" "$ARCHIVE_DIR"

# 1. Browse results
echo "Phase 1/4: Pre-computing browse results..."
python3 scripts/precompute_browse.py
if [ $? -ne 0 ]; then
  echo "ERROR: precompute_browse.py failed"
  exit 1
fi
echo ""

# 2. Org details (from browse files — no DB required)
echo "Phase 2a/4: Pre-computing org detail pages from browse data..."
python3 scripts/precompute_orgs_from_browse.py
if [ $? -ne 0 ]; then
  echo "ERROR: precompute_orgs_from_browse.py failed"
  exit 1
fi
echo ""

echo "Phase 2b/4: Computing similar orgs (location-aware: NTEECC + city/state + tags)..."
python3 scripts/precompute_similar_orgs.py
if [ $? -ne 0 ]; then
  echo "ERROR: precompute_similar_orgs.py failed"
  exit 1
fi
echo ""

# 3. Content pages
echo "Phase 3/4: Pre-computing content pages..."
python3 scripts/precompute_content.py
if [ $? -ne 0 ]; then
  echo "ERROR: precompute_content.py failed"
  exit 1
fi
echo ""

# 4. FAISS index (requires GPU if available)
echo "Phase 4/4: Building FAISS index..."
python3 scripts/build_faiss_index.py
if [ $? -ne 0 ]; then
  echo "ERROR: build_faiss_index.py failed"
  exit 1
fi
echo ""

# Archive and compress
echo "Packaging files for upload..."
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
ARCHIVE_NAME="precompute_${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="$ARCHIVE_DIR/$ARCHIVE_NAME"

cd "$OUTPUT_BASE"
tar --exclude='precompute_output' -czf "$ARCHIVE_PATH" .
cd "$MERITGIVING_DIR"

ARCHIVE_SIZE=$(du -sh "$ARCHIVE_PATH" | awk '{print $1}')
echo "Archive created: $ARCHIVE_PATH ($ARCHIVE_SIZE)"

# Create checksum
CHECKSUM_PATH="${ARCHIVE_PATH}.sha256"
sha256sum "$ARCHIVE_PATH" > "$CHECKSUM_PATH"
echo "Checksum: $(cat $CHECKSUM_PATH)"

# Summary
echo ""
echo "========== PRE-COMPUTE COMPLETE =========="
echo "Completed at: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "Output:"
du -sh "$OUTPUT_BASE"/*
echo ""
echo "Ready for upload:"
echo "  Archive: $ARCHIVE_PATH"
echo "  Size: $ARCHIVE_SIZE"
echo "  Checksum: $CHECKSUM_PATH"
echo ""
echo "Next step: Upload to droplet with:"
echo "  scp $ARCHIVE_PATH root@162.243.97.179:/opt/daanaa/staging/"
echo "  scp $CHECKSUM_PATH root@162.243.97.179:/opt/daanaa/staging/"
echo ""
