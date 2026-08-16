#!/usr/bin/env python3
"""
Compute 9 similar orgs per org from each organization's persisted v6 peer
group (scoring_tier) -- the exact same NTEE2 x band x Census region criteria
Financial Context states to donors on the org detail page.

Rewritten 2026-08-16: the previous version matched on NTEECC + city/state
(location-aware, no size or region-of-record concept), which disagreed with
what Financial Context told donors this org was being compared against.
This is the precomputed FALLBACK path (used only when the live
/api/organizations/:ein/similar endpoint returns nothing, per
OrganizationDetail.tsx:404-410) -- if it used different criteria than the
live API, the fallback would silently reintroduce the exact drift the fix
was for. See DECISIONS.md 2026-08-16 and scripts/scoring/peer_group.py,
which both this script and the live API import from.

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

Parallelized 2026-08-16: the single-threaded version was killed after 6h
having written only ~4.3GB of an estimated ~16-18GB (confirmed CPU-bound at
91%+ on one core via /proc/<pid>/io, not I/O-bound -- NVMe disk otherwise
idle, 16 logical cores mostly unused). Pass 2 is now parallelized with
Linux's fork multiprocessing start method. The parent completes Pass 1 and
builds the large org/index dicts before workers are forked, so workers
inherit them through copy-on-write rather than pickling or re-sending ~2M
entries to each process -- the same pattern gunicorn's --preload uses for
embeddings (see CLAUDE.md's "Embedding load" section).
"""
import argparse
import gzip
import json
import multiprocessing as mp
import os
import signal
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from scripts.scoring import peer_group

# Matches precompute_orgs.py's env var so this script honors the same
# sandbox when invoked from safe_deploy_droplet.sh (PRECOMPUTE_OUT points
# at the deploy's scratch dir, not the repo's live precompute_output/).
_OUT = os.environ.get("PRECOMPUTE_OUT", "precompute_output")
ORGS_DIR = Path(_OUT) / "orgs"
SIMILAR_COUNT = 9

DB_PATH = os.environ.get("DAANAA_DB_PATH", "data/merit_registry.db")

# Leave significant CPU headroom on the 16-logical-core production machine
# while matching the repository's established 6-worker convention for
# similar-scale work (see scripts/enrichment/missions/generate_missions.py).
MAX_DEFAULT_WORKERS = 6
CPU_HEADROOM = 2
PASS2_CHUNK_SIZE = 1_000
PROGRESS_INTERVAL = 100_000

# These are assigned in the parent after Pass 1/index construction and before
# Pool creation. With Linux fork, workers inherit them without pickling.
_PASS2_ORGS = None
_PASS2_INDEXES = None
_PASS2_TIER_FIELDS_BY_EIN = None
_PASS2_DRY_RUN = False

# precompute_orgs.py (the script that generates these per-org JSON files in
# the first place) has never selected scoring_tier/tier_label from the DB at
# all, and only ever writes merit_archetype_v5_label nested inside
# v5_context (gated on the older v5 archetype column, not a flat top-level
# field). Found 2026-08-16 while wiring this script to the new peer-group
# criteria: every precomputed org file had scoring_tier=None, so
# peer_group.peer_group_criteria() would have returned None for virtually
# every org and silently emptied out similar_organizations everywhere.
# Rather than risk a second script (precompute_orgs.py runs the OOM-prone
# full org build -- not something to touch for a 3-field gap), this loads
# the 3 missing fields straight from SQLite (cheap: ~2M rows x 3 short
# strings) and both (a) overlays them onto the in-memory slim dict so
# matching works correctly this run, and (b) patches them into each org's
# persisted file during Pass 2's write-back, so the underlying gap is fixed
# going forward too, not just papered over for this one run.
TIER_FIELDS = ("scoring_tier", "tier_label", "merit_archetype_v5_label")


def default_worker_count():
    """Choose a conservative default while retaining useful parallelism."""
    cpu_count = os.cpu_count() or 1
    return min(MAX_DEFAULT_WORKERS, max(1, cpu_count - CPU_HEADROOM))


