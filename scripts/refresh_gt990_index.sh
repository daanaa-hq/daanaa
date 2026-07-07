#!/bin/bash
# Refresh GT990 index from public S3 bucket (no AWS CLI required)
# Run: bash scripts/refresh_gt990_index.sh

set -e
cd "$(dirname "$0")/.."

LOG="logs/gt990_refresh.log"
CACHE="data/cache/gt990_latest.csv"
S3_BASE="https://gt990datalake-rawdata.s3.amazonaws.com/Indices/990xmls"

{
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] GT990 refresh started"

  # List available CSV files from S3 and get the latest
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] Fetching S3 index..."
  LATEST_FILE=$(curl -s "${S3_BASE}/" | grep -oP '(?<=<Key>)[^<]*\.csv(?=</Key>)' | sort | tail -1)

  if [ -z "$LATEST_FILE" ]; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: Could not find any CSV files in S3"
    exit 1
  fi

  echo "[$(date +'%Y-%m-%d %H:%M:%S')] Latest file: $LATEST_FILE"

  # Download the file
  DOWNLOAD_URL="${S3_BASE}/${LATEST_FILE}"
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] Downloading from $DOWNLOAD_URL"

  curl -s -L --max-time 600 -o "$CACHE" "$DOWNLOAD_URL"

  if [ ! -f "$CACHE" ]; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: Download failed"
    exit 1
  fi

  FILE_SIZE=$(du -h "$CACHE" | cut -f1)
  ROW_COUNT=$(wc -l < "$CACHE")
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] Downloaded: $FILE_SIZE ($ROW_COUNT rows)"

  # Run the ingestion script
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] Running ingest script..."
  source venv/bin/activate
  python3 -u scripts/ingest_gt990_index.py --index "$CACHE"

  echo "[$(date +'%Y-%m-%d %H:%M:%S')] GT990 refresh completed successfully"
} >> "$LOG" 2>&1
