#!/bin/bash
# Orchestrate NCCS data ingestion pipeline
# Run after agent downloads files to ~/meritgiving/data/nccs/

set -euo pipefail

REPO_ROOT="$HOME/meritgiving"
VENV_PATH="$REPO_ROOT/venv"
SCRIPTS_DIR="$REPO_ROOT/scripts"
DATA_DIR="$REPO_ROOT/data/nccs"
LOG_DIR="$REPO_ROOT/logs"

mkdir -p "$LOG_DIR"

echo "[$(date)] === Starting NCCS Data Ingestion Pipeline ==="

# Activate venv
if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo "ERROR: venv not found at $VENV_PATH"
    exit 1
fi

source "$VENV_PATH/bin/activate"
cd "$REPO_ROOT"

# Step 1: Add database columns
echo "[$(date)] Step 1: Adding NCCS columns to database..."
python3 "$SCRIPTS_DIR/add_nccs_columns.py"

# Step 2: Ingest Part VII (Compensation)
echo "[$(date)] Step 2: Ingesting Part VII (Compensation)..."
if python3 "$SCRIPTS_DIR/ingest_nccs_part_vii.py"; then
    echo "[$(date)] ✓ Part VII ingestion complete"
else
    echo "[$(date)] ⚠ Part VII ingestion failed or no files found"
fi

# Step 3: Ingest Part X (Balance Sheet)
echo "[$(date)] Step 3: Ingesting Part X (Balance Sheet)..."
if python3 "$SCRIPTS_DIR/ingest_nccs_part_x.py"; then
    echo "[$(date)] ✓ Part X ingestion complete"
else
    echo "[$(date)] ⚠ Part X ingestion failed or no files found"
fi

# Step 4: Validate results
echo "[$(date)] Step 4: Validating ingestion..."
python3 << 'PYTHON_VALIDATE'
import sqlite3
import os

db_path = os.path.expanduser("~/meritgiving/data/merit_registry.db")
db = sqlite3.connect(db_path)
db.row_factory = sqlite3.Row

# Check coverage
stats = db.execute("""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN nccs_net_assets IS NOT NULL THEN 1 ELSE 0 END) as part_x_coverage,
        SUM(CASE WHEN nccs_executive_compensation IS NOT NULL THEN 1 ELSE 0 END) as part_vii_coverage
    FROM registry_enriched
""").fetchone()

print(f"\nIngestion Results:")
print(f"  Total orgs: {stats['total']:,}")
print(f"  Part X coverage: {stats['part_x_coverage']:,} ({100*stats['part_x_coverage']/stats['total']:.1f}%)")
print(f"  Part VII coverage: {stats['part_vii_coverage']:,} ({100*stats['part_vii_coverage']/stats['total']:.1f}%)")

db.close()
PYTHON_VALIDATE

echo "[$(date)] === NCCS Data Ingestion Pipeline Complete ==="
