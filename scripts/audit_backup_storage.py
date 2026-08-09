#!/usr/bin/env python3
"""Read-only audit of backup storage and retention pressure.

This tool inventories backup-like files, SQLite WAL/SHM files, filesystem
capacity, age bands, and duplicate candidates. It never deletes, moves,
compresses, or modifies files and does not contact remote backup providers.

Examples:
  python3 scripts/audit_backup_storage.py
  python3 scripts/audit_backup_storage.py --root ~/meritgiving --json
  python3 scripts/audit_backup_storage.py --root ~/meritgiving --hash
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


BACKUP_SUFFIXES = (".db", ".db.gz", ".sql.gz", ".sqlite", ".sqlite3", ".bak")
BACKUP_WORDS = ("backup", "snapshot", "checkpoint", "restore", "hourly", "daily", "full", "critical")
SKIP_DIRS = {".git", "node_modules", "frontend/node_modules", "venv", ".venv"}


def bytes_human(value: int) -> str:
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    number = float(value)
    for unit in units:
        if number < 1024 or unit == units[-1]:
            return f"{number:.1f} {unit}"
        number /= 1024
    return f"{value} B"


def is_backup_candidate(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith(BACKUP_SUFFIXES) or any(word in name for word in BACKUP_WORDS)


def walk_files(root: Path):
    for base, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if str(Path(base, d).relative_to(root)) not in SKIP_DIRS]
        for name in names:
            path = Path(base, name)
            try:
                if path.is_file() and not path.is_symlink():
                    yield path
            except OSError:
                continue


def digest(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def sqlite_probe(path: Path) -> dict:
    result = {"sqlite": False, "integrity": "not_checked", "error": None}
    if path.name.endswith((".gz", ".sql.gz")):
        return result
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=2)
        result["sqlite"] = bool(conn.execute("SELECT 1 FROM sqlite_master LIMIT 1").fetchone())
        if result["sqlite"]:
            result["integrity"] = conn.execute("PRAGMA quick_check").fetchone()[0]
        conn.close()
    except Exception as exc:  # audit must continue across unrelated files
        result["error"] = str(exc)
    return result


def audit(root: Path, do_hash: bool, verify_sqlite: bool) -> dict:
    if not root.is_dir():
        raise FileNotFoundError(root)
    files = []
    for path in walk_files(root):
        try:
            stat = path.stat()
        except OSError:
            continue
        if is_backup_candidate(path):
            item = {
                "path": str(path),
                "relative_path": str(path.relative_to(root)),
                "bytes": stat.st_size,
                "mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "age_days": round((datetime.now(timezone.utc).timestamp() - stat.st_mtime) / 86400, 2),
            }
            if verify_sqlite:
                item.update(sqlite_probe(path))
            files.append(item)

    duplicate_groups = []
    by_size = defaultdict(list)
    for item in files:
        by_size[item["bytes"]].append(item)
    for size, same_size in by_size.items():
        if len(same_size) < 2:
            continue
        if do_hash:
            by_digest = defaultdict(list)
            for item in same_size:
                try:
                    by_digest[digest(Path(item["path"]))].append(item["path"])
                except OSError as exc:
                    item["hash_error"] = str(exc)
            for checksum, paths in by_digest.items():
                if len(paths) > 1:
                    duplicate_groups.append({"bytes": size, "sha256": checksum, "paths": paths})
        else:
            duplicate_groups.append({"bytes": size, "sha256": None, "paths": [x["path"] for x in same_size], "candidate_only": True})

    usage = shutil.disk_usage(root)
    by_extension = Counter(Path(x["path"]).suffix or "[none]" for x in files)
    by_age = Counter(
        "0-1d" if x["age_days"] < 1 else "1-7d" if x["age_days"] < 7 else "7-30d" if x["age_days"] < 30 else "30-90d" if x["age_days"] < 90 else "90d+"
        for x in files
    )
    wal_files = []
    for path in walk_files(root):
        if path.name.endswith(("-wal", "-shm")):
            try:
                wal_files.append({"path": str(path), "bytes": path.stat().st_size})
            except OSError:
                pass

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root.resolve()),
        "filesystem": {
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
            "free_percent": round(usage.free / usage.total * 100, 2),
        },
        "backup_candidates": {
            "count": len(files),
            "total_bytes": sum(x["bytes"] for x in files),
            "by_extension": dict(by_extension),
            "by_age": dict(by_age),
            "files": sorted(files, key=lambda x: x["bytes"], reverse=True),
            "duplicate_groups": duplicate_groups,
        },
        "sqlite_sidecars": {
            "count": len(wal_files),
            "total_bytes": sum(x["bytes"] for x in wal_files),
            "files": sorted(wal_files, key=lambda x: x["bytes"], reverse=True),
        },
    }


def print_report(report: dict, warning_percent: float) -> None:
    fs = report["filesystem"]
    backups = report["backup_candidates"]
    print(f"Backup storage audit: {report['root']}")
    print(f"Filesystem: {bytes_human(fs['free_bytes'])} free ({fs['free_percent']:.2f}%) of {bytes_human(fs['total_bytes'])}")
    print(f"Backup candidates: {backups['count']} files, {bytes_human(backups['total_bytes'])}")
    print(f"Age bands: {backups['by_age']}")
    print(f"SQLite WAL/SHM: {report['sqlite_sidecars']['count']} files, {bytes_human(report['sqlite_sidecars']['total_bytes'])}")
    if backups["duplicate_groups"]:
        print(f"Duplicate candidates: {len(backups['duplicate_groups'])} groups (hash-confirmed only with --hash)")
    print("\nLargest backup candidates:")
    for item in backups["files"][:15]:
        print(f"  {bytes_human(item['bytes']):>12}  {item['age_days']:>7.1f}d  {item['relative_path']}")
    if fs["free_percent"] < warning_percent:
        print(f"\nWARNING: free space is below {warning_percent:.1f}%. No files were changed.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only backup storage audit")
    parser.add_argument("--root", type=Path, default=Path.home() / "meritgiving")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--hash", action="store_true", help="SHA-256 same-size candidates; can be expensive")
    parser.add_argument("--verify-sqlite", action="store_true", help="Run quick_check on uncompressed SQLite candidates")
    parser.add_argument("--warning-free-percent", type=float, default=15.0)
    args = parser.parse_args()
    report = audit(args.root, args.hash, args.verify_sqlite)
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report, args.warning_free_percent)
    return 2 if report["filesystem"]["free_percent"] < args.warning_free_percent else 0


if __name__ == "__main__":
    raise SystemExit(main())
