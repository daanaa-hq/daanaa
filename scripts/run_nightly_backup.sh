#!/bin/bash
set -euo pipefail
cd /home/akbar/meritgiving
set -a
source .env
set +a
source venv/bin/activate
python3 scripts/nightly_backup_critical.py >> logs/s3_backup.log 2>&1
