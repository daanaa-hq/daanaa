#!/usr/bin/env python3
"""
Fast org detail precompute: extract org data from browse files.
Uses FAISS GPU batch search for similar orgs.
Resumes from existing files.
"""
import gzip
import json
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

BROWSE_DIR = Path("precompute_output/browse")
OUTPUT_DIR = Path("precompute_output/orgs")
FAISS_INDEX_PATH = "precompute_output/faiss_index_dm.bin"  # DirectMap-enabled index
EIN_MAP_PATH = "precompute_output/ein_map.json.gz"
SIMILAR_COUNT = 12
BATCH_SIZE = 5000


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] Building org detail files from browse data...")

    # Check existing files
    existing_eins = {f.stem for f in OUTPUT_DIR.rglob('*.json.gz')}
    print(f"  Existing org files: {len(existing_eins)}")

    # Collect all orgs from browse files
    print("  Scanning browse files...")
    all_orgs = {}  # ein → org_dict
    for browse_file in sorted(BROWSE_DIR.rglob('*.json.gz')):
        try:
            with gzip.open(browse_file, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            for org in data.get('organizations', []):
                ein = org.get('EIN')
                if ein and ein not in all_orgs:
                    all_orgs[ein] = org
        except Exception as e:
            pass

    print(f"  Found {len(all_orgs)} unique orgs in browse files")

    # Filter to unprocessed
    to_process = {ein: org for ein, org in all_orgs.items() if ein not in existing_eins}
    print(f"  Need to process: {len(to_process)}")

    if not to_process:
        print("  All orgs already have detail files!")
        return

    # Load FAISS for similar orgs
    faiss_index = None
    ein_map = None
    ein_to_pos = None
    can_reconstruct = False

    if HAS_FAISS and Path(FAISS_INDEX_PATH).exists():
        print("  Loading FAISS index...")
        try:
            faiss_index = faiss.read_index(FAISS_INDEX_PATH)
            faiss_index.nprobe = 32
            with gzip.open(EIN_MAP_PATH, 'rt') as f:
                ein_map = json.load(f)
            ein_to_pos = {ein: int(i) for i, ein in ein_map.items()}
            print(f"  FAISS: {faiss_index.ntotal} vectors")

            # Test reconstruct
            test = np.zeros(1024, dtype=np.float32)
            faiss_index.reconstruct(0, test)
            can_reconstruct = True
            print("  Reconstruct: SUPPORTED — will compute similar orgs via GPU")
        except Exception as e:
            print(f"  Reconstruct: not available ({e}) — similar_orgs will be empty for new files")

    # Try GPU
    if can_reconstruct and HAS_FAISS:
        try:
            res = faiss.StandardGpuResources()
            faiss_index = faiss.index_cpu_to_gpu(res, 0, faiss_index)
            print("  GPU acceleration: ACTIVE")
        except Exception as e:
            print(f"  GPU not available: {e}")

    # Process in batches
    eins = list(to_process.keys())
    total = len(eins)
    processed = 0

    for batch_start in range(0, total, BATCH_SIZE):
        batch_eins = eins[batch_start:batch_start + BATCH_SIZE]
        similar_map = {}

        if can_reconstruct and faiss_index is not None:
            # Build query matrix
            query_eins = []
            query_vecs = []

            for ein in batch_eins:
                pos = ein_to_pos.get(ein)
                if pos is not None:
                    try:
                        vec = np.zeros(1024, dtype=np.float32)
                        if hasattr(faiss_index, 'index'):  # GPU index wrapper
                            faiss_index.index.reconstruct(pos, vec)
                        else:
                            faiss_index.reconstruct(pos, vec)
                        query_eins.append(ein)
                        query_vecs.append(vec)
                    except Exception:
                        pass

            if query_vecs:
                Q = np.array(query_vecs, dtype=np.float32)
                norms = np.linalg.norm(Q, axis=1, keepdims=True)
                Q = Q / (norms + 1e-10)
                D, I = faiss_index.search(Q, SIMILAR_COUNT + 1)

                for qi, (ein, dists, idxs) in enumerate(zip(query_eins, D, I)):
                    similar = []
                    for dist, idx in zip(dists, idxs):
                        if idx < 0:
                            continue
                        s_ein = ein_map.get(str(idx))
                        if s_ein and s_ein != ein and s_ein in all_orgs:
                            s_data = dict(all_orgs[s_ein])
                            s_data['similarity_score'] = float(np.clip(dist, 0, 1))
                            similar.append(s_data)
                            if len(similar) >= SIMILAR_COUNT:
                                break
                    similar_map[ein] = similar

        # Write files
        for ein in batch_eins:
            org_data = dict(to_process[ein])
            org_data['similar_organizations'] = similar_map.get(ein, [])
            ein_prefix = ein[:3]
            out_dir = OUTPUT_DIR / ein_prefix
            out_dir.mkdir(parents=True, exist_ok=True)
            filepath = out_dir / f"{ein}.json.gz"
            with gzip.open(filepath, 'wt', encoding='utf-8', compresslevel=1) as f:
                json.dump(org_data, f, separators=(',', ':'))

        processed += len(batch_eins)
        if processed % 50000 == 0 or processed == total:
            pct = processed / total * 100
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] {processed}/{total} ({pct:.1f}%)")

    total_files = len(list(OUTPUT_DIR.rglob('*.json.gz')))
    print(f"\n[{datetime.now().isoformat()}] Done!")
    print(f"  New files: {processed}")
    print(f"  Total org files: {total_files}")
    total_size = sum(f.stat().st_size for f in OUTPUT_DIR.rglob('*') if f.is_file())
    print(f"  Disk: {total_size / 1024 / 1024:.0f} MB")


if __name__ == '__main__':
    main()
