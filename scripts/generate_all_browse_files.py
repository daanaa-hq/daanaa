#!/usr/bin/env python3
"""
Generate ALL_*.json.gz browse files by aggregating existing state-specific files.
Reads from precompute_output/browse/NTEE1/STATE_*.json.gz and writes ALL_*.json.gz.
No database required — works from existing pre-computed files.
"""
import gzip
import json
from pathlib import Path
from datetime import datetime

BROWSE_DIR = Path("precompute_output/browse")
PAGE_SIZE = 25


def load_gz(path):
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def write_gz(path, data):
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=1) as f:
        json.dump(data, f, separators=(",", ":"))


def main():
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] Generating ALL-state browse files from existing state files...")

    categories = sorted([d.name for d in BROWSE_DIR.iterdir() if d.is_dir() and len(d.name) == 1])
    print(f"  Categories found: {categories}")

    total_files = 0
    total_orgs = 0

    for cat in categories:
        cat_dir = BROWSE_DIR / cat
        state_files = sorted(cat_dir.glob("*.json.gz"))

        # Skip files that are already ALL_ files
        state_files = [f for f in state_files if not f.name.startswith("ALL_")]

        print(f"  [{cat}] Loading from {len(state_files)} state files...", end="", flush=True)

        # Collect all orgs across all states
        seen_eins = set()
        all_orgs = []

        for sf in state_files:
            data = load_gz(sf)
            if not data or not data.get("organizations"):
                continue
            for org in data["organizations"]:
                ein = org.get("EIN")
                if ein and ein not in seen_eins:
                    seen_eins.add(ein)
                    all_orgs.append(org)

        if not all_orgs:
            print(f" 0 orgs, skipping")
            continue

        # Sort by merit_score DESC (nulls last), then total_revenue DESC
        all_orgs.sort(
            key=lambda o: (
                -(o.get("merit_score") or o.get("peer_percentile") or o.get("ntee1_percentile") or 0),
                -(o.get("total_revenue") or 0),
            )
        )

        num_pages = (len(all_orgs) + PAGE_SIZE - 1) // PAGE_SIZE
        print(f" {len(all_orgs):,} orgs → {num_pages} ALL-state pages")

        for page_num in range(1, num_pages + 1):
            start = (page_num - 1) * PAGE_SIZE
            page_orgs = all_orgs[start:start + PAGE_SIZE]

            response = {
                "organizations": page_orgs,
                "total": len(all_orgs),
                "page": page_num,
                "per_page": PAGE_SIZE,
                "pages": num_pages,
            }

            out = cat_dir / f"ALL_{page_num}.json.gz"
            write_gz(out, response)
            total_files += 1
            total_orgs += len(page_orgs)

        total_orgs += 0  # already counted above

    print(f"\n[{datetime.now().isoformat()}] Done!")
    print(f"  ALL files written: {total_files}")
    size = sum(f.stat().st_size for f in BROWSE_DIR.rglob("ALL_*.json.gz"))
    print(f"  Disk: {size / 1024 / 1024:.0f} MB")
    print(f"\n  Next step: bash scripts/deploy_browse.sh")


if __name__ == "__main__":
    main()
