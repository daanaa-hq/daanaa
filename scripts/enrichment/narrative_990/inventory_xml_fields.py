#!/usr/bin/env python3
"""
scripts/enrichment/narrative_990/inventory_xml_fields.py

Phase 1 of the 990 Narrative Enrichment project (docs/990-enrichment/).
Research tool, not a production script: pulls a small, diverse sample of real
IRS Form 990-series XML filings from ONE recent monthly batch, then walks
every filing's full XML tree and records every text-bearing element -- so we
can see what narrative fields actually exist before designing a parser
around them.

Reuses scripts/ops/fetch_irs_direct_filing.py's index/batch-URL functions
rather than re-implementing IRS acquisition (see docs/990-enrichment/
system-audit.md "do not rebuild IRS acquisition").

Sampling strategy (bandwidth-efficient per the project brief -- one batch ZIP
download, not one per EIN):
  1. Take the single most recent IRS monthly batch (currently 2026_TEOS_XML_06A).
  2. Within that batch, prefer EINs already in registry_enriched, spread
     across distinct NTEE1 codes and form types (990/990EZ/990PF), so the
     sample reflects orgs Daanaa actually needs to enrich.
  3. Extract only the sampled EINs' XML from the one downloaded ZIP.

Usage:
    python3 -m scripts.enrichment.narrative_990.inventory_xml_fields
    python3 -m scripts.enrichment.narrative_990.inventory_xml_fields --sample-size 24
"""
import argparse
import csv
import io
import re
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

import requests

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
from scripts.ops.fetch_irs_direct_filing import INDEX_BASE, batch_zip_url  # noqa: E402

DB_PATH = REPO_ROOT / "data" / "merit_registry.db"
SAMPLE_DIR = REPO_ROOT / "data" / "990_xml" / "samples"
OUTPUT_INVENTORY = REPO_ROOT / "docs" / "990-enrichment" / "xml-field-inventory.md"
OUTPUT_MANIFEST = SAMPLE_DIR / "manifest.csv"
NS = "{http://www.irs.gov/efile}"

# A text-bearing element is "interesting" if it holds free-text narrative
# rather than a bare number/code/date. Cheap heuristic: text length >= this
# after whitespace normalization, OR the tag name matches a narrative-ish
# keyword regardless of length (short program names etc. still matter).
MIN_INTERESTING_LEN = 15
NARRATIVE_TAG_HINTS = re.compile(
    r"Mission|ActivityOrMission|ProgramService|Accomplishment|Description"
    r"|Explanation|Narrative|Purpose|Grant.*Desc|ActivityDesc|Achievement",
    re.IGNORECASE,
)


def pick_sample_eins(batch_rows: list[dict], target_size: int) -> list[dict]:
    """Selects a diverse sample from one batch's index rows: prefer EINs
    already in registry_enriched, spread across NTEE1 + form type."""
    ein_to_row = {}
    for row in batch_rows:
        ein = row.get("EIN", "").strip().zfill(9)
        rtype = row.get("RETURN_TYPE", "").strip()
        if rtype not in ("990", "990EZ", "990PF"):
            continue  # 990T is unrelated-business-income, not this project's shape
        # Keep the newest TAX_PERIOD per EIN if it appears more than once in this batch.
        prior = ein_to_row.get(ein)
        if prior is None or row.get("TAX_PERIOD", "") > prior.get("TAX_PERIOD", ""):
            ein_to_row[ein] = row

    conn = sqlite3.connect(str(DB_PATH))
    known = {}
    batch_eins = list(ein_to_row.keys())
    for i in range(0, len(batch_eins), 900):  # sqlite variable limit safety
        chunk = batch_eins[i : i + 900]
        placeholders = ",".join("?" * len(chunk))
        rows = conn.execute(
            f"SELECT EIN, ntee1, mission_source, total_revenue "
            f"FROM registry_enriched WHERE EIN IN ({placeholders})",
            chunk,
        ).fetchall()
        for ein, ntee1, mission_source, revenue in rows:
            known[ein] = {"ntee1": ntee1 or "?", "mission_source": mission_source, "revenue": revenue}
    conn.close()
    print(f"  {len(ein_to_row)} EINs in batch, {len(known)} already known to Daanaa")

    # Bucket known EINs by (ntee1, form_type) for spread; unknown EINs are a fallback pool.
    buckets: dict[tuple, list[str]] = defaultdict(list)
    for ein, row in ein_to_row.items():
        if ein in known:
            key = (known[ein]["ntee1"], row["RETURN_TYPE"])
            buckets[key].append(ein)

    sample: list[str] = []
    bucket_keys = sorted(buckets.keys())
    idx = 0
    while len(sample) < target_size and bucket_keys:
        key = bucket_keys[idx % len(bucket_keys)]
        pool = buckets[key]
        if pool:
            sample.append(pool.pop())
        else:
            bucket_keys.remove(key)
            if not bucket_keys:
                break
            continue
        idx += 1

    # Backfill from unknown-but-in-batch EINs if buckets ran dry (rare).
    if len(sample) < target_size:
        for ein in ein_to_row:
            if ein not in sample:
                sample.append(ein)
            if len(sample) >= target_size:
                break

    return [dict(ein=ein, **ein_to_row[ein], **known.get(ein, {})) for ein in sample[:target_size]]


