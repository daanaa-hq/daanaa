#!/usr/bin/env python3
"""
Pre-compute org detail pages for all tax-deductible 501(c)(3) orgs.
Uses FAISS index for similar orgs (no database embeddings required).
Resumes from where it left off — skips existing files.
"""

import sqlite3
import json
import gzip
import os
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    print("WARNING: faiss not installed — similar_orgs will be empty")

# Cause-cohort context for orgs with no financial assessment of their own.
# Baked into the static org JSON so the droplet (which serves precompute files,
# not the live API) can show it. Lookup is a cached dict read — cheap per org.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from enrich_api_responses import get_cohort_context, build_v5_context
except Exception:
    get_cohort_context = None
    build_v5_context = None

DB_PATH = os.environ.get("MERIT_DB_PATH", "data/merit_registry.db")
_OUT = os.environ.get("PRECOMPUTE_OUT", "precompute_output")
FAISS_INDEX_PATH = os.path.join(_OUT, "faiss_index.bin")
EIN_MAP_PATH = os.path.join(_OUT, "ein_map.json.gz")
OUTPUT_DIR = os.path.join(_OUT, "orgs")
SIMILAR_COUNT = 12
BATCH_SIZE = 10000   # Process N orgs per FAISS batch search


def org_to_dict(row):
    d = {
        'EIN': row[0],
        'organization_name': row[1],
        'NTEE1': row[2],
        'NTEECC': row[3],
        'CITY': row[4],
        'STATE': row[5],
        'total_revenue': row[6],
        'total_revenue_formatted': f"${row[6]:,.0f}" if row[6] else None,
        'ntee1_percentile': row[7],
        'ntee1_total_orgs': row[8],
        'source': row[9],
        'zipcode': row[10],
        'street_address': row[11],
        'revenue_band': row[12],
        'peer_percentile': row[13],
        'peer_rank': row[14],
        'peer_total': row[15],
        'peer_group': row[16],
        'latest_tax_year': row[17],
        'data_source': row[18],
        'updated_at': row[19],
        'merit_tier': row[20],
        'merit_score': row[21],
        'merit_band': row[22],
        'financial_health': row[23],
        'months_of_reserve': row[24],
        'net_assets': row[25],
        'total_expenses': row[26],
        'total_liabilities': row[27],
        'employee_count': row[28],
        'program_expense_pct': row[29],
        'ruling_date': row[30],
        'nccs_year': row[31],
        'mission': row[32],
        'mission_source': row[33],
        'website': row[34],
        'website_status': row[35],
        'cause_tags': json.loads(row[36]) if row[36] else None,
        'activ1': row[37],
        'activ2': row[38],
        'activ3': row[39],
        'is_hidden_gem': bool(row[48]) if row[48] is not None else False,
        # donate_url re-scoped 2026-07-07 (superseded the 2026-06-10 blanket
        # omission — see DECISIONS.md): confidence-gated, fail-closed hand-off
        # links only. donate_confidence must be checked by the caller before
        # rendering any donate action (validate_link_integrity.py already
        # gates this same field before every deploy).
        'donate_url': row[49],
        'donate_url_status': row[50],
        'donate_confidence': row[51],
        'donate_platform': row[52],
    }
    # v5.0 peer-based financial context. Built from the org's own v5 fields
    # (archetype=row[40], labels/band/score/health/peer at row[41..47],
    # months_of_reserve=row[24]). build_v5_context returns None when there is no
    # archetype, so scored orgs get the card and unscored orgs don't.
    v5 = None
    if build_v5_context and row[40] is not None:
        try:
            v5 = build_v5_context(
                row[40], row[41], row[42], row[43],
                row[44], row[45], row[46], row[47], row[24],
            )
        except Exception:
            v5 = None
    d['v5_context'] = v5

    # Cause-cohort context: only when this org has NO financial assessment of
    # its own (no v5_context above, no v4 financial_health at row[23]), so it
    # fills a genuinely blank financial section and never competes with a real
    # score (Stewardship P3/P4). NTEE1=row[2], NTEECC=row[3].
    cohort = None
    if get_cohort_context and v5 is None and row[23] is None:
        try:
            cohort = get_cohort_context(row[3], row[2])
        except Exception:
            cohort = None
    d['cohort_context'] = cohort
    return d


