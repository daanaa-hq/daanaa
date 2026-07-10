#!/usr/bin/env python3
"""
Compute 9 similar orgs per org using location-aware matching.
Matching priority: same NTEECC + same city > same NTEECC + same state > same NTEE1 + same state.
Tiebreaker: cause_tags overlap, then merit_score desc.
Monthly re-run on home server; upload org files to droplet.
"""
import gzip
import json
import os
import random
from collections import defaultdict
from pathlib import Path
from datetime import datetime

# Matches precompute_orgs.py's env var so this script honors the same
# sandbox when invoked from safe_deploy_droplet.sh (PRECOMPUTE_OUT points
# at the deploy's scratch dir, not the repo's live precompute_output/).
_OUT = os.environ.get("PRECOMPUTE_OUT", "precompute_output")
ORGS_DIR = Path(_OUT) / "orgs"
BROWSE_DIR = Path(_OUT) / "browse"
SIMILAR_COUNT = 9

# ─── Load all orgs from pre-computed files ────────────────────────────────

def load_all_orgs():
    print("  Loading all org data from pre-computed files...")
    orgs = {}
    for f in ORGS_DIR.rglob("*.json.gz"):
        try:
            with gzip.open(f, "rt", encoding="utf-8") as fp:
                d = json.load(fp)
            ein = d.get("EIN")
            if ein:
                orgs[ein] = d
        except Exception:
            pass
    print(f"  Loaded {len(orgs)} orgs")
    return orgs


# ─── Build lookup indexes ──────────────────────────────────────────────────

def build_indexes(orgs):
    print("  Building lookup indexes...")
    # nteecc → city → [eins]
    by_nteecc_city = defaultdict(lambda: defaultdict(list))
    # nteecc → state → [eins]
    by_nteecc_state = defaultdict(lambda: defaultdict(list))
    # ntee1 → state → [eins]
    by_ntee1_state = defaultdict(lambda: defaultdict(list))
    # ntee1 → all eins (national fallback)
    by_ntee1_all = defaultdict(list)

    for ein, o in orgs.items():
        nteecc = (o.get("NTEECC") or "").upper()
        ntee1 = nteecc[0] if nteecc else (o.get("NTEE1") or "").upper()
        state = (o.get("STATE") or "").upper()
        city = (o.get("CITY") or "").upper()

        if nteecc and state and city:
            by_nteecc_city[nteecc][f"{city}|{state}"].append(ein)
        if nteecc and state:
            by_nteecc_state[nteecc][state].append(ein)
        if ntee1 and state:
            by_ntee1_state[ntee1][state].append(ein)
        if ntee1:
            by_ntee1_all[ntee1].append(ein)

    return by_nteecc_city, by_nteecc_state, by_ntee1_state, by_ntee1_all


def tags_overlap(org, candidate):
    t1 = set(org.get("cause_tags") or [])
    t2 = set(candidate.get("cause_tags") or [])
    if not t1 or not t2:
        return 0
    return len(t1 & t2)


def score_key(candidate, org):
    """Higher = better match."""
    score = candidate.get("merit_score") or 0
    tag_bonus = tags_overlap(org, candidate) * 10
    return score + tag_bonus


def find_similar(ein, org, orgs, by_nteecc_city, by_nteecc_state, by_ntee1_state, by_ntee1_all):
    nteecc = (org.get("NTEECC") or "").upper()
    ntee1 = nteecc[0] if nteecc else (org.get("NTEE1") or "").upper()
    state = (org.get("STATE") or "").upper()
    city = (org.get("CITY") or "").upper()
    city_key = f"{city}|{state}" if city and state else ""

    seen = {ein}
    candidates = []

    # Tier 1: same NTEECC + same city (same work, nearby)
    if nteecc and city_key:
        for e in by_nteecc_city[nteecc].get(city_key, []):
            if e not in seen:
                seen.add(e)
                candidates.append((3, e))

    # Tier 2: same NTEECC + same state
    if nteecc and state:
        for e in by_nteecc_state[nteecc].get(state, []):
            if e not in seen:
                seen.add(e)
                candidates.append((2, e))

    # Tier 3: same NTEE1 + same state (broader category)
    if ntee1 and state:
        for e in by_ntee1_state[ntee1].get(state, []):
            if e not in seen:
                seen.add(e)
                candidates.append((1, e))

    # Tier 4: same NTEE1, any state (national fallback — fills remaining slots)
    if len(candidates) < SIMILAR_COUNT and ntee1:
        for e in by_ntee1_all.get(ntee1, []):
            if e not in seen:
                seen.add(e)
                candidates.append((0, e))
            if len(candidates) >= SIMILAR_COUNT * 3:
                break

    if not candidates:
        return []

    # Sort: tier desc, then tag_overlap + merit_score desc
    candidates.sort(key=lambda x: (x[0], score_key(orgs.get(x[1], {}), org)), reverse=True)

    # Take top SIMILAR_COUNT
    result = []
    for tier, e in candidates[:SIMILAR_COUNT]:
        c = orgs.get(e)
        if c:
            entry = dict(c)
            entry.pop("similar_organizations", None)  # don't nest
            entry["similarity_score"] = 1.0 if tier == 3 else (0.9 if tier == 2 else (0.75 if tier == 1 else 0.6))
            # is_local: tiers 1-3 share the org's city or state; tier 0 is the
            # nationwide NTEE1 fallback with no locality guarantee. The frontend
            # must not claim "near [CITY]" for is_local=False matches (2026-07-10
            # eng review finding — the old code made that claim regardless of tier).
            entry["is_local"] = tier > 0
            result.append(entry)

    return result


# ─── Main ─────────────────────────────────────────────────────────────────

def main():
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] Computing {SIMILAR_COUNT} similar orgs per org (location-aware)...")

    orgs = load_all_orgs()
    if not orgs:
        print("ERROR: No orgs loaded. Run precompute_orgs_from_browse.py first.")
        return

    by_nteecc_city, by_nteecc_state, by_ntee1_state, by_ntee1_all = build_indexes(orgs)

    total = len(orgs)
    processed = 0
    updated = 0

    print(f"  Processing {total} orgs...")
    for ein, org in orgs.items():
        similar = find_similar(ein, org, orgs, by_nteecc_city, by_nteecc_state, by_ntee1_state, by_ntee1_all)

        # Only rewrite if different from current
        current_similar = org.get("similar_organizations", [])
        if similar != current_similar:
            org["similar_organizations"] = similar
            ein_prefix = ein[:3]
            out_dir = ORGS_DIR / ein_prefix
            out_dir.mkdir(parents=True, exist_ok=True)
            with gzip.open(out_dir / f"{ein}.json.gz", "wt", encoding="utf-8", compresslevel=1) as f:
                json.dump(org, f, separators=(",", ":"))
            updated += 1

        processed += 1
        if processed % 100000 == 0:
            pct = processed / total * 100
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] {processed}/{total} ({pct:.1f}%) | updated: {updated}")

    print(f"\n[{datetime.now().isoformat()}] Done!")
    print(f"  Total: {total} orgs, {updated} updated with new similar orgs")
    total_size = sum(f.stat().st_size for f in ORGS_DIR.rglob("*") if f.is_file())
    print(f"  Disk: {total_size / 1024 / 1024:.0f} MB")
    print(f"\n  Next step: rsync orgs/ to droplet and restart search.db")


if __name__ == "__main__":
    main()
