#!/usr/bin/env python3
"""Inventory, compare, and package Phase 3 precompute artifacts safely.

This tool is deliberately separate from the live deployment script.  It makes
the file set explicit before packaging and creates resumable, bounded archives
instead of one opaque multi-million-file tarball.

Examples:
  python3 scripts/phase3_artifact_tools.py inventory \
    --root .deploy_scratch/precompute \
    --output .deploy_scratch/precompute.manifest.json

  python3 scripts/phase3_artifact_tools.py compare-archive \
    --root .deploy_scratch/precompute \
    --archive .deploy_scratch/precompute_payload.tar.gz

  python3 scripts/phase3_artifact_tools.py package-org-shards \
    --root .deploy_scratch/precompute \
    --output-dir .deploy_scratch/precompute_shards \
    --shards 32
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tarfile
from collections import Counter
from pathlib import Path
from typing import Iterable, Iterator


EXCLUDED_NAMES = {"vectors.f32.memmap"}


def iter_files(root: Path) -> Iterator[Path]:
    """Yield regular files under root without following symlinks."""
    if not root.is_dir():
        raise SystemExit(f"artifact root is not a directory: {root}")

    for base, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not (Path(base) / d).is_symlink())
        for name in sorted(names):
            path = Path(base) / name
            if name in EXCLUDED_NAMES:
                continue
            if path.is_symlink():
                raise SystemExit(f"refusing symlink artifact: {path}")
            if not path.is_file():
                raise SystemExit(f"refusing non-regular artifact: {path}")
            yield path


def rel_files(root: Path) -> Iterator[tuple[str, Path]]:
    for path in iter_files(root):
        yield path.relative_to(root).as_posix(), path


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(root: Path, output: Path | None, include_hashes: bool) -> dict:
    files = []
    prefixes: Counter[str] = Counter()
    total_bytes = 0

    for relative, path in rel_files(root):
        size = path.stat().st_size
        total_bytes += size
        parts = relative.split("/")
        prefix = parts[1] if len(parts) > 2 and parts[0] == "orgs" else parts[0]
        prefixes[prefix] += 1
        entry = {"path": relative, "size": size}
        if include_hashes:
            entry["sha256"] = sha256_file(path)
        files.append(entry)

    result = {
        "format": "daanaa.phase3.artifact-manifest.v1",
        "root": str(root.resolve()),
        "file_count": len(files),
        "total_bytes": total_bytes,
        "prefix_counts": dict(sorted(prefixes.items())),
        "files": files,
    }
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        temp = output.with_suffix(output.suffix + ".tmp")
        temp.write_text(json.dumps(result, separators=(",", ":")), encoding="utf-8")
        os.replace(temp, output)
    return result


def archive_members(archive: Path) -> Iterator[tuple[str, int]]:
    if not archive.is_file():
        raise SystemExit(f"archive not found: {archive}")
    try:
        with tarfile.open(archive, mode="r:*") as handle:
            for member in handle:
                if member.isdir():
                    continue
                if not member.isfile():
                    raise SystemExit(f"archive contains non-regular member: {member.name}")
                yield member.name.lstrip("./"), member.size
    except (tarfile.TarError, OSError) as exc:
        raise SystemExit(f"archive cannot be read: {archive}: {exc}") from exc


def compare_archive(root: Path, archive: Path) -> dict:
    source = {relative: path.stat().st_size for relative, path in rel_files(root)}
    seen: dict[str, int] = {}
    duplicate_members = []
    for relative, size in archive_members(archive):
        if relative in seen:
            duplicate_members.append(relative)
        seen[relative] = size

    missing = sorted(set(source) - set(seen))
    extra = sorted(set(seen) - set(source))
    size_mismatches = sorted(
        path for path in set(source) & set(seen) if source[path] != seen[path]
    )
    result = {
        "source_files": len(source),
        "archive_files": len(seen),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "size_mismatch_count": len(size_mismatches),
        "duplicate_member_count": len(duplicate_members),
        "missing_examples": missing[:20],
        "extra_examples": extra[:20],
        "size_mismatch_examples": size_mismatches[:20],
        "duplicate_examples": duplicate_members[:20],
    }
    print(json.dumps(result, indent=2))
    if any(result[key] for key in (
        "missing_count", "extra_count", "size_mismatch_count", "duplicate_member_count"
    )):
        raise SystemExit(1)
    print("artifact archive matches source manifest")
    return result


def shard_for_prefix(prefix: str, shard_count: int) -> int:
    if not prefix.isdigit():
        return shard_count - 1
    return min(int(prefix) * shard_count // 1000, shard_count - 1)


def package_org_shards(root: Path, output_dir: Path, shard_count: int) -> None:
    if shard_count < 1 or shard_count > 1000:
        raise SystemExit("--shards must be between 1 and 1000")
    org_root = root / "orgs"
    if not org_root.is_dir():
        raise SystemExit(f"missing org artifact directory: {org_root}")
    output_dir.mkdir(parents=True, exist_ok=True)

    prefixes = sorted(
        path.name for path in org_root.iterdir()
        if path.is_dir() and not path.is_symlink()
    )
    grouped: dict[int, list[str]] = {index: [] for index in range(shard_count)}
    for prefix in prefixes:
        grouped[shard_for_prefix(prefix, shard_count)].append(prefix)

    for index, selected in grouped.items():
        if not selected:
            continue
        archive = output_dir / f"orgs-shard-{index:03d}-of-{shard_count:03d}.tar.gz"
        if archive.exists():
            print(f"skip existing {archive}")
            continue
        temporary = archive.with_suffix(archive.suffix + ".tmp")
        print(f"creating {archive} ({len(selected)} prefix directories)", flush=True)
        with tarfile.open(temporary, mode="w:gz") as handle:
            for prefix in selected:
                directory = org_root / prefix
                handle.add(directory, arcname=f"orgs/{prefix}", recursive=True)
        os.replace(temporary, archive)
        checksum = sha256_file(archive)
        archive.with_suffix(archive.suffix + ".sha256").write_text(
            f"{checksum}  {archive.name}\n", encoding="utf-8"
        )
        print(f"completed {archive} sha256={checksum}", flush=True)


def validate_org_layout(root: Path, expected_count: int | None) -> int:
    """Validate that a precompute root contains only nested org artifacts."""
    orgs = root / "orgs"
    if not orgs.is_dir():
        print(json.dumps({"ok": False, "error": f"missing directory: {orgs}"}))
        return 1

    root_files = []
    invalid_prefixes = []
    invalid_files = []
    nested_json_gz = 0
    other_files = 0

    for entry in sorted(orgs.iterdir()):
        if entry.is_symlink():
            invalid_prefixes.append(entry.name)
        elif entry.is_file():
            root_files.append(entry.name)
        elif not (entry.is_dir() and len(entry.name) == 3 and entry.name.isdigit()):
            invalid_prefixes.append(entry.name)

    for prefix_dir in sorted(orgs.iterdir()):
        if not (prefix_dir.is_dir() and not prefix_dir.is_symlink()):
            continue
        if not (len(prefix_dir.name) == 3 and prefix_dir.name.isdigit()):
            continue
        for path in prefix_dir.rglob("*"):
            if path.is_symlink() or not path.is_file():
                invalid_files.append(str(path.relative_to(orgs)))
                continue
            rel = path.relative_to(prefix_dir)
            if len(rel.parts) != 1 or not path.name.startswith(prefix_dir.name):
                invalid_files.append(str(path.relative_to(orgs)))
            elif path.name.endswith(".json.gz"):
                nested_json_gz += 1
            else:
                other_files += 1

    ok = not root_files and not invalid_prefixes and not invalid_files and other_files == 0
    if expected_count is not None and nested_json_gz != expected_count:
        ok = False

    result = {
        "ok": ok,
        "root": str(root),
        "nested_json_gz": nested_json_gz,
        "flat_json": len(root_files),
        "other_or_invalid_nested_files": other_files + len(invalid_files),
        "invalid_prefixes": invalid_prefixes[:10],
        "invalid_files": invalid_files[:10],
    }
    if expected_count is not None:
        result["expected_count"] = expected_count
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    inv = sub.add_parser("inventory")
    inv.add_argument("--root", type=Path, required=True)
    inv.add_argument("--output", type=Path)
    inv.add_argument("--include-hashes", action="store_true")

    compare = sub.add_parser("compare-archive")
    compare.add_argument("--root", type=Path, required=True)
    compare.add_argument("--archive", type=Path, required=True)

    shards = sub.add_parser("package-org-shards")
    shards.add_argument("--root", type=Path, required=True)
    shards.add_argument("--output-dir", type=Path, required=True)
    shards.add_argument("--shards", type=int, default=32)

    layout = sub.add_parser("validate-org-layout")
    layout.add_argument("--root", type=Path, required=True)
    layout.add_argument("--expected-count", type=int)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "inventory":
        result = inventory(args.root, args.output, args.include_hashes)
        print(json.dumps({k: result[k] for k in ("file_count", "total_bytes", "prefix_counts")}, indent=2))
    elif args.command == "compare-archive":
        compare_archive(args.root, args.archive)
    elif args.command == "package-org-shards":
        package_org_shards(args.root, args.output_dir, args.shards)
    elif args.command == "validate-org-layout":
        return validate_org_layout(args.root, args.expected_count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