def download_batch(batch_id: str) -> Path:
    zip_url = batch_zip_url(batch_id)
    dest = SAMPLE_DIR / f"{batch_id}.zip"
    if dest.exists() and dest.stat().st_size > 10_000_000:
        print(f"  Reusing cached {dest.name} ({dest.stat().st_size/1e6:.0f} MB)")
        return dest
    print(f"  Downloading {zip_url} (this is a full monthly batch, ~400-700MB)...")
    resp = requests.get(zip_url, timeout=900, stream=True)
    resp.raise_for_status()
    tmp = dest.with_suffix(".zip.part")
    with open(tmp, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1 << 20):
            f.write(chunk)
    tmp.rename(dest)
    print(f"  Saved {dest.name} ({dest.stat().st_size/1e6:.0f} MB)")
    return dest


def extract_filings(zip_path: Path, samples: list[dict]) -> list[dict]:
    extracted = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for row in samples:
            xml_name = f"{row['OBJECT_ID']}_public.xml"
            result = subprocess.run(
                ["unzip", "-o", str(zip_path), xml_name, "-d", tmpdir],
                capture_output=True, text=True,
            )
            xml_path = Path(tmpdir) / xml_name
            if result.returncode != 0 or not xml_path.exists():
                print(f"  MISSING in batch: {row['ein']} ({xml_name})")
                continue
            dest = SAMPLE_DIR / f"{row['ein']}_{row['RETURN_TYPE']}_{row['TAX_PERIOD']}.xml"
            dest.write_bytes(xml_path.read_bytes())
            row["local_path"] = dest
            extracted.append(row)
    return extracted


