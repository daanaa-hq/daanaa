#!/bin/bash
# Cron wrapper for GT990 index refresh
# Runs: Sunday 1 AM via crontab
# Purpose: Fetch latest GT990 index from S3 and ingest into database

set -e

BASE_DIR="/home/akbar/meritgiving"
VENV_BIN="$BASE_DIR/venv/bin"
LOG_FILE="$BASE_DIR/logs/gt990_refresh.log"
CACHE_FILE="$BASE_DIR/data/cache/gt990_latest.csv"
S3_BUCKET="s3://gt990datalake-rawdata/Indices/990xmls"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

{
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] GT990 cron refresh started"

  # Get latest filename from S3
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] Listing S3 bucket..."
  LATEST_FILE=$("$VENV_BIN/aws" s3 ls "$S3_BUCKET/" --no-sign-request 2>/dev/null | grep '.csv' | sort | tail -1 | awk '{print $4}')

  if [ -z "$LATEST_FILE" ]; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: Could not find CSV file in S3"
    exit 1
  fi

  echo "[$(date +'%Y-%m-%d %H:%M:%S')] Found: $LATEST_FILE"

  # Download from S3
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] Downloading..."
  "$VENV_BIN/aws" s3 cp "$S3_BUCKET/$LATEST_FILE" "$CACHE_FILE" --no-sign-request 2>/dev/null

  if [ ! -f "$CACHE_FILE" ]; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: Download failed"
    exit 1
  fi

  FILE_SIZE=$(du -h "$CACHE_FILE" | cut -f1)
  ROW_COUNT=$(wc -l < "$CACHE_FILE")
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] Downloaded: $FILE_SIZE ($ROW_COUNT rows)"

  # Run ingest
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] Running ingest..."
  cd "$BASE_DIR"
  source "$VENV_BIN/activate"
  # Fixed 2026-08-21 (LESSONS.md same date): stale pre-2026-08-12-migration
  # path (real location: scripts/migrations/ingest_gt990_index.py).
  "$VENV_BIN/python3" -u scripts/migrations/ingest_gt990_index.py --index "$CACHE_FILE"

  echo "[$(date +'%Y-%m-%d %H:%M:%S')] GT990 refresh completed successfully"
} >> "$LOG_FILE" 2>&1
