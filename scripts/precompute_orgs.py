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

DB_PATH = os.environ.get("MERIT_DB_PATH", "data/merit_registry.db")
_OUT = os.environ.get("PRECOMPUTE_OUT", "precompute_output")
FAISS_INDEX_PATH = os.path.join(_OUT, "faiss_index.bin")
EIN_MAP_PATH = os.path.join(_OUT, "ein_map.json.gz")
OUTPUT_DIR = os.path.join(_OUT, "orgs")
SIMILAR_COUNT = 12
BATCH_SIZE = 10000   # Process N orgs per FAISS batch search


def org_to_dict(row):
    return {
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
        'address': row[11],
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
        'donate_url': row[37],
        'donate_platform': row[38],
        'donate_url_status': row[39],
        'activ1': row[40],
        'activ2': row[41],
        'activ3': row[42],
    }


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] Pre-computing org detail pages...")

    # Load all org data from DB
    print("  Loading org data...")
    cursor.execute("""
        SELECT
            EIN, organization_name, NTEE1, NTEECC, CITY, STATE,
            total_revenue, ntee1_percentile, ntee1_total_orgs, source,
            zipcode, NULL as address, revenue_band, peer_percentile, peer_rank, peer_total, peer_group,
            latest_tax_year, data_source, updated_at, merit_tier, merit_score,
            merit_band, financial_health, months_of_reserve, net_assets,
            total_expenses, total_liabilities, employee_count, program_expense_pct,
            ruling_date, NULL as nccs_year, mission, mission_source, website, website_status,
            cause_tags, donate_url, donate_platform, donate_url_status,
            NULL as activ1, NULL as activ2, NULL as activ3
        FROM registry_enriched
        -- Only generate pages for orgs where donating is currently tax-deductible:
        -- deductible 501(c)(3) AND not IRS-revoked. Fail closed on revocation.
        WHERE EIN IS NOT NULL AND deductibility = 1 AND org_status = 'active'
        ORDER BY EIN
    """)
    all_rows = cursor.fetchall()
    org_dict = {row[0]: row for row in all_rows}
    total_orgs = len(all_rows)
    print(f"  Loaded {total_orgs} tax-deductible orgs")
    conn.close()

    # Check existing files
    existing = {f.stem for f in Path(OUTPUT_DIR).rglob('*.json.gz')}
    print(f"  Existing files: {len(existing)}")

    orgs_to_process = [row for row in all_rows if row[0] not in existing]
    print(f"  To process: {len(orgs_to_process)}")

    if not orgs_to_process:
        print("  All orgs already processed!")
        return

    # Load FAISS index + EIN map for similar orgs
    faiss_ok = False
    index = None
    ein_map = None

    if HAS_FAISS and Path(FAISS_INDEX_PATH).exists() and Path(EIN_MAP_PATH).exists():
        print("  Loading FAISS index...")
        try:
            index = faiss.read_index(FAISS_INDEX_PATH)
            index.nprobe = 32
            # IVFPQ/IVFFlat need a direct map for reconstruct() (used to fetch each
            # org's own vector). Without this, the quantized index falls back to
            # empty similar_orgs. Harmless if already present.
            try:
                index.make_direct_map()
            except Exception:
                pass
            with gzip.open(EIN_MAP_PATH, 'rt') as f:
                ein_map = json.load(f)  # {str(idx): ein}
            # Build position lookup: ein → faiss position
            ein_to_pos = {ein: int(i) for i, ein in ein_map.items()}
            faiss_ok = True
            print(f"  FAISS ready: {index.ntotal} vectors")

            # Try reconstruct to verify
            try:
                test_vec = np.zeros(1024, dtype=np.float32)
                index.reconstruct(0, test_vec)
                print("  Vector reconstruction: supported")
            except Exception:
                # IVFFlat without store_pairs — reconstruct not available
                print("  Vector reconstruction: not supported, will use batch queries")
                faiss_ok = False
        except Exception as e:
            print(f"  FAISS load error: {e}")

    processed = 0
    no_similar = 0

    if faiss_ok:
        # Reconstruct-based: get each org's vector from FAISS
        _process_with_reconstruction(orgs_to_process, org_dict, index, ein_map, ein_to_pos)
    else:
        # No reconstruction: write org files with empty similar_orgs
        # (still correct — all org data present, similar_orgs = [])
        print("  Writing org files without similar orgs (FAISS reconstruct unavailable)")
        _process_without_similar(orgs_to_process, org_dict, existing, total_orgs)

    total_files = len(list(Path(OUTPUT_DIR).rglob('*.json.gz')))
    print(f"\n[{datetime.now().isoformat()}] Done! Total org files: {total_files}")
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