def load_tier_fields_from_db():
    print(f"  Loading {', '.join(TIER_FIELDS)} from {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        f"SELECT EIN, {', '.join(TIER_FIELDS)} FROM registry_enriched WHERE EIN IS NOT NULL"
    )
    fields = {row[0]: dict(zip(TIER_FIELDS, row[1:])) for row in cur}
    conn.close()
    print(f"  Loaded tier fields for {len(fields)} EINs")
    return fields


# Every field the frontend consumes from a similar-org entry (adaptOrg in
# OrganizationDetail.tsx) plus what this script needs for peer-group
# matching (scoring_tier, merit_archetype_v5_label), ranking
# (merit_percentile_v6, cause_tags), and the diamonds filter (is_hidden_gem).
SLIM_FIELDS = (
    "EIN", "organization_name", "CITY", "STATE", "NTEE1", "NTEECC",
    "mission", "mission_source", "website",
    "total_revenue", "revenue_band", "latest_tax_year", "updated_at",
    "data_source", "merit_score", "merit_tier", "merit_band",
    "peer_percentile", "peer_rank", "peer_total", "peer_group",
    "ntee1_percentile", "cause_tags", "is_hidden_gem",
    "scoring_tier", "merit_archetype_v5_label", "merit_percentile_v6",
)


# ─── Pass 1: stream slim org data from pre-computed files ──────────────────

def load_slim_orgs(tier_fields_by_ein):
    print("  Pass 1: streaming slim org data (memory-safe)...")
    orgs = {}
    count = 0
    for f in ORGS_DIR.rglob("*.json.gz"):
        try:
            with gzip.open(f, "rt", encoding="utf-8") as fp:
                d = json.load(fp)
            ein = d.get("EIN")
            if ein:
                slim = {k: d[k] for k in SLIM_FIELDS if k in d}
                # DB is the freshest source for these 3 fields -- the
                # precomputed file's own copy (if any) is never newer.
                slim.update(tier_fields_by_ein.get(ein, {}))
                orgs[ein] = slim
            count += 1
            if count % 200000 == 0:
                print(
                    f"    [{datetime.now().strftime('%H:%M:%S')}] "
                    f"streamed {count} files...",
                    flush=True,
                )
        except Exception:
            pass
    print(f"  Loaded {len(orgs)} slim orgs")
    return orgs


# ─── Build lookup indexes ──────────────────────────────────────────────────

def _criteria_key(criteria):
    """Turn a peer_group.peer_group_criteria() dict into a hashable index key."""
    tier = criteria["tier"]
    if tier == "1_Full_Context":
        return criteria["ntee2"], criteria["band"], criteria["region"]
    if tier == "2_Regional_Context":
        return criteria["ntee2"], criteria["band"]
    if tier == "3_Broad_Category":
        return (criteria["ntee2"],)
    if tier == "3b_Broad_Category":
        return criteria["ntee1"], criteria["band"]
    if tier == "4_Archetype_Only":
        return criteria["archetype"], criteria["band"]
    raise ValueError(f"Unsupported peer-group tier: {tier}")


def _org_criteria(o):
    return peer_group.peer_group_criteria(
        o.get("scoring_tier"),
        (o.get("NTEECC") or "").upper() or None,
        (o.get("STATE") or "").upper() or None,
        o.get("total_revenue"),
        o.get("merit_archetype_v5_label"),
    )


def build_indexes(orgs):
    print("  Building v6 peer-group lookup indexes...")
    # One index per tier -- an org is looked up ONLY in its own tier's
    # index (no cascading to a broader tier), matching the live API's
    # no-fallback behavior so the precomputed path can't drift from it.
    indexes = {
        "1_Full_Context": defaultdict(list),
        "2_Regional_Context": defaultdict(list),
        "3_Broad_Category": defaultdict(list),
        "3b_Broad_Category": defaultdict(list),
        "4_Archetype_Only": defaultdict(list),
    }

    for ein, o in orgs.items():
        criteria = _org_criteria(o)
        if criteria is not None:
            indexes[criteria["tier"]][_criteria_key(criteria)].append(ein)

    return indexes


def tags_overlap(org, candidate):
    t1 = set(org.get("cause_tags") or [])
    t2 = set(candidate.get("cause_tags") or [])
    if not t1 or not t2:
        return 0
    return len(t1 & t2)