def localname(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def walk_narrative_fields(xml_path: Path, form_type: str) -> list[dict]:
    """Enumerates every text-bearing element worth cataloguing: local tag,
    approximate path (parent chain of local names), text length, and a short
    snippet. Returns one row per element instance found."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    findings = []

    def visit(el, path):
        tag = localname(el.tag)
        this_path = f"{path}/{tag}"
        text = (el.text or "").strip()
        norm = " ".join(text.split())
        if norm and (len(norm) >= MIN_INTERESTING_LEN or NARRATIVE_TAG_HINTS.search(tag)):
            findings.append({
                "form_type": form_type,
                "path": this_path,
                "tag": tag,
                "text_len": len(norm),
                "snippet": norm[:160],
            })
        for child in el:
            visit(child, this_path)

    visit(root, "")
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-size", type=int, default=24)
    ap.add_argument("--batch-id", default=None, help="Override auto-picked most-recent batch")
    args = ap.parse_args()

    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    print("Fetching current submission-year index (2026)...")
    resp = requests.get(f"{INDEX_BASE}/2026/index_2026.csv", timeout=120)
    resp.raise_for_status()
    all_rows = list(csv.DictReader(io.StringIO(resp.text)))

    batch_counts = Counter(r["XML_BATCH_ID"] for r in all_rows)
    batch_id = args.batch_id or max(batch_counts, key=lambda b: (b, batch_counts[b]))
    print(f"Using batch {batch_id} ({batch_counts[batch_id]:,} filings in index)")

    batch_rows = [r for r in all_rows if r["XML_BATCH_ID"] == batch_id]
    print(f"Selecting a diverse sample of {args.sample_size} EINs...")
    sample = pick_sample_eins(batch_rows, args.sample_size)
    print(f"  Selected {len(sample)}: " + ", ".join(
        f"{r['ein']}({r['RETURN_TYPE']},{r.get('ntee1','?')})" for r in sample))

    zip_path = download_batch(batch_id)
    extracted = extract_filings(zip_path, sample)
    print(f"Extracted {len(extracted)}/{len(sample)} filings")

    all_findings = []
    per_form_tag_stats: dict[str, Counter] = defaultdict(Counter)
    for row in extracted:
        try:
            findings = walk_narrative_fields(row["local_path"], row["RETURN_TYPE"])
        except ET.ParseError as e:
            print(f"  PARSE ERROR {row['ein']}: {e}")
            continue
        for f in findings:
            f["ein"] = row["ein"]
            per_form_tag_stats[row["RETURN_TYPE"]][f["path"]] += 1
        all_findings.extend(findings)

    # Manifest: what we actually sampled, for reproducibility.
    with open(OUTPUT_MANIFEST, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ein", "form_type", "tax_period", "ntee1", "mission_source", "revenue", "object_id"])
        for row in extracted:
            w.writerow([row["ein"], row["RETURN_TYPE"], row["TAX_PERIOD"], row.get("ntee1", ""),
                        row.get("mission_source", ""), row.get("revenue", ""), row["OBJECT_ID"]])

    # Aggregate: distinct field paths seen, by form type, with example snippet + frequency.
    path_examples: dict[str, dict] = {}
    for f in all_findings:
        key = (f["form_type"], f["path"])
        if key not in path_examples or f["text_len"] > path_examples[key]["text_len"]:
            path_examples[key] = f

    write_inventory_doc(per_form_tag_stats, path_examples, extracted, batch_id)
    print(f"\nWrote {OUTPUT_INVENTORY}")
    print(f"Wrote {OUTPUT_MANIFEST}")
    print(f"Raw XML samples in {SAMPLE_DIR}/")


def write_inventory_doc(per_form_tag_stats, path_examples, extracted, batch_id):
    lines = [
        "# 990 XML Narrative Field Inventory (Phase 1)",
        "",
        f"Generated from IRS batch `{batch_id}` "
        f"({len(extracted)} sampled filings across "
        f"{sorted(set(r['RETURN_TYPE'] for r in extracted))}).",
        "",
        "Programmatic walk of every sampled filing's full XML tree. A row here means "
        "the element appeared with non-trivial text in at least one sampled filing. "
        "Not every field is useful to Daanaa -- see the Verdict column.",
        "",
    ]
    for form_type in sorted(per_form_tag_stats.keys()):
        n_filings = sum(1 for r in extracted if r["RETURN_TYPE"] == form_type)
        lines.append(f"## {form_type} ({n_filings} sampled filings)")
        lines.append("")
        lines.append("| Path | Seen in N filings | Max text len | Example snippet |")
        lines.append("|---|---|---|---|")
        rows = [(path, count) for path, count in per_form_tag_stats[form_type].items()]
        rows.sort(key=lambda x: -x[1])
        for path, count in rows:
            ex = path_examples.get((form_type, path))
            snippet = ex["snippet"].replace("|", "\\|") if ex else ""
            max_len = ex["text_len"] if ex else 0
            lines.append(f"| `{path}` | {count} | {max_len} | {snippet} |")
        lines.append("")

    OUTPUT_INVENTORY.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_INVENTORY.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
