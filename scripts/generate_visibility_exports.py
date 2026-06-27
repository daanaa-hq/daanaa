#!/usr/bin/env python3
"""
Generate Daanaa visibility/export artifacts from local nonprofit data.

This script is intentionally read-only against the application database. It
writes only data/orgs.csv, dist/sitemap-index.xml, dist/sitemaps/*,
dist/llms.txt, dist/open-data.html, and dist/visibility-manifest.json.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import Iterable
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "merit_registry.db"
DEFAULT_ORGS_CSV = ROOT / "data" / "orgs.csv"
DEFAULT_DIST = ROOT / "dist"
BASE_URL = "https://daanaa.org"
SITEMAP_LIMIT = 50_000

NTEE_MAJOR = {
    "A": "Arts, Culture, and Humanities",
    "B": "Education",
    "C": "Environment",
    "D": "Animal-Related",
    "E": "Health Care",
    "F": "Mental Health and Crisis Intervention",
    "G": "Voluntary Health Associations and Medical Disciplines",
    "H": "Medical Research",
    "I": "Crime and Legal-Related",
    "J": "Employment",
    "K": "Food, Agriculture, and Nutrition",
    "L": "Housing and Shelter",
    "M": "Public Safety, Disaster Preparedness, and Relief",
    "N": "Recreation and Sports",
    "O": "Youth Development",
    "P": "Human Services",
    "Q": "International, Foreign Affairs, and National Security",
    "R": "Civil Rights, Social Action, and Advocacy",
    "S": "Community Improvement and Capacity Building",
    "T": "Philanthropy, Voluntarism, and Grantmaking Foundations",
    "U": "Science and Technology Research Institutes",
    "V": "Social Science Research Institutes",
    "W": "Public and Societal Benefit",
    "X": "Religion-Related",
    "Y": "Mutual and Membership Benefit",
    "Z": "Unknown",
    "0": "Unclassified",
}


def normalized_ein(value: object) -> str:
    text = "" if value is None else str(value).strip()
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) != 9:
        raise ValueError(f"Invalid EIN {text!r}: EIN must contain exactly 9 digits")
    return digits


def category_letter(ntee1: object, nteecc: object) -> str:
    for value in (ntee1, nteecc):
        text = "" if value is None else str(value).strip().upper()
        if text:
            return text[0]
    return "Z"


def open_readonly(db_path: Path) -> sqlite3.Connection:
    uri = f"file:{db_path.resolve()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def iter_orgs(conn: sqlite3.Connection) -> Iterable[dict[str, str]]:
    sql = """
        SELECT EIN, organization_name, CITY, STATE, NTEE1, NTEECC
        FROM registry_enriched
        WHERE EIN IS NOT NULL
          AND EIN != ''
          AND organization_name IS NOT NULL
          AND organization_name != ''
          AND org_status = 'active'
          AND CAST(deductibility AS TEXT) = '1'
        ORDER BY EIN
    """
    for row in conn.execute(sql):
        ein = normalized_ein(row["EIN"])
        letter = category_letter(row["NTEE1"], row["NTEECC"])
        yield {
            "ein": ein,
            "name": row["organization_name"] or "",
            "city": row["CITY"] or "",
            "state": row["STATE"] or "",
            "category_letter": letter,
            "category_name": NTEE_MAJOR.get(letter, "Unknown"),
            "profile_url": f"{BASE_URL}/org/{ein}",
        }


def write_orgs_csv(conn: sqlite3.Connection, output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "ein",
        "name",
        "city",
        "state",
        "category_letter",
        "category_name",
        "profile_url",
    ]
    count = 0
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for org in iter_orgs(conn):
            writer.writerow(org)
            count += 1
    return count


def write_sitemaps(orgs_csv: Path, dist_dir: Path) -> tuple[int, int]:
    sitemaps_dir = dist_dir / "sitemaps"
    sitemaps_dir.mkdir(parents=True, exist_ok=True)
    for old in sitemaps_dir.glob("*.xml"):
        old.unlink()

    sitemap_count = 0
    url_count = 0
    current = None

    def start_file(index: int):
        path = sitemaps_dir / f"orgs-{index:04d}.xml"
        f = path.open("w", encoding="utf-8")
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        return path, f

    with orgs_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        file_handle = None
        try:
            for row in reader:
                if url_count % SITEMAP_LIMIT == 0:
                    if file_handle:
                        file_handle.write("</urlset>\n")
                        file_handle.close()
                    sitemap_count += 1
                    current, file_handle = start_file(sitemap_count)
                loc = html.escape(row["profile_url"], quote=True)
                file_handle.write("  <url>\n")
                file_handle.write(f"    <loc>{loc}</loc>\n")
                file_handle.write("  </url>\n")
                url_count += 1
        finally:
            if file_handle:
                file_handle.write("</urlset>\n")
                file_handle.close()

    today = date.today().isoformat()
    index_path = dist_dir / "sitemap-index.xml"
    with index_path.open("w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for path in sorted(sitemaps_dir.glob("orgs-*.xml")):
            loc = f"{BASE_URL}/sitemaps/{quote(path.name)}"
            f.write("  <sitemap>\n")
            f.write(f"    <loc>{loc}</loc>\n")
            f.write(f"    <lastmod>{today}</lastmod>\n")
            f.write("  </sitemap>\n")
        f.write("</sitemapindex>\n")

    return sitemap_count, url_count


def write_llms_txt(dist_dir: Path, record_count: int, sitemap_count: int) -> None:
    text = f"""# Daanaa

