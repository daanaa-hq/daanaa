#!/usr/bin/env python3
"""Prepare a Cloudflare Pages-compatible copy of the visibility overlay."""

from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "visibility" / "public"
OUT = ROOT / "visibility" / "cloudflare-public"
MAX_CHUNK_BYTES = 20_000_000
TEXT_SUFFIXES = {".html", ".json", ".txt", ".xml"}
ABSOLUTE_HTML_URL_RE = re.compile(
    r"(?P<base>(?:https://)?data\.daanaa\.org)"
    r"(?P<path>/[A-Za-z0-9._~!$&()*+,;=:@%/-]*?\.html)"
    r"(?P<suffix>[?#][^\"'<> \t\r\n]*)?"
)
ROOT_HTML_LINK_RE = re.compile(
    r"(?P<prefix>\b(?:href|content)=[\"'])"
    r"(?P<path>/[A-Za-z0-9._~!$&()*+,;=:@%/-]*?\.html)"
    r"(?P<suffix>[?#][^\"'<> \t\r\n]*)?"
    r"(?P<quote>[\"'])"
)


def clean_html_path(path: str) -> str:
    if path.endswith("/index.html"):
        return path[: -len("index.html")]
    return path[:-5]


def normalize_overlay_urls(text: str) -> str:
    def replace_absolute(match: re.Match[str]) -> str:
        return (
            match.group("base")
            + clean_html_path(match.group("path"))
            + (match.group("suffix") or "")
        )

    def replace_root_link(match: re.Match[str]) -> str:
        return (
            match.group("prefix")
            + clean_html_path(match.group("path"))
            + (match.group("suffix") or "")
            + match.group("quote")
        )

    text = ABSOLUTE_HTML_URL_RE.sub(replace_absolute, text)
    return ROOT_HTML_LINK_RE.sub(replace_root_link, text)


def copy_base() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SRC, OUT, ignore=shutil.ignore_patterns("orgs.csv"))
    (OUT / "data").mkdir(parents=True, exist_ok=True)


def split_csv() -> list[dict[str, object]]:
    src_csv = SRC / "data" / "orgs.csv"
    chunks_dir = OUT / "data" / "orgs"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []

    with src_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        chunk_index = 0
        row_count = 0
        out = None
        writer = None
        chunk_rows = 0
        chunk_path = None

        def open_chunk() -> None:
            nonlocal chunk_index, out, writer, chunk_rows, chunk_path
            if out:
                out.close()
                manifest[-1]["rows"] = chunk_rows
                manifest[-1]["bytes"] = chunk_path.stat().st_size
            chunk_index += 1
            chunk_rows = 0
            chunk_path = chunks_dir / f"orgs-{chunk_index:04d}.csv"
            out = chunk_path.open("w", newline="", encoding="utf-8")
            writer = csv.writer(out)
            writer.writerow(header)
            manifest.append({"path": f"data/orgs/{chunk_path.name}", "rows": 0, "bytes": 0})

        open_chunk()
        for row in reader:
            if chunk_rows > 0 and chunk_path.stat().st_size >= MAX_CHUNK_BYTES:
                open_chunk()
            writer.writerow(row)
            chunk_rows += 1
            row_count += 1

        if out:
            out.close()
            manifest[-1]["rows"] = chunk_rows
            manifest[-1]["bytes"] = chunk_path.stat().st_size

    payload = {"source": "data/orgs.csv", "rows": row_count, "chunks": manifest}
    (OUT / "data" / "orgs-manifest.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def rewrite_text_files(chunks: list[dict[str, object]]) -> None:
    chunk_count = len(chunks)
    replacements = {
        "/data/orgs.csv": "/data/orgs-manifest.json",
        "https://data.daanaa.org/data/orgs.csv": "https://data.daanaa.org/data/orgs-manifest.json",
        "Organization CSV": "Organization CSV manifest",
        "Organizations CSV": "Organizations CSV manifest",
    }
    for rel in ["llms.txt", "open-data.html", "dataset.json", "visibility-manifest.json"]:
        path = OUT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        if rel == "open-data.html" and "CSV chunks" not in text:
            chunk_html = (
                f'<p>CSV chunks: {chunk_count:,}. The full organization export is split for '
                'static-host file-size limits. See <a href="/data/orgs-manifest.json">'
                'the CSV manifest</a>.</p>\n    <p>CSV columns:'
            )
            text = text.replace("<p>CSV columns:", chunk_html)
        if rel == "llms.txt" and "CSV chunks" not in text:
            text += (
                "\n## Chunked CSV\n\n"
                f"The organization export is split into {chunk_count} CSV chunks listed at "
                "https://data.daanaa.org/data/orgs-manifest.json.\n"
            )
        path.write_text(text, encoding="utf-8")


def normalize_deployable_urls(root: Path = OUT) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        original = path.read_text(encoding="utf-8")
        normalized = normalize_overlay_urls(original)
        if normalized != original:
            path.write_text(normalized, encoding="utf-8")


def validate_sizes() -> None:
    large = []
    for path in OUT.rglob("*"):
        if path.is_file() and path.stat().st_size > 25_000_000:
            large.append((path.stat().st_size, path))
    if large:
        for size, path in large:
            print(f"Too large for Cloudflare Pages: {size} {path}")
        raise SystemExit(1)


def main() -> int:
    copy_base()
    chunks = split_csv()
    rewrite_text_files(chunks)
    normalize_deployable_urls()
    validate_sizes()
    total = sum(int(c["rows"]) for c in chunks)
    print(f"Prepared {OUT}")
    print(f"CSV chunks: {len(chunks)}")
    print(f"Rows: {total:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
