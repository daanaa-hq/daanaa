#!/usr/bin/env bash
# scripts/download_irs_soi.sh
# Download / refresh IRS Statistics of Income 990 + 990-EZ extract files.
# Skips files already downloaded.  Run monthly to pick up new year releases.
#
# IRS publishes new annual extracts around October/November each year.
# Cron suggestion (1st of each month, 1 AM):
#   0 1 1 * *  /home/akbar/meritgiving/scripts/download_irs_soi.sh >> /home/akbar/meritgiving/autodev/logs/soi_download.log 2>&1

set -euo pipefail

SOI_DIR="$HOME/meritgiving/data/irs_soi"
BASE_URL="https://www.irs.gov/pub/irs-soi"
STAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

mkdir -p "$SOI_DIR"
cd "$SOI_DIR"

echo ""
echo "=========================================="
echo " IRS SOI Download — $STAMP"
echo "=========================================="

# Years and their filenames (expand as new years are published)
declare -A FILES_990=(
  [19]="19eoextract990.zip"
  [20]="20eoextract990.zip"
  [21]="21eoextract990.zip"
  [22]="22eoextract990.zip"
  [23]="23eoextract990.zip"
  [24]="24eoextract990.zip"
)
declare -A FILES_EZ=(
  [19]="19eoextractez.zip"
  [20]="20eoextractez.zip"
  [21]="21eoextractez.zip"
  [22]="22eoextractez.zip"
  [23]="23eoextractez.zip"
  [24]="24eoextract990EZ.zip"
)

downloaded=0
skipped=0

for yr in "${!FILES_990[@]}"; do
  for fname in "${FILES_990[$yr]}" "${FILES_EZ[$yr]}"; do
    if [ -f "$fname" ]; then
      echo "  EXISTS  $fname"
      ((skipped++)) || true
    else
      echo "  DOWNLOAD $fname ..."
      if curl -s -L --max-time 180 -o "$fname" "$BASE_URL/$fname"; then
        echo "    OK $(du -sh $fname | cut -f1)"
        ((downloaded++)) || true
      else
        echo "    FAILED — removing partial file"
        rm -f "$fname"
      fi
    fi
  done
done

echo ""
echo "Done — $downloaded downloaded, $skipped already present"
echo "Next: run  python3 scripts/ingest_irs_soi.py  to load new files"
echo "=========================================="
