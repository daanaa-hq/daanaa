#!/bin/bash
set -e

# CRITICAL: Activate venv before ANY python imports
export HOME=/root
source /root/meritgiving/venv/bin/activate

# Now safe to run pipeline (all imports available)
cd /home/akbar/meritgiving
python3 scripts/core/overnight_pipeline.py

echo "Pipeline completed: $(date)"
