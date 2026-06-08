#!/bin/bash
#
# Refresh the research dashboard data points.
#
# The public research page (daanaa.org/research) is a flat static page backed by
# frontend/public/research-snapshot.json — no live server connection. Run this
# whenever the underlying data changes to regenerate those data points, then
# rebuild + deploy the frontend.
#
# Usage:  bash scripts/refresh_research.sh
#
set -e

cd "$(dirname "$0")/.."
source venv/bin/activate

echo "── 1/2 · Recomputing research summary tables ─────────────────"
python3 scripts/research_summary_generator.py

echo ""
echo "── 2/2 · Exporting static snapshot ───────────────────────────"
python3 scripts/export_research_snapshot.py

echo ""
echo "Done. The fresh snapshot is at frontend/public/research-snapshot.json."
echo "Next: rebuild the frontend (npm run build) and deploy to pick up the new numbers."
