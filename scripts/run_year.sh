#!/bin/bash
# Usage: bash run_year.sh 2021 10000
YEAR=$1
SIZE=${2:-10000}
source ~/meritgiving/venv/bin/activate
python ~/meritgiving/scripts/py/download_year.py "$YEAR" "$SIZE"
