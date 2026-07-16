#!/usr/bin/env python3
"""
Compute 9 similar orgs per org using location-aware matching.
Matching priority: same NTEECC + same city > same NTEECC + same state > same NTEE1 + same state.
Tiebreaker: cause_tags overlap, then merit_score desc.
Monthly re-run on home server; upload org files to droplet.

Memory-safe rewrite (2026-07-16): the previous version loaded all 1.7M FULL
org dicts into RAM (~25GB with Python object overhead) and was OOM-killed on
every full deploy since 2026-07-12 (kernel log: anon-rss 25.3GB, killed).
This version streams two passes:
  Pass 1: read each org file once, keep only SLIM_FIELDS (~2GB total).
  Pass 2: recompute similar lists from the slim index; rewrite only files
          whose similar list changed (read file -> patch field -> write).
Embedded similar entries carry only the fields the frontend's adaptOrg()
actually reads (OrganizationDetail.tsx:155) plus similarity_score/is_local —
NOT the full org dict. This also shrinks the org-file payload shipped to the
droplet.
"""
import gzip
import json
import os
from collections import defaultdict
from pathlib import Path
from datetime import datetime

# Matches precompute_orgs.py's env var so this script honors the same
# sandbox when invoked from safe_deploy_droplet.sh (PRECOMPUTE_OUT points
# at the deploy's scratch dir, not the repo's live precompute_output/).
_OUT = os.environ.get("PRECOMPUTE_OUT", "precompute_output")
ORGS_DIR = Path(_OUT) / "orgs"
SIMILAR_COUNT = 9

# Every field the frontend consumes from a similar-org entry (adaptOrg in
# OrganizationDetail.tsx) plus what this script needs for matching/scoring
# (cause_tags, merit_score) and the diamonds filter (is_hidden_gem).
SLIM_FIELDS = (
    "EIN", "organization_name", "CITY", "STATE", "NTEE1", "NTEECC",
    "mission", "mission_source", "website",
    "total_revenue", "revenue_band", "latest_tax_year", "updated_at",
    "data_source", "merit_score", "merit_tier", "merit_band",
    "peer_percentile", "peer_rank", "peer_total", "peer_group",
    "ntee1_percentile", "cause_tags", "is_hidden_gem",
)


# ─── Pass 1: stream slim org data from pre-computed files ──────────────────

def load_slim_orgs():
    print("  Pass 1: streaming slim org data (memory-safe)...")
    orgs = {}
    count = 0
    for f in ORGS_DIR.rglob("*.json.gz"):
        try:
            with gzip.open(f, "rt", encoding="utf-8") as fp:
                d = json.load(fp)
            ein = d.get("EIN")
            if ein:
                orgs[ein] = {k: d[k] for k in SLIM_FIELDS if k in d}
            count += 1
            if count % 200000 == 0:
                print(f"    [{datetime.now().strftime('%H:%M:%S')}] streamed {count} files...")
        except Exception:
            pass
    print(f"  Loaded {len(orgs)} slim orgs")
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

    # Take top SIMILAR_COUNT — embed SLIM entries only (never the full dict)
    result = []
    for tier, e in candidates[:SIMILAR_COUNT]:
        c = orgs.get(e)
        if c:
            entry = dict(c)
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
    print(f"[{timestamp}] Computing {SIMILAR_COUNT} similar orgs per org (location-aware, memory-safe)...")

    orgs = load_slim_orgs()
    if not orgs:
        print("ERROR: No orgs loaded. Run precompute_orgs.py first.")
        return

    by_nteecc_city, by_nteecc_state, by_ntee1_state, by_ntee1_all = build_indexes(orgs)

    total = len(orgs)
    processed = 0
    updated = 0

    print(f"  Pass 2: computing + patching {total} org files...")
    for ein, org in orgs.items():
        similar = find_similar(ein, org, orgs, by_nteecc_city, by_nteecc_state, by_ntee1_state, by_ntee1_all)

        # Read the org's file, patch only if changed, write back.
        ein_prefix = ein[:3]
        f_path = ORGS_DIR / ein_prefix / f"{ein}.json.gz"
        try:
            with gzip.open(f_path, "rt", encoding="utf-8") as fp:
                full = json.load(fp)
        except Exception:
            processed += 1
            continue

        if similar != full.get("similar_organizations", []):
            full["similar_organizations"] = similar
            with gzip.open(f_path, "wt", encoding="utf-8", compresslevel=1) as fp:
                json.dump(full, fp, separators=(",", ":"))
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