def score_key(candidate, org):
    """Higher = better match within the organization's own peer group."""
    tag_bonus = tags_overlap(org, candidate) * 10
    org_pct = org.get("merit_percentile_v6")
    cand_pct = candidate.get("merit_percentile_v6")
    if org_pct is not None and cand_pct is not None:
        # Closer percentile = better; invert distance so higher is better.
        return tag_bonus - abs(cand_pct - org_pct)
    return tag_bonus + (candidate.get("merit_score") or 0)


def find_similar(ein, org, orgs, indexes):
    criteria = _org_criteria(org)
    if criteria is None:
        return []

    candidate_eins = indexes[criteria["tier"]].get(_criteria_key(criteria), [])
    candidates = [e for e in candidate_eins if e != ein]
    if not candidates:
        return []

    candidates.sort(key=lambda e: score_key(orgs.get(e, {}), org), reverse=True)

    # Specificity score reflects how tight the shared peer group is, not
    # geography -- region (tier 1) is now part of the peer-group definition
    # itself, so there's no separate "same NTEECC, different tier" case the
    # old code's tier 2/3 distinguished.
    specificity = {
        "1_Full_Context": 1.0,
        "2_Regional_Context": 0.85,
        "3_Broad_Category": 0.7,
        "3b_Broad_Category": 0.7,
        "4_Archetype_Only": 0.5,
    }[criteria["tier"]]
    # is_local: true only for tier 1, the only tier with a region component.
    # The frontend must not claim a locality relationship for broader tiers
    # (2026-07-10 eng review finding — the old code made that claim
    # regardless of tier; the same rule now applies to the region concept).
    is_local = criteria["tier"] == "1_Full_Context"

    # Take top SIMILAR_COUNT — embed SLIM entries only (never the full dict)
    result = []
    for e in candidates[:SIMILAR_COUNT]:
        c = orgs.get(e)
        if c:
            entry = dict(c)
            entry["similarity_score"] = specificity
            entry["is_local"] = is_local
            result.append(entry)

    return result


# ─── Pass 2: parallel patching ─────────────────────────────────────────────

