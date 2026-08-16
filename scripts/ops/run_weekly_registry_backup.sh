#!/bin/bash
set -euo pipefail
cd /home/akbar/meritgiving
set -a
source .env
set +a
source venv/bin/activate
python3 scripts/weekly_registry_backup.py >> logs/weekly_backup.log 2>&1