Daanaa is a public nonprofit discovery directory built from local IRS, NCCS, ProPublica, and Daanaa registry data.

## Open Data

- Organization CSV: {BASE_URL}/data/orgs.csv
- Open data page: {BASE_URL}/open-data.html
- Sitemap index: {BASE_URL}/sitemap-index.xml
- Sitemap files: {sitemap_count}
- Organization records in this export: {record_count}

## Profile URLs

Organization profiles follow this pattern:

{BASE_URL}/org/{{ein}}

The exported CSV columns are ein, name, city, state, category_letter, category_name, and profile_url.
"""
    (dist_dir / "llms.txt").write_text(text, encoding="utf-8")


def write_open_data_html(dist_dir: Path, record_count: int, sitemap_count: int) -> None:
    markup = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Daanaa Open Nonprofit Data</title>
  <meta name="description" content="Open nonprofit organization export for Daanaa discovery and indexing.">
</head>
<body>
  <main>
    <h1>Daanaa Open Nonprofit Data</h1>
    <p>Daanaa publishes a local nonprofit discovery export for search engines, AI agents, and civic data review.</p>
    <ul>
      <li><a href="/data/orgs.csv">Organization CSV</a></li>
      <li><a href="/sitemap-index.xml">Sitemap index</a></li>
      <li><a href="/llms.txt">llms.txt</a></li>
    </ul>
    <p>Records: {record_count:,}</p>
    <p>Sitemap files: {sitemap_count:,}</p>
    <p>CSV columns: ein, name, city, state, category_letter, category_name, profile_url.</p>
  </main>
</body>
</html>
"""
    (dist_dir / "open-data.html").write_text(markup, encoding="utf-8")


