#!/usr/bin/env python3
"""Mirror backups/full and backups/critical to S3 as a second, independent
offsite copy alongside the existing Google Drive (rclone) push in
scripts/ops/daanaa_backup.sh.

Deliberately does NOT take its own database backup — daanaa_backup.sh
already does that (SQLite online-backup API, weekly full + nightly
critical-table dump) and has run reliably for weeks. This script only
uploads whatever daanaa_backup.sh already produced, so we get a second
cloud provider for disaster recovery without doubling the compression/
backup work or maintaining two independent backup-taking pipelines.

Called as the last step of daanaa_backup.sh (fail-loud, same as the rest
of that script) — not its own cron entry.
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKUPS_DIR = Path("/home/akbar/meritgiving/backups")
BUCKET = "daanaa-backups"
KEEP_S3_DAYS = 90  # registry is reproducible from IRS/ProPublica source data;
                   # this is a disaster-recovery window, not an archive


def _load_env():
    env_path = Path("/home/akbar/meritgiving/.env")
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k, v)


def main():
    _load_env()
    import boto3

    s3 = boto3.client(
        "s3",
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )

    uploaded = 0
    for subdir, prefix in (("full", "home-server/full/"), ("critical", "home-server/critical-sql/")):
        local_dir = BACKUPS_DIR / subdir
        if not local_dir.exists():
            continue
        existing = {
            obj["Key"].rsplit("/", 1)[-1]
            for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=prefix)
            for obj in page.get("Contents", [])
        }
        for f in local_dir.iterdir():
            if not f.is_file() or f.name in existing:
                continue
            s3.upload_file(str(f), BUCKET, f"{prefix}{f.name}", ExtraArgs={"ServerSideEncryption": "AES256"})
            print(f"Uploaded s3://{BUCKET}/{prefix}{f.name}")
            uploaded += 1

    # Prune S3 copies past retention (local pruning already handled by daanaa_backup.sh)
    cutoff = datetime.now(timezone.utc) - timedelta(days=KEEP_S3_DAYS)
    removed = 0
    for prefix in ("home-server/full/", "home-server/critical-sql/"):
        for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=prefix):
            for obj in page.get("Contents", []):
                if obj["LastModified"] < cutoff:
                    s3.delete_object(Bucket=BUCKET, Key=obj["Key"])
                    removed += 1

    print(f"s3_mirror_backups: uploaded={uploaded} pruned={removed}")


if __name__ == "__main__":
    sys.exit(main())
