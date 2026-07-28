#!/usr/bin/env python3
"""Refresh and verify the IRS eligibility boundary used by Daanaa.

This job is deliberately separate from scoring.  It answers one question:
"May Daanaa present this organization as currently eligible for a charitable
donation?"  It requires all three public IRS signals:

* EO Business Master File: subsection 03 and deductibility 1
* Publication 78: current EIN match with an accepted deductibility code
* Auto-revocation list: no current revocation without reinstatement

The default mode is read-only.  ``--apply`` is an explicit, transactional
reconciliation of the existing ``registry_enriched.deductibility`` and
revocation fields.  It never changes scores, peer assignments, missions, or
organization-provided data.

The source files are kept outside the database so a failed download cannot
partially change production data.  A stale or malformed source blocks the
job rather than weakening the eligibility boundary.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


PUB78_URL = "https://apps.irs.gov/pub/epostcard/data-download-pub78.zip"
REVOCATION_URL = "https://apps.irs.gov/pub/epostcard/data-download-revocation.zip"
BMF_URLS = [
    "https://www.irs.gov/pub/irs-soi/eo1.csv",
    "https://www.irs.gov/pub/irs-soi/eo2.csv",
    "https://www.irs.gov/pub/irs-soi/eo3.csv",
    "https://www.irs.gov/pub/irs-soi/eo4.csv",
]
PUB78_CODES = {"PC", "POF", "SC", "IND", "GOV"}
MAX_SOURCE_AGE_HOURS = 168
MIN_BMF_BYTES = 100 * 1024 * 1024
MIN_ZIP_BYTES = 100 * 1024


@dataclass
class Source:
    name: str
    path: Path
    url: str
    records: int = 0
    sha256: str = ""


def normalize_ein(value: str) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits if len(digits) == 9 else ""


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path, minimum_bytes: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Daanaa-IRS-Eligibility-Refresh/1.0"},
    )
    with urllib.request.urlopen(request, timeout=300) as response, partial.open("wb") as out:
        shutil.copyfileobj(response, out, length=1024 * 1024)
    if partial.stat().st_size < minimum_bytes:
        partial.unlink(missing_ok=True)
        raise RuntimeError(f"IRS source is unexpectedly small: {url}")
    partial.replace(destination)


def extract_first_text(zip_path: Path, destination: Path) -> Path:
    with zipfile.ZipFile(zip_path) as archive:
        candidates = [name for name in archive.namelist() if name.lower().endswith((".txt", ".csv"))]
        if not candidates:
            raise RuntimeError(f"No text file found in {zip_path}")
        member = candidates[0]
        target = destination / Path(member).name
        with archive.open(member) as source, target.open("wb") as out:
            shutil.copyfileobj(source, out, length=1024 * 1024)
    if target.stat().st_size == 0:
        raise RuntimeError(f"Extracted IRS source is empty: {target}")
    return target


def source_age_hours(path: Path) -> float:
    return (datetime.now(timezone.utc).timestamp() - path.stat().st_mtime) / 3600


def load_registry_eins(db_path: Path) -> set[str]:
    with sqlite3.connect(db_path) as db:
        return {
            normalize_ein(row[0])
            for row in db.execute("SELECT EIN FROM registry_enriched")
            if normalize_ein(row[0])
        }


def parse_pub78(path: Path, registry_eins: set[str]) -> tuple[set[str], int, int]:
    eligible: set[str] = set()
    records = malformed = 0
    with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
        for row in csv.reader(fh, delimiter="|"):
            if not row or len(row) < 6:
                continue
            ein = normalize_ein(row[0])
            if not ein:
                malformed += 1
                continue
            records += 1
            if ein in registry_eins and row[5].strip().upper() in PUB78_CODES:
                eligible.add(ein)
    return eligible, records, malformed


def parse_revocations(path: Path, registry_eins: set[str]) -> tuple[set[str], int, int]:
    revoked: set[str] = set()
    records = malformed = 0
    with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
        for row in csv.reader(fh, delimiter="|"):
            if not row or len(row) < 12:
                continue
            ein = normalize_ein(row[0])
            if not ein:
                malformed += 1
                continue
            records += 1
            # A non-empty reinstatement date means this is not currently revoked.
            if ein in registry_eins and not row[11].strip():
                revoked.add(ein)
    return revoked, records, malformed


def parse_bmf(path: Path, registry_eins: set[str]) -> tuple[set[str], int, int, int]:
    eligible: set[str] = set()
    records = malformed = matches = 0
    with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
        for row in csv.DictReader(fh):
            records += 1
            ein = normalize_ein(row.get("EIN", ""))
            if not ein:
                malformed += 1
                continue
            if ein not in registry_eins:
                continue
            matches += 1
            if row.get("SUBSECTION", "").strip() == "03" and row.get("DEDUCTIBILITY", "").strip() == "1":
                eligible.add(ein)
    return eligible, records, malformed, matches


def write_manifest(path: Path, sources: list[Source], result: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": now_iso(),
        "max_source_age_hours": MAX_SOURCE_AGE_HOURS,
        "sources": [
            {
                "name": source.name,
                "path": str(source.path),
                "url": source.url,
                "bytes": source.path.stat().st_size,
                "mtime": datetime.fromtimestamp(source.path.stat().st_mtime, timezone.utc).isoformat(),
                "age_hours": round(source_age_hours(source.path), 2),
                "sha256": source.sha256 or sha256(source.path),
                "records": source.records,
            }
            for source in sources
        ],
        "result": result,
    }
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def reconcile(db_path: Path, eligible: set[str], revoked: set[str], backup_dir: Path, audit_id: str) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f"eligibility_{audit_id}.db"
    with sqlite3.connect(db_path) as source, sqlite3.connect(backup) as target:
        source.backup(target)

    with sqlite3.connect(db_path) as db:
        db.execute("PRAGMA busy_timeout=120000")
        db.execute("BEGIN IMMEDIATE")
        revoked_count = 0
        for chunk_start in range(0, len(revoked), 1000):
            batch = list(revoked)[chunk_start : chunk_start + 1000]
            db.executemany(
                "UPDATE registry_enriched SET deductibility='revoked', irs_revoked=1, org_status='revoked', updated_at=? WHERE EIN=?",
                [(now_iso(), ein) for ein in batch],
            )
            revoked_count += len(batch)
        eligible_count = 0
        for chunk_start in range(0, len(eligible), 1000):
            batch = list(eligible)[chunk_start : chunk_start + 1000]
            db.executemany(
                "UPDATE registry_enriched SET deductibility='1', irs_revoked=0, updated_at=? WHERE EIN=? AND COALESCE(irs_revoked,0)=0",
                [(now_iso(), ein) for ein in batch],
            )
            eligible_count += len(batch)
        db.execute(
            "INSERT INTO ingestion_audit_log (source_name,batch_id,source_record_count,valid_records,quarantined_records,validation_errors,notes) VALUES (?,?,?,?,?,?,?)",
            ("irs_eligibility_refresh", audit_id, len(eligible) + len(revoked), eligible_count, 0, "", "Pub78+BMF+auto-revocation transactional reconciliation"),
        )
        db.commit()
    return backup


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("data/merit_registry.db"))
    parser.add_argument("--data-dir", type=Path, default=Path("data/irs_authority/v6_eligibility"))
    parser.add_argument("--refresh", action="store_true", help="Download fresh IRS sources")
    parser.add_argument("--apply", action="store_true", help="Apply eligible/revoked field reconciliation")
    parser.add_argument("--max-age-hours", type=float, default=MAX_SOURCE_AGE_HOURS)
    args = parser.parse_args()

    if args.apply and not args.refresh:
        print("BLOCKED: --apply requires --refresh so source freshness is explicit", file=sys.stderr)
        return 2
    if not args.db.exists():
        print(f"BLOCKED: database not found: {args.db}", file=sys.stderr)
        return 2

    args.data_dir.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="v6_irs_", dir=args.data_dir))
    try:
        pub_zip = args.data_dir / "pub78.zip"
        rev_zip = args.data_dir / "revocation.zip"
        bmf_path = args.data_dir / "bmf.csv"
        if args.refresh:
            download(PUB78_URL, staging / "pub78.zip", MIN_ZIP_BYTES)
            download(REVOCATION_URL, staging / "revocation.zip", MIN_ZIP_BYTES)
            for index, url in enumerate(BMF_URLS, 1):
                # eo4 is naturally smaller (~1MB); others are 50-170MB
                min_size = 500_000 if index == 4 else 1_000_000
                download(url, staging / f"eo{index}.csv", min_size)
            (staging / "pub78.zip").replace(pub_zip)
            (staging / "revocation.zip").replace(rev_zip)
            # Keep the four regional BMF files; avoid a partial combined file.
            with (staging / "bmf.csv").open("w", encoding="utf-8") as out:
                for index in range(1, 5):
                    with (staging / f"eo{index}.csv").open("r", encoding="utf-8", errors="replace") as src:
                        header = next(src, None)
                        if index == 1 and header:
                            out.write(header)
                        for line in src:
                            out.write(line)
            if (staging / "bmf.csv").stat().st_size < MIN_BMF_BYTES:
                raise RuntimeError("combined BMF source is unexpectedly small")
            (staging / "bmf.csv").replace(bmf_path)
            extracted_pub = extract_first_text(pub_zip, staging)
            extracted_rev = extract_first_text(rev_zip, staging)
            pub_path = args.data_dir / "pub78.txt"
            rev_path = args.data_dir / "revocation.txt"
            extracted_pub.replace(pub_path)
            extracted_rev.replace(rev_path)
        else:
            pub_path = args.data_dir / "pub78.txt"
            rev_path = args.data_dir / "revocation.txt"
            if not (pub_path.exists() and rev_path.exists() and bmf_path.exists()):
                print("BLOCKED: local IRS sources are incomplete; run with --refresh", file=sys.stderr)
                return 2

        source_paths = [
            Source("pub78", pub_path, PUB78_URL),
            Source("auto_revocation", rev_path, REVOCATION_URL),
            Source("eo_bmf", bmf_path, ",".join(BMF_URLS)),
        ]
        stale = [f"{s.name}={source_age_hours(s.path):.1f}h" for s in source_paths if source_age_hours(s.path) > args.max_age_hours]
        if stale:
            print("BLOCKED: stale IRS source(s): " + ", ".join(stale), file=sys.stderr)
            return 2

        registry_eins = load_registry_eins(args.db)
        pub_eligible, pub_records, pub_bad = parse_pub78(pub_path, registry_eins)
        revoked, rev_records, rev_bad = parse_revocations(rev_path, registry_eins)
        bmf_eligible, bmf_records, bmf_bad, bmf_matches = parse_bmf(bmf_path, registry_eins)
        eligible = pub_eligible & bmf_eligible - revoked
        result = {
            "registry_eins": len(registry_eins),
            "pub78_records": pub_records,
            "pub78_malformed": pub_bad,
            "bmf_records": bmf_records,
            "bmf_malformed": bmf_bad,
            "bmf_registry_matches": bmf_matches,
            "bmf_eligible": len(bmf_eligible),
            "pub78_eligible": len(pub_eligible),
            "current_revoked": len(revoked),
            "final_donation_eligible": len(eligible),
            "bmf_without_pub78": len(bmf_eligible - pub_eligible),
            "pub78_without_bmf": len(pub_eligible - bmf_eligible),
            "revoked_removed": len((pub_eligible & bmf_eligible) & revoked),
            "mode": "apply" if args.apply else "check",
        }
        manifest = args.data_dir / "eligibility_manifest.json"
        write_manifest(manifest, source_paths, result)
        print(json.dumps(result, indent=2))
        print(f"manifest={manifest}")

        if args.apply:
            audit_id = "irs-eligibility-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup = reconcile(args.db, eligible, revoked, Path("data/backups/v6"), audit_id)
            print(f"backup={backup}")
        return 0
    except Exception as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(staging, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