def grouped_counts(conn: sqlite3.Connection, column: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value, count in conn.execute(
        f"SELECT {column}, COUNT(*) FROM registry_enriched GROUP BY {column} ORDER BY COUNT(*) DESC"
    ):
        key = "blank/null" if value is None or value == "" else str(value)
        counts[key] = counts.get(key, 0) + int(count)
    return counts


def source_counts(conn: sqlite3.Connection, db_path: Path) -> dict[str, object]:
    def one(sql: str) -> int:
        return int(conn.execute(sql).fetchone()[0])

    return {
        "database": str(db_path.relative_to(ROOT)) if db_path.is_relative_to(ROOT) else str(db_path),
        "table": "registry_enriched",
        "registry_records": one("SELECT COUNT(*) FROM registry_enriched"),
        "export_records_query": one(
            """
            SELECT COUNT(*) FROM registry_enriched
            WHERE EIN IS NOT NULL AND EIN != ''
              AND organization_name IS NOT NULL AND organization_name != ''
              AND org_status = 'active'
              AND CAST(deductibility AS TEXT) = '1'
            """
        ),
        "records_with_city": one("SELECT COUNT(*) FROM registry_enriched WHERE CITY IS NOT NULL AND CITY != ''"),
        "records_with_state": one("SELECT COUNT(*) FROM registry_enriched WHERE STATE IS NOT NULL AND STATE != ''"),
        "records_with_category": one(
            "SELECT COUNT(*) FROM registry_enriched WHERE COALESCE(NTEE1, NTEECC) IS NOT NULL AND COALESCE(NTEE1, NTEECC) != ''"
        ),
        "source_counts": grouped_counts(conn, "source"),
        "data_source_counts": grouped_counts(conn, "data_source"),
    }


def discovered_sources() -> list[dict[str, str]]:
    return [
        {
            "path": "data/merit_registry.db",
            "role": "Primary active SQLite registry. Table registry_enriched contains EIN, organization_name, CITY, STATE, NTEE1/NTEECC, status, deductibility, and enrichment fields.",
        },
        {
            "path": "data/search.db and data/droplet_search.db",
            "role": "Derived search/static-serving SQLite databases with registry_enriched/orgs copies for droplet search and public org lookup.",
        },
        {
            "path": "data/eo1.csv, data/eo3.csv, data/eo4.csv, data/cache/bmf_new/*.csv, data/bmf/2026-04-BMF.csv, data/raw/2023_eo_bmf.csv",
            "role": "IRS Exempt Organizations Business Master File extracts; contain EIN, name, city, state, and NTEE fields used to seed/backfill registry records.",
        },
        {
            "path": "data/csv/master_orgs.csv and data/master_orgs.csv",
            "role": "Master organization CSV snapshots used by earlier ETL scripts; include EIN, NAME, CITY, STATE, and NTEE-style fields.",
        },
        {
            "path": "data/corepcf/*.csv and data/nccs/*.CSV",
            "role": "NCCS Core/expense inputs used for financial and category enrichment keyed by EIN.",
        },
        {
            "path": "data/propublica_cache/*.json",
            "role": "Cached ProPublica Nonprofit Explorer organization responses keyed by EIN; include org identity, location, NTEE, filings, and revenue data.",
        },
        {
            "path": "data/xml/{2020,2022}/*.xml and data/csv/*_parsed.tar.gz",
            "role": "IRS 990 XML filings and parsed filing archives used to extract mission, website, and financial fields keyed by EIN.",
        },
        {
            "path": "data/990n_data.zip, data/epostcard.zip, data/data-download-epostcard.txt, data/csv/postcard_filers.csv",
            "role": "IRS 990-N/e-postcard data for smaller nonprofits, keyed by EIN.",
        },
        {
            "path": "precompute_output/ein_map.json.gz and precompute_output/orgs/",
            "role": "Generated static org lookup/precompute artifacts used by the public site when present.",
        },
        {
            "path": "migrations/*.sql, scripts/ingest_*.py, scripts/import_bmf_orgs.py, scripts/propublica_backfill.py, scripts/overnight_build.py",
            "role": "Schema and ETL scripts that create, ingest, and backfill nonprofit data into registry_enriched.",
        },
    ]


def write_manifest(dist_dir: Path, counts: dict[str, object], record_count: int, sitemap_count: int) -> None:
    manifest = {
        "generated_at": date.today().isoformat(),
        "base_url": BASE_URL,
        "orgs_csv": "data/orgs.csv",
        "sitemap_index": "dist/sitemap-index.xml",
        "sitemap_count": sitemap_count,
        "export_record_count": record_count,
        "counts": counts,
        "discovered_sources": discovered_sources(),
    }
    (dist_dir / "visibility-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Daanaa visibility/export files from local data.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--orgs-csv", type=Path, default=DEFAULT_ORGS_CSV)
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    args = parser.parse_args()

    args.dist.mkdir(parents=True, exist_ok=True)
    with open_readonly(args.db) as conn:
        counts = source_counts(conn, args.db)
        record_count = write_orgs_csv(conn, args.orgs_csv)

    sitemap_count, sitemap_urls = write_sitemaps(args.orgs_csv, args.dist)
    write_llms_txt(args.dist, record_count, sitemap_count)
    write_open_data_html(args.dist, record_count, sitemap_count)
    write_manifest(args.dist, counts, record_count, sitemap_count)

    print(f"Wrote {display_path(args.orgs_csv)} ({record_count:,} records)")
    print(f"Wrote {display_path(args.dist / 'sitemap-index.xml')}")
    print(f"Wrote {sitemap_count:,} sitemap files with {sitemap_urls:,} URLs")
    print(f"Wrote {display_path(args.dist / 'llms.txt')}")
    print(f"Wrote {display_path(args.dist / 'open-data.html')}")
    print(f"Wrote {display_path(args.dist / 'visibility-manifest.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
