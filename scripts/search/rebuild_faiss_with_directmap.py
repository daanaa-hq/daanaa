#!/usr/bin/env python3
"""
Extract vectors from existing IVFFlat index (via inverted lists),
rebuild with DirectMap so precompute_orgs can reconstruct vectors.
No re-embedding needed — extracts from the IVF invlists directly.
"""
import numpy as np
import json
import gzip
from pathlib import Path
from datetime import datetime
import sys

try:
    import faiss
except ImportError:
    print("ERROR: faiss not installed")
    sys.exit(1)

SRC_INDEX = "precompute_output/faiss_index.bin"
DST_INDEX = "precompute_output/faiss_index_dm.bin"
EIN_MAP_PATH = "precompute_output/ein_map.json.gz"


def main():
    print(f"[{datetime.now().isoformat()}] Rebuilding FAISS index with DirectMap...")

    print("  Loading source index...")
    src = faiss.read_index(SRC_INDEX)
    d = src.d
    nlist = src.nlist
    total = src.ntotal
    print(f"  Source: {total} vectors, d={d}, nlist={nlist}")

    # Extract all vectors + their FAISS IDs from inverted lists
    print("  Extracting vectors from inverted lists...")
    all_vecs = np.zeros((total, d), dtype=np.float32)
    all_ids = np.zeros(total, dtype=np.int64)

    pos = 0
    for il_idx in range(nlist):
        list_size = src.invlists.list_size(il_idx)
        if list_size == 0:
            continue

        # IndexIVFFlat stores raw float32: code_size = d * 4 bytes per vector
        codes_ptr = src.invlists.get_codes(il_idx)
        nbytes = list_size * src.code_size  # code_size = d * sizeof(float) = d*4
        codes_bytes = faiss.rev_swig_ptr(codes_ptr, nbytes)  # uint8 array
        codes = codes_bytes.view(np.float32).reshape(list_size, d).copy()

        ids_ptr = src.invlists.get_ids(il_idx)
        ids = faiss.rev_swig_ptr(ids_ptr, list_size).copy()

        all_vecs[pos:pos + list_size] = codes
        all_ids[pos:pos + list_size] = ids
        pos += list_size

        if (il_idx + 1) % 100 == 0:
            print(f"  Extracted {pos}/{total} vectors ({il_idx+1}/{nlist} lists)...")

    print(f"  Extracted {pos} vectors from {nlist} inverted lists")

    # Sort by FAISS sequential ID (0..N-1) so reconstruct(i) returns vector i
    print("  Sorting by FAISS ID...")
    order = np.argsort(all_ids)
    all_vecs = all_vecs[order]
    all_ids = all_ids[order]

    # Build new IVFFlat index with DirectMap
    print("  Building new index with DirectMap...")
    quantizer = faiss.IndexFlatIP(d)
    new_index = faiss.IndexIVFFlat(quantizer, d, nlist, faiss.METRIC_INNER_PRODUCT)
    new_index.set_direct_map_type(faiss.DirectMap.Array)

    # Use GPU for training if available
    res = None
    try:
        res = faiss.StandardGpuResources()
        gpu_q = faiss.index_cpu_to_gpu(res, 0, quantizer)
        print("  GPU available — training quantizer on GPU...")
        # Train using sampled vectors
        sample_size = min(256000, total)
        sample_idx = np.random.choice(total, sample_size, replace=False)
        gpu_q.train(all_vecs[sample_idx])
        # Copy centroids back to CPU quantizer
        faiss.copy_index_ivf_to_cpu(gpu_q, quantizer) if hasattr(faiss, 'copy_index_ivf_to_cpu') else None
        print("  GPU training done")
    except Exception as e:
        print(f"  GPU not available ({e}), using CPU...")
        new_index.train(all_vecs[:min(256000, total)])

    # DirectMap.Array requires sequential add() — not add_with_ids()
    # Vectors are already sorted by FAISS ID (0..N-1) so position == ID
    print(f"  Adding {total} vectors (sequential, no explicit IDs)...")
    batch = 100000
    for i in range(0, total, batch):
        new_index.add(all_vecs[i:i + batch])
        if (i // batch + 1) % 5 == 0:
            print(f"    Added {min(i+batch, total)}/{total} vectors")

    new_index.nprobe = 32
    print(f"  New index: {new_index.ntotal} vectors")

    # Verify reconstruction works
    print("  Verifying reconstruction...")
    test_vec = np.zeros(d, dtype=np.float32)
    new_index.reconstruct(0, test_vec)
    print(f"  Reconstruction OK — norm={np.linalg.norm(test_vec):.4f}")

    # Save
    print(f"  Saving to {DST_INDEX}...")
    faiss.write_index(new_index, DST_INDEX)
    size_mb = Path(DST_INDEX).stat().st_size / 1024 / 1024
    print(f"  Saved: {size_mb:.0f}MB")

    print(f"\n[{datetime.now().isoformat()}] Done! New index supports reconstruction.")
    print(f"  Next: rename {DST_INDEX} → {SRC_INDEX} and run precompute_orgs.py")


if __name__ == '__main__':
    main()
