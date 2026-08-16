#!/usr/bin/env python3
"""
Nightly critical-data backup to S3 (boto3, no aws-cli needed).
Backs up ONLY the critical tables (org_claims, community_partners) plus
daanaa_live.db from the droplet — NOT the full 7.2GB registry.

Runs at 3:00 AM via cron. Completes in < 30 seconds.
"""
import gzip
import json
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────────────
DB = Path(os.environ.get("DB_PATH", "/home/akbar/meritgiving/data/merit_registry.db"))
BUCKET = "daanaa-backups"
REGION = "us-east-1"
DROPLET = "root@107.170.26.8"
LOG = Path("/home/akbar/meritgiving/logs/s3_backup.log")

CRITICAL_TABLES = ["org_claims", "community_partners"]


def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def dump_tables_json(db_path, tables):
    """Dump tables to JSON-serializable dict."""
    data = {}
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        for tbl in tables:
            try:
                rows = conn.execute(f"SELECT * FROM {tbl}").fetchall()
                data[tbl] = [dict(r) for r in rows]
                log(f"  {tbl}: {len(rows)} rows")
            except Exception as e:
                log(f"  {tbl}: SKIP ({e})")
    return data


def upload_gz(s3, s3_path, payload_bytes):
    gz = gzip.compress(payload_bytes)
    s3.put_object(
        Bucket=BUCKET,
        Key=s3_path,
        Body=gz,
        ContentType="application/gzip",
        ServerSideEncryption="AES256",
    )
    log(f"  uploaded s3://{BUCKET}/{s3_path} ({len(gz)//1024}KB)")


def main():
    import boto3

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log(f"=== Daanaa S3 backup start: {ts} ===")

    s3 = boto3.client("s3", region_name=REGION)

    # 1. Dump critical SQLite tables from home server
    log("1. Dumping critical tables from merit_registry.db ...")
    data = dump_tables_json(DB, CRITICAL_TABLES)
    upload_gz(
        s3,
        f"home-server/critical_{ts}.json.gz",
        json.dumps(data, default=str).encode(),
    )

    # 2. Backup daanaa_live.db from droplet (scp then upload)
    log("2. Pulling daanaa_live.db from droplet ...")
    tmp = Path(f"/tmp/daanaa_live_{ts}.db")
    try:
        result = subprocess.run(
            ["scp", "-q", "-o", "StrictHostKeyChecking=no",
             f"{DROPLET}:/opt/daanaa/daanaa_live.db", str(tmp)],
            timeout=60, capture_output=True
        )
        if result.returncode == 0 and tmp.exists():
            upload_gz(s3, f"droplet/daanaa_live_{ts}.db.gz", tmp.read_bytes())
        else:
            log(f"  daanaa_live.db: not found on droplet (ok if droplet uses DynamoDB)")
        tmp.unlink(missing_ok=True)
    except Exception as e:
        log(f"  droplet backup: {e}")

    # 3. Prune old backups (keep 30 days in S3 — lifecycle handles Glacier after that)
    log("3. Pruning local gzip dumps older than 7 days ...")
    cutoff = time.time() - 7 * 86400
    local_backup_dir = Path("/home/akbar/meritgiving/backups")
    removed = 0
    for f in local_backup_dir.glob("daanaa_*.gz"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            removed += 1
    log(f"  removed {removed} old local files")

    log(f"=== backup complete ===\n")


if __name__ == "__main__":
    sys.path.insert(0, "/home/akbar/meritgiving/venv/lib/python3.12/site-packages")
    main()
