#!/usr/bin/env python3
"""
Weekly backup of merit_registry.db to S3.
Runs Sunday 1 AM. Keeps 4 weekly backups (1 month rolling window).
"""
import gzip
import os
import boto3
from datetime import datetime, timezone
from pathlib import Path

DB = Path("/home/akbar/meritgiving/data/merit_registry.db")
BUCKET = "daanaa-backups"
REGION = "us-east-1"
LOG = Path("/home/akbar/meritgiving/logs/weekly_backup.log")


def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def main():
    if not DB.exists():
        log(f"✗ {DB} not found")
        return

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log(f"=== Weekly registry backup start: {ts} ===")

    s3 = boto3.client("s3", region_name=REGION)

    # Read and compress
    log(f"Compressing {DB.name}...")
    raw_size = DB.stat().st_size
    with open(DB, "rb") as f:
        gz = gzip.compress(f.read(), compresslevel=6)
    compressed_size = len(gz)
    ratio = (1 - compressed_size / raw_size) * 100
    log(f"  {raw_size / 1e9:.1f}GB → {compressed_size / 1e9:.2f}GB ({ratio:.0f}% compression)")

    # Upload
    s3_path = f"home-server/registry_{ts}.db.gz"
    try:
        s3.put_object(
            Bucket=BUCKET,
            Key=s3_path,
            Body=gz,
            ContentType="application/gzip",
            ServerSideEncryption="AES256",
        )
        log(f"✓ Uploaded s3://{BUCKET}/{s3_path}")
    except Exception as e:
        log(f"✗ Upload failed: {e}")
        return

    # Cleanup: keep only latest 4 weekly backups (1 month)
    log("Cleanup: removing old backups...")
    try:
        resp = s3.list_objects_v2(Bucket=BUCKET, Prefix="home-server/registry_")
        if "Contents" in resp:
            from operator import itemgetter
            files = sorted(resp["Contents"], key=itemgetter("LastModified"), reverse=True)
            for old_file in files[4:]:  # Keep only 4, delete rest
                s3_path = old_file["Key"]
                s3.delete_object(Bucket=BUCKET, Key=s3_path)
                log(f"  deleted {s3_path.split('/')[-1]}")
    except Exception as e:
        log(f"  cleanup warning: {e}")

    log(f"=== backup complete ===\n")


if __name__ == "__main__":
    main()
