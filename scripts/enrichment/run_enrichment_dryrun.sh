#!/bin/bash
# Test enrichment on a subset of orgs before full 1.7M run
#
# This script runs the enrichment pipeline in dry-run mode, which:
# - Processes the specified number of orgs
# - Generates cause tags and website suggestions
# - Performs quality measurement
# - **DOES NOT write any results to the database** (safe to run in production)
#
# Usage:
#   ./scripts/run_enrichment_dryrun.sh              # Default: 10K orgs
#   ./scripts/run_enrichment_dryrun.sh 1000         # Custom: 1K orgs
#   ./scripts/run_enrichment_dryrun.sh 100 2        # Custom: 100 orgs, 2 workers

set -e

BASE_DIR="/home/akbar/meritgiving"
VENV_PYTHON="$BASE_DIR/venv/bin/python3"

# Parameters
MAX_ORGS="${1:-10000}"    # Default: 10K orgs for testing
WORKERS="${2:-4}"          # Default: 4 parallel workers

echo "========================================="
echo "Enrichment Pipeline Dry-Run"
echo "========================================="
echo "Max orgs:  $MAX_ORGS"
echo "Workers:   $WORKERS"
echo "Mode:      Dry-run (no database writes)"
echo "========================================="
echo

cd "$BASE_DIR"

# Activate virtual environment
if [ ! -f "venv/bin/activate" ]; then
    echo "Error: venv not found at $BASE_DIR/venv"
    exit 1
fi

source venv/bin/activate

# Run enrichment in dry-run mode
echo "Starting enrichment batch..."
$VENV_PYTHON scripts/enrich_batch.py \
    --dry-run \
    --max-orgs "$MAX_ORGS" \
    --workers "$WORKERS"

echo
echo "✓ Dry-run complete."
echo "  Check logs/enrich_batch_YYYYMMDD.log for details"
echo