def _load_financials_index(conn):
    """Load all financial history rows keyed by EIN. Returns {} if table absent."""
    try:
        rows = conn.execute("""
            SELECT EIN, tax_prd_yr, totrevenue, totfuncexpns, totassetsend,
                   totliabend, totnetassetend, totcntrbgfts, totprgmrevnue,
                   compnsatncurrofcr, pdf_url
            FROM propublica_financials
            ORDER BY EIN, tax_prd_yr DESC
        """).fetchall()
    except Exception:
        return {}
    index = {}
    for r in rows:
        ein = r[0]
        if ein not in index:
            index[ein] = []
        index[ein].append({
            'tax_prd_yr':        r[1],
            'totrevenue':        r[2],
            'totfuncexpns':      r[3],
            'totassetsend':      r[4],
            'totliabend':        r[5],
            'totnetassetend':    r[6],
            'totcntrbgfts':      r[7],
            'totprgmrevnue':     r[8],
            'compnsatncurrofcr': r[9],
            'pdf_url':           r[10],
        })
    return index


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] Pre-computing org detail pages...")

    # Load financial history index once (keyed by EIN)
    print("  Loading financial history index...")
    financials_index = _load_financials_index(conn)
    print(f"  Financial history: {len(financials_index):,} orgs with multi-year data")

    # Check existing files FIRST (before loading all orgs into memory)
    print("  Checking existing files...")
    existing = {f.stem for f in Path(OUTPUT_DIR).rglob('*.json.gz')}
    print(f"  Existing files: {len(existing)}")

    # Count total orgs (without loading them all)
    print("  Counting tax-deductible orgs...")
    cursor.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE EIN IS NOT NULL AND deductibility = 1 AND org_status = 'active'
    """)
    total_orgs = cursor.fetchone()[0]
    print(f"  Total: {total_orgs} tax-deductible orgs")

    # Stream orgs directly without loading all into memory
    # street_address was backfilled 2026-06-11; older snapshots may not have it.
    cols = {r[1] for r in conn.execute("PRAGMA table_info(registry_enriched)").fetchall()}
    street_col = "street_address" if "street_address" in cols else "NULL as street_address"

    print(f"  Streaming {total_orgs} orgs (skipping {len(existing)} existing)...")
    cursor.execute(f"""
        SELECT
            EIN, organization_name, NTEE1, NTEECC, CITY, STATE,
            total_revenue, ntee1_percentile, ntee1_total_orgs, source,
            zipcode, {street_col}, revenue_band, peer_percentile, peer_rank, peer_total, peer_group,
            latest_tax_year, data_source, updated_at, merit_tier, merit_score,
            merit_band, financial_health, months_of_reserve, net_assets,
            total_expenses, total_liabilities, employee_count, program_expense_pct,
            ruling_date, NULL as nccs_year, mission, mission_source, website, website_status,
            cause_tags,
            NULL as activ1, NULL as activ2, NULL as activ3,
            merit_archetype_v5,
            merit_archetype_v5_label, merit_band_v5, merit_band_v5_label,
            merit_score_v5, merit_health_signal_v5, merit_peer_group_v5,
            merit_peer_count_v5, is_hidden_gem,
            donate_url, donate_url_status, donate_confidence, donate_platform
        FROM registry_enriched
        WHERE EIN IS NOT NULL AND deductibility = 1 AND org_status = 'active'
        ORDER BY EIN
    """)

    # Stream and process without FAISS (cursor iteration, not fetchall)
    processed = 0
    for row in cursor:
        ein = row[0]
        if ein in existing:
            continue

        org_data = org_to_dict(row)
        org_data['similar_organizations'] = []
        org_data['financials'] = financials_index.get(ein, [])
        _write_org(org_data)

        processed += 1
        if processed % 100000 == 0:
            pct = (len(existing) + processed) / total_orgs * 100
            print(f"  Processed {processed}/{total_orgs} ({pct:.1f}%)")

    conn.close()
    total_files = len(list(Path(OUTPUT_DIR).rglob('*.json.gz')))
    print(f"\n[{datetime.now().isoformat()}] Done! {processed} new files. Total: {total_files}")
    total_size = sum(f.stat().st_size for f in Path(OUTPUT_DIR).rglob('*') if f.is_file())
    print(f"  Disk usage: {total_size / 1024 / 1024:.1f} MB")


def _write_org(org_data):
    ein = org_data['EIN']
    ein_prefix = ein[:3]
    org_dir = Path(OUTPUT_DIR) / ein_prefix
    org_dir.mkdir(parents=True, exist_ok=True)
    filepath = org_dir / f"{ein}.json.gz"
    with gzip.open(filepath, 'wt', encoding='utf-8', compresslevel=1) as f:
        json.dump(org_data, f, separators=(',', ':'))


def _process_without_similar(orgs_to_process, org_dict, existing, total_orgs):
    processed = 0
    for org_row in orgs_to_process:
        org_data = org_to_dict(org_row)
        org_data['similar_organizations'] = []
        _write_org(org_data)
        processed += 1
        if processed % 100000 == 0:
            pct = (len(existing) + processed) / total_orgs * 100
            print(f"  Processed {processed}/{len(orgs_to_process)} ({pct:.1f}% total)")
    print(f"  Complete: {processed} orgs written")


def _process_with_reconstruction(orgs_to_process, org_dict, index, ein_map, ein_to_pos):
    total = len(orgs_to_process)
    processed = 0
    no_vec = 0
    d = 1024

    for i in range(0, total, BATCH_SIZE):
        batch = orgs_to_process[i:i + BATCH_SIZE]

        # Build query matrix for this batch
        query_eins = []
        query_vecs = []
        no_vec_rows = []

        for row in batch:
            ein = row[0]
            pos = ein_to_pos.get(ein)
            if pos is not None:
                vec = np.zeros(d, dtype=np.float32)
                try:
                    index.reconstruct(pos, vec)
                    query_eins.append(ein)
                    query_vecs.append(vec)
                except Exception:
                    no_vec_rows.append(row)
                    no_vec += 1
            else:
                no_vec_rows.append(row)
                no_vec += 1

        # Batch FAISS search
        similar_map = {}
        if query_vecs:
            Q = np.array(query_vecs, dtype=np.float32)
            # Normalize
            norms = np.linalg.norm(Q, axis=1, keepdims=True)
            Q = Q / (norms + 1e-10)
            D, I = index.search(Q, SIMILAR_COUNT + 1)
            for qi, (ein, dists, idxs) in enumerate(zip(query_eins, D, I)):
                similar = []
                for dist, idx in zip(dists, idxs):
                    if idx < 0:
                        continue
                    s_ein = ein_map.get(str(idx))
                    if s_ein and s_ein != ein and s_ein in org_dict:
                        s_data = org_to_dict(org_dict[s_ein])
                        s_data['similarity_score'] = float(np.clip(dist, 0, 1))
                        similar.append(s_data)
                        if len(similar) >= SIMILAR_COUNT:
                            break
                similar_map[ein] = similar

        # Write files
        for row in batch:
            ein = row[0]
            org_data = org_to_dict(row)
            org_data['similar_organizations'] = similar_map.get(ein, [])
            _write_org(org_data)

        for row in no_vec_rows:
            org_data = org_to_dict(row)
            org_data['similar_organizations'] = []
            _write_org(org_data)

        processed += len(batch)
        if processed % 100000 == 0 or processed == total:
            print(f"  Processed {processed}/{total} ({processed/total*100:.1f}%)")

    print(f"  Done: {processed} orgs, {no_vec} without vectors")


if __name__ == '__main__':
    main()
