#!/usr/bin/env python3
"""
Generate the bi-weekly cause-spotlight data — automatically, from the registry.

READ-ONLY on merit_registry.db (no writes → never competes with the pipeline).
For every NTEE1 category that has a logo asset in frontend/public/categories/,
it computes the landscape stats + the top hidden gems and writes a single static
file: frontend/public/cause-spotlights.json. The page reads that file (droplet-
safe, like research-snapshot.json) so new categories light up the moment their
logo lands — no per-category hand-editing.

Stewardship alignment: only evidence-based public data; hidden gems are the
transparent, documented rule (small + high peer rank + has a mission); every
category is treated equally (same query, same shape). Creative copy (taglines)
stays human in frontend/src/data/featuredCategory.ts — we generate data, not voice.

  python3 scripts/generate_cause_spotlights.py
"""
import json, sqlite3
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "data" / "merit_registry.db"
LOGO_DIR = BASE / "frontend" / "public" / "categories"
OUT = BASE / "frontend" / "public" / "cause-spotlights.json"

# Hidden gem rule (documented in flag_hidden_gems.py / DECISIONS): small, ranks
# high among true peers, has a readable story.
GEM = ("merit_score >= 85 AND total_revenue < 500000 "
       "AND mission IS NOT NULL AND TRIM(mission) <> ''")

FEATURED_PER_CATEGORY = 3

NTEE1_NAMES = {
    'A': 'Arts & Culture', 'B': 'Education', 'C': 'Environment', 'D': 'Animals',
    'E': 'Health', 'F': 'Mental Health', 'G': 'Disease & Disorders', 'H': 'Medical Research',
    'I': 'Crime & Legal', 'J': 'Employment', 'K': 'Food & Agriculture', 'L': 'Housing',
    'M': 'Public Safety & Relief', 'N': 'Recreation & Sports', 'O': 'Youth Development',
    'P': 'Human Services', 'Q': 'International', 'R': 'Civil Rights', 'S': 'Community Development',
    'T': 'Philanthropy', 'U': 'Science', 'V': 'Social Science', 'W': 'Public Benefit',
    'X': 'Religion', 'Y': 'Mutual Benefit', 'Z': 'Unknown',
}


def logo_categories():
    if not LOGO_DIR.exists():
        return []
    return sorted({p.stem.upper() for p in LOGO_DIR.glob("*.png")
                   if len(p.stem) == 1 and p.stem.isalpha()})


def main():
    con = sqlite3.connect(DB, timeout=120)
    cats = logo_categories()
    print(f"[{datetime.now():%H:%M:%S}] generating spotlights for: {cats}", flush=True)

    out = {"generated_at": datetime.now(timezone.utc).isoformat(), "categories": {}}
    for c in cats:
        total = con.execute("SELECT COUNT(*) FROM registry_enriched WHERE NTEE1=?", (c,)).fetchone()[0]
        if not total:
            continue
        with_ctx = con.execute(
            "SELECT COUNT(*) FROM registry_enriched WHERE NTEE1=? AND merit_score IS NOT NULL", (c,)
        ).fetchone()[0]
        top_states = [
            {"state": s, "count": n}
            for s, n in con.execute(
                "SELECT STATE, COUNT(*) FROM registry_enriched WHERE NTEE1=? AND STATE IS NOT NULL "
                "GROUP BY STATE ORDER BY COUNT(*) DESC LIMIT 5", (c,)
            ).fetchall()
        ]
        featured = []
        for ein, name, city, state, mission in con.execute(
            f"SELECT EIN, organization_name, CITY, STATE, mission FROM registry_enriched "
            f"WHERE NTEE1=? AND {GEM} ORDER BY merit_score DESC, total_revenue ASC LIMIT ?",
            (c, FEATURED_PER_CATEGORY),
        ).fetchall():
            featured.append({
                "ein": ein, "name": (name or "").strip(),
                "city": (city or "").strip(), "state": (state or "").strip(),
                "blurb": (mission or "").strip()[:160],
            })
        out["categories"][c] = {
            "id": c, "name": NTEE1_NAMES.get(c, c),
            "totalOrgs": total, "withContext": with_ctx,
            "topStates": top_states, "featured": featured,
        }
        print(f"  {c} ({NTEE1_NAMES.get(c, c)}): {total:,} orgs, {len(featured)} gems", flush=True)

    con.close()
    OUT.write_text(json.dumps(out, indent=2))
    print(f"[{datetime.now():%H:%M:%S}] wrote {OUT} ({OUT.stat().st_size // 1024} KB)", flush=True)


if __name__ == "__main__":
    main()
