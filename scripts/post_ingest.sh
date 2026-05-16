#!/bin/bash
# scripts/post_ingest.sh
# Run everything needed after SOI ingest completes.
# Waits for the ingest process to finish, then runs in sequence:
#   1. Mission extraction from 990 XML
#   2. Recompute peer percentiles (NTEECC + revenue band)
#   3. Restart the API
#   4. Kick off full 551K embedding job

set -e
cd "$(dirname "$0")/.."
source venv/bin/activate

LOG="logs/post_ingest_$(date +%Y%m%d_%H%M%S).log"
mkdir -p logs
exec > >(tee -a "$LOG") 2>&1

echo "========================================"
echo "MERIT post-ingest sequence"
echo "Started: $(date)"
echo "========================================"

# Wait for SOI ingest to finish
SOI_PID=$(pgrep -f "ingest_irs_soi" || true)
if [ -n "$SOI_PID" ]; then
    echo "Waiting for SOI ingest (PID $SOI_PID) to finish..."
    wait "$SOI_PID" 2>/dev/null || true
    echo "SOI ingest done at $(date)"
else
    echo "SOI ingest already finished."
fi

echo ""
echo "--- Step 1: Extract missions from 990 XML files ---"
python3 scripts/extract_990_fields.py
echo ""

echo "--- Step 1b: Enrich deductibility from BMF ---"
python3 scripts/enrich_bmf_deductibility.py
echo ""

echo "--- Step 2: Recompute peer percentiles ---"
python3 scripts/recompute_percentiles.py
echo ""

echo "--- Step 3: Restart API ---"
if [ -f restart_merit_api.sh ]; then
    bash restart_merit_api.sh
    echo "API restarted."
else
    echo "No restart script found — restart merit_api.py manually."
fi
echo ""

echo "--- Step 4: Full embedding job (551K orgs) ---"
EMBED_PID=$(pgrep -f "build_embeddings" || true)
if [ -n "$EMBED_PID" ]; then
    echo "Waiting for 100-org test (PID $EMBED_PID) to finish first..."
    wait "$EMBED_PID" 2>/dev/null || true
    echo "Test run done."
fi
echo "Starting full embedding job..."
python3 scripts/build_embeddings.py --rebuild &
FULL_EMBED_PID=$!
echo "Embedding job running in background (PID $FULL_EMBED_PID)"
echo ""

echo "========================================"
echo "Post-ingest sequence complete: $(date)"
echo "Embeddings building in background — restart API again when done."
echo "Log: $LOG"
echo "========================================"