def _write_gzip_atomically(f_path, full):
    """
    Write beside the destination, then atomically replace it.

    The prior direct gzip.open(f_path, "wt") overwrite could leave a target
    truncated if interrupted. A same-directory os.replace() is atomic on the
    local filesystem: interruption can leave only a disposable temp file while
    the prior complete target remains intact.
    """
    temp_path = f_path.with_name(f".{f_path.name}.{os.getpid()}.tmp")
    try:
        with gzip.open(temp_path, "wt", encoding="utf-8", compresslevel=1) as fp:
            json.dump(full, fp, separators=(",", ":"))
        os.replace(temp_path, f_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _process_ein_chunk(eins):
    """
    Process a small chunk using only fork-inherited Pass 1 structures.

    Only the short EIN chunk is sent through Pool's task queue; orgs, indexes,
    and DB tier fields are inherited by copy-on-write and never re-pickled.
    """
    processed = 0
    updated = 0
    tier_fields_backfilled = 0

    for ein in eins:
        org = _PASS2_ORGS[ein]
        similar = find_similar(ein, org, _PASS2_ORGS, _PASS2_INDEXES)

        # Read the org's file, patch only if changed, write back.
        ein_prefix = ein[:3]
        f_path = ORGS_DIR / ein_prefix / f"{ein}.json.gz"
        try:
            with gzip.open(f_path, "rt", encoding="utf-8") as fp:
                full = json.load(fp)
        except Exception:
            processed += 1
            continue

        changed = similar != full.get("similar_organizations", [])
        if changed:
            full["similar_organizations"] = similar

        # Backfill scoring_tier/tier_label/merit_archetype_v5_label into the
        # persisted file too -- precompute_orgs.py never wrote these as flat
        # fields (see TIER_FIELDS comment above), so every file was carrying
        # a permanent gap independent of this script's own similar-orgs job.
        db_tier_fields = _PASS2_TIER_FIELDS_BY_EIN.get(ein, {})
        for field, value in db_tier_fields.items():
            if value is not None and full.get(field) != value:
                full[field] = value
                changed = True
                tier_fields_backfilled += 1

        if changed:
            if not _PASS2_DRY_RUN:
                _write_gzip_atomically(f_path, full)
            updated += 1

        processed += 1

    return processed, updated, tier_fields_backfilled


def _ein_chunks(eins, chunk_size):
    """Yield bounded EIN chunks for balanced Pass 2 work distribution."""
    chunk = []
    for ein in eins:
        chunk.append(ein)
        if len(chunk) == chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def _ignore_keyboard_interrupt():
    """Let the parent coordinate Ctrl+C cleanup for the worker pool."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


# ─── Main ─────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Precompute similar nonprofit organizations from v6 peer groups."
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=default_worker_count(),
        help=(
            "Pass 2 worker processes "
            f"(default: {default_worker_count()}, based on os.cpu_count() with headroom)"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute and report Pass 2 changes without writing any org files.",
    )
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be at least 1")
    return args


def main():
    global _PASS2_ORGS
    global _PASS2_INDEXES
    global _PASS2_TIER_FIELDS_BY_EIN
    global _PASS2_DRY_RUN

    args = parse_args()
    timestamp = datetime.now().isoformat()
    print(
        f"[{timestamp}] Computing {SIMILAR_COUNT} similar orgs per org "
        "(v6 peer group, memory-safe)..."
    )

    tier_fields_by_ein = load_tier_fields_from_db()
    orgs = load_slim_orgs(tier_fields_by_ein)
    if not orgs:
        print("ERROR: No orgs loaded. Run precompute_orgs.py first.")
        return

    indexes = build_indexes(orgs)

    # Assign all large structures before Pool creation. Linux fork workers
    # inherit these allocations through copy-on-write.
    _PASS2_ORGS = orgs
    _PASS2_INDEXES = indexes
    _PASS2_TIER_FIELDS_BY_EIN = tier_fields_by_ein
    _PASS2_DRY_RUN = args.dry_run

    total = len(orgs)
    processed = 0
    updated = 0
    tier_fields_backfilled = 0
    next_progress = PROGRESS_INTERVAL

    mode = "computing (dry run; no writes)" if args.dry_run else "computing + patching"
    print(
        f"  Pass 2: {mode} {total} org files with {args.workers} worker(s) "
        f"(chunk size {PASS2_CHUNK_SIZE})...",
        flush=True,
    )

    # Explicitly request fork: this deployment target is Linux, and fork is
    # essential for sharing the already-built Pass 1 structures via CoW.
    context = mp.get_context("fork")
    try:
        with context.Pool(
            processes=args.workers,
            initializer=_ignore_keyboard_interrupt,
        ) as pool:
            chunks = _ein_chunks(orgs.keys(), PASS2_CHUNK_SIZE)
            for chunk_processed, chunk_updated, chunk_backfilled in pool.imap_unordered(
                _process_ein_chunk,
                chunks,
                chunksize=1,
            ):
                processed += chunk_processed
                updated += chunk_updated
                tier_fields_backfilled += chunk_backfilled

                while processed >= next_progress:
                    pct = processed / total * 100
                    print(
                        f"  [{datetime.now().strftime('%H:%M:%S')}] "
                        f"{processed}/{total} ({pct:.1f}%) | updated: {updated} | "
                        f"tier fields backfilled: {tier_fields_backfilled}",
                        flush=True,
                    )
                    next_progress += PROGRESS_INTERVAL
    except KeyboardInterrupt:
        print(
            "\nInterrupted. Completed files are intact; any in-progress write "
            "was isolated in a temporary file.",
            flush=True,
        )
        return

    print(f"\n[{datetime.now().isoformat()}] Done!")
    if args.dry_run:
        print(
            f"  Total: {total} orgs, {updated} files would be updated, "
            f"{tier_fields_backfilled} tier-field values would be backfilled"
        )
    else:
        print(
            f"  Total: {total} orgs, {updated} files updated, "
            f"{tier_fields_backfilled} tier-field values backfilled"
        )
    total_size = sum(f.stat().st_size for f in ORGS_DIR.rglob("*") if f.is_file())
    print(f"  Disk: {total_size / 1024 / 1024:.0f} MB")
    print(f"\n  Next step: rsync orgs/ to droplet and restart search.db")


if __name__ == "__main__":
    main()
