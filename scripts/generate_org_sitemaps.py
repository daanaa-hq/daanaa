#!/usr/bin/env python3
"""
Generate dynamic org sitemaps for Google discovery.

Strategy: Create per-letter sitemaps (A-Z) so each file stays <50MB.
Sitemap index at /sitemaps/index.xml lists all 26 org sitemaps + static sitemap.

Runs weekly (or on-demand) and outputs to /data/precompute/v1/sitemaps/
"""
import sqlite3
import gzip
import time
from pathlib import Path
from datetime import datetime, timezone

import os as _os

DB_PATH = Path(_os.environ.get("MERIT_DB_PATH", "/home/akbar/meritgiving/data/merit_registry.db"))
OUTPUT_DIR = Path(_os.environ.get("SITEMAP_OUTPUT", "/tmp/daanaa-sitemaps"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# How many orgs per sitemap file before splitting
ORGS_PER_FILE = 50000
PRIORITY_BY_BAND = {
    "Established": "0.9",
    "Professional": "0.8",
    "Micro": "0.7",
}

def log(msg):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def generate_org_sitemaps():
    """Generate sitemaps organized by first letter of org name."""

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    # Get total org count
    total = db.execute("SELECT COUNT(*) FROM registry_enriched WHERE organization_name IS NOT NULL").fetchone()[0]
    log(f"Generating sitemaps for {total:,} orgs")

    # Sitemap index entries
    sitemap_files = []
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Generate per-letter sitemaps
    for first_letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        sitemaps_for_letter = generate_sitemaps_for_letter(db, first_letter, now_iso)
        sitemap_files.extend(sitemaps_for_letter)

    # Generate sitemap index
    index_content = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""

    # Add static sitemap first
    index_content += f"""  <sitemap>
    <loc>https://daanaa.org/sitemap.xml</loc>
    <lastmod>{now_iso}</lastmod>
  </sitemap>
"""

    # Add all org sitemaps
    for filename, lastmod in sitemap_files:
        index_content += f"""  <sitemap>
    <loc>https://daanaa.org/sitemaps/{filename}</loc>
    <lastmod>{lastmod}</lastmod>
  </sitemap>
"""

    index_content += """</sitemapindex>"""

    # Write index
    index_path = OUTPUT_DIR / "index.xml"
    with gzip.open(index_path, 'wt', encoding='utf-8') as f:
        f.write(index_content)

    log(f"✅ Sitemap index written: {len(sitemap_files)} org sitemaps")
    return len(sitemap_files)

def generate_sitemaps_for_letter(db, letter, now_iso):
    """Generate one or more sitemaps for orgs starting with this letter."""

    # Query orgs starting with letter, ordered by EIN (stable ordering)
    query = """
    SELECT EIN, organization_name, merit_band_v5_label
    FROM registry_enriched
    WHERE organization_name LIKE ? AND organization_name IS NOT NULL
    ORDER BY EIN
    """

    orgs = db.execute(query, (f"{letter}%",)).fetchall()
    log(f"  {letter}: {len(orgs)} orgs")

    if not orgs:
        return []

    sitemap_files = []
    file_num = 1

    # Split into files of ORGS_PER_FILE each
    for batch_start in range(0, len(orgs), ORGS_PER_FILE):
        batch = orgs[batch_start : batch_start + ORGS_PER_FILE]

        # Filename: orgs-A-1.xml.gz, orgs-A-2.xml.gz, etc.
        filename = f"orgs-{letter}-{file_num}.xml.gz"
        file_path = OUTPUT_DIR / filename

        sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="https://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="https://www.google.com/schemas/sitemap-image/1.1">
"""

        for org in batch:
            ein = org["EIN"]
            name = org["organization_name"] or "Nonprofit"
            band = org["merit_band_v5_label"] or "Micro"
            priority = PRIORITY_BY_BAND.get(band, "0.7")

            sitemap += f"""  <url>
    <loc>https://daanaa.org/org/{ein}</loc>
    <lastmod>{now_iso}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>{priority}</priority>
  </url>
"""

        sitemap += """</urlset>"""

        # Write gzipped sitemap
        with gzip.open(file_path, 'wt', encoding='utf-8') as f:
            f.write(sitemap)

        sitemap_files.append((filename, now_iso))
        file_num += 1

    return sitemap_files

def main():
    start = time.time()
    log("=== Org Sitemap Generation ===")

    try:
        count = generate_org_sitemaps()
        elapsed = time.time() - start
        log(f"=== Done in {elapsed:.1f}s — {count} sitemaps generated ===")
    except Exception as e:
        log(f"ERROR: {str(e)}")
        raise

if __name__ == "__main__":
    main()
