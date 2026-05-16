import json
from pathlib import Path
from collections import Counter

BASE_DIR = Path.home() / "meritgiving"
PROPUBLICA_DIR = BASE_DIR / "data" / "propublica_cache"
OUTPUT_DIR = BASE_DIR / "data"

def main():
    print("MERIT Enrichment v2")
    print("=" * 50)

    if not PROPUBLICA_DIR.exists():
        print(f"ERROR: Not found: {PROPUBLICA_DIR}")
        return

    files = list(PROPUBLICA_DIR.glob("*.json"))
    print(f"Scanning {len(files):,} files...")

    stats = {"total": len(files), "with_ntee": 0, "with_ruling": 0,
             "with_foundation": 0, "with_revenue": 0, "with_assets": 0,
             "with_extracts": 0, "with_pdf": 0, "errors": 0,
             "subsection": Counter(), "foundation": Counter(),
             "status": Counter(), "ruling_years": Counter()}

    enrichment = {}
    ruling_dates = {}
    foundation_types = {}
    pdf_links = {}
    revenue_data = {}

    foundation_meanings = {
        10: "Church", 11: "School", 12: "Hospital",
        15: "Public Charity", 16: "Supporting Organization",
        17: "Public Charity (509a2)", 18: "Public Charity (509a3)",
        2: "Private Foundation", 3: "Private Foundation",
        4: "Private Foundation", 9: "Supporting Organization",
    }

    for i, filepath in enumerate(files):
        if i % 5000 == 0 and i > 0:
            print(f"  {i:,}/{len(files):,}...")

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
        except Exception:
            stats["errors"] += 1
            continue

        ein = filepath.stem
        org = data.get("organization", {})
        filings = data.get("filings_with_data", [])

        record = {"ein": ein}

        # NTEE code
        ntee = org.get("ntee_code")
        if ntee and str(ntee).strip():
            record["ntee_code"] = str(ntee).strip()
            stats["with_ntee"] += 1

        # Ruling date (year founded)
        ruling = org.get("ruling_date")
        if ruling and str(ruling).strip():
            record["ruling_date"] = str(ruling).strip()
            ruling_dates[ein] = str(ruling).strip()
            stats["with_ruling"] += 1
            year = str(ruling)[:4]
            if year.isdigit():
                stats["ruling_years"][year] += 1

        # Foundation code
        fc = org.get("foundation_code")
        if fc is not None:
            record["foundation_code"] = fc
            record["foundation_type"] = foundation_meanings.get(fc, f"Code {fc}")
            foundation_types[ein] = record["foundation_type"]
            stats["with_foundation"] += 1
            stats["foundation"][str(fc)] += 1

        # Subsection code
        sc = org.get("subsection_code")
        if sc is not None:
            stats["subsection"][str(sc)] += 1
            record["subsection_code"] = sc

        # Status code
        st = org.get("exempt_organization_status_code")
        if st is not None:
            stats["status"][str(st)] += 1
            record["status_code"] = st

        # Revenue (numeric)
        rev = org.get("revenue_amount")
        if rev is not None and rev != 0:
            record["revenue_amount"] = rev
            revenue_data[ein] = rev
            stats["with_revenue"] += 1

        # Assets
        asset = org.get("asset_amount")
        if asset is not None and asset != 0:
            record["asset_amount"] = asset
            stats["with_assets"] += 1

        # 990 availability
        if org.get("have_extracts"):
            record["have_extracts"] = True
            stats["with_extracts"] += 1
        if org.get("have_pdfs"):
            record["have_pdfs"] = True
            stats["with_pdf"] += 1

        # PDF URLs
        pdfs = []
        for filing in filings:
            if isinstance(filing, dict) and filing.get("pdf_url"):
                pdfs.append(filing["pdf_url"])
        if pdfs:
            record["pdf_urls"] = pdfs[:5]
            pdf_links[ein] = pdfs[:5]

        # Care-of name (DBA)
        careof = org.get("careofname")
        if careof and isinstance(careof, str) and careof.strip() and careof.strip() != "%":
            record["careofname"] = careof.strip().lstrip("% ").strip()

        enrichment[ein] = record

    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_DIR / "enrichment_v2.json", "w") as f:
        json.dump(enrichment, f, indent=2)
    with open(OUTPUT_DIR / "ruling_dates.json", "w") as f:
        json.dump(ruling_dates, f, indent=2)
    with open(OUTPUT_DIR / "foundation_types.json", "w") as f:
        json.dump(foundation_types, f, indent=2)
    with open(OUTPUT_DIR / "pdf_links.json", "w") as f:
        json.dump(pdf_links, f, indent=2)
    with open(OUTPUT_DIR / "revenue_numeric.json", "w") as f:
        json.dump(revenue_data, f, indent=2)

    def pct(key):
        return f"{stats[key] / stats['total'] * 100:.1f}%" if stats['total'] else "N/A"

    print(f"\n{'=' * 50}")
    print(f"RESULTS")
    print(f"  Total orgs:           {stats['total']:,}")
    print(f"  With NTEE code:       {stats['with_ntee']:,} ({pct('with_ntee')})")
    print(f"  With ruling date:     {stats['with_ruling']:,} ({pct('with_ruling')})")
    print(f"  With foundation type: {stats['with_foundation']:,} ({pct('with_foundation')})")
    print(f"  With revenue (num):   {stats['with_revenue']:,} ({pct('with_revenue')})")
    print(f"  With assets:          {stats['with_assets']:,} ({pct('with_assets')})")
    print(f"  With 990 extracts:    {stats['with_extracts']:,} ({pct('with_extracts')})")
    print(f"  With 990 PDFs:        {stats['with_pdf']:,} ({pct('with_pdf')})")
    print(f"  With PDF links:       {len(pdf_links):,}")
    print(f"\n  Subsection (501c type):")
    for code, count in stats["subsection"].most_common():
        print(f"    {code}: {count:,}")
    print(f"\n  Foundation types (top):")
    for code, count in stats["foundation"].most_common(8):
        meaning = foundation_meanings.get(int(code), f"Code {code}")
        print(f"    {code}: {count:,} — {meaning}")
    print(f"\n  Status codes:")
    for code, count in stats["status"].most_common():
        print(f"    {code}: {count:,}")
    print(f"\n  Ruling years (top 10):")
    for year, count in stats["ruling_years"].most_common(10):
        print(f"    {year}: {count:,}")
    print(f"\n  MISSING (not in cache):")
    print(f"    website: 0.0% — NOT in ProPublica cache")
    print(f"    mission: 0.0% — NOT in ProPublica cache")
    print(f"    phone:   0.0% — NOT in ProPublica cache")
    print(f"\nSaved all outputs to ~/meritgiving/data/")

if __name__ == "__main__":
    main()
