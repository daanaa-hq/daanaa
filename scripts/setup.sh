#!/bin/bash
# MERIT Data Pipeline — Phase 0 Setup Script
# Run this first to prepare the environment

set -euo pipefail

echo "============================================================"
echo "  MERIT Data Pipeline — Phase 0 Setup"
echo "============================================================"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Create directory structure
echo "[1/5] Creating directory structure..."
mkdir -p data/{raw/{propublica,irs_990_xml,irs_bmf},csv,propublica_cache,scripts,logs}
echo "  ✓ Directories created"

# Install Python dependencies
echo ""
echo "[2/5] Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q requests urllib3 boto3 botocore pandas numpy tqdm
echo "  ✓ Dependencies installed"

# Verify imports
echo ""
echo "[3/5] Verifying imports..."
python3 -c "import requests, boto3, pandas, csv, json, xml.etree.ElementTree; print('  ✓ All required modules available')"

# Copy scripts to data/scripts
echo ""
echo "[4/5] Copying scripts..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/scripts/"*.py data/scripts/ 2>/dev/null || true
cp "$SCRIPT_DIR/scripts/requirements.txt" data/scripts/ 2>/dev/null || true
echo "  ✓ Scripts ready"

# Display disk space
echo ""
echo "[5/5] Checking disk space..."
AVAILABLE=$(df -BG "$(pwd)" | awk 'NR==2 {print $4}' | tr -d 'G')
echo "  Available disk space: ${AVAILABLE}GB"
if [ "$AVAILABLE" -lt 150 ]; then
    echo "  ⚠ WARNING: Less than 150GB available. Pipeline may fail."
else
    echo "  ✓ Sufficient disk space"
fi

echo ""
echo "============================================================"
echo "  Setup Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Review the execution plan: cat EXECUTION_PLAN.md"
echo "  2. Start Workstream C (reference data):"
echo "     python data/scripts/workstream_c_irs_bmf.py --download --parse"
echo "  3. Start Workstream A (ProPublica) in terminal 1:"
echo "     python data/scripts/workstream_a_propublica.py"
echo "  4. Start Workstream B (IRS S3) in terminal 2:"
echo "     python data/scripts/workstream_b_irs_s3.py --years 2019,2020,2021,2022,2023"
echo "  5. Run Workstream D (master merge) after A+B+C complete:"
echo "     python data/scripts/workstream_d_master_merge.py --validate --output"
echo ""
echo "  Or use the orchestrator for sequential execution:"
echo "     python data/scripts/orchestrator.py --all"
echo ""
