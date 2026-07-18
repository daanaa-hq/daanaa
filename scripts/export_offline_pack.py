#!/usr/bin/env python3
"""
export_offline_pack.py — build the offline directory pack the app downloads.

The pack is the entire active 501(c)(3) directory slimmed to search-index
fields, sharded so phones can download and update it incrementally:

  offline_pack/
    manifest.json          version, row count, shard list with sha256 + bytes
    shard_00.json.gz ...   compact rows: [ein, name, city, state, ntee1, donate]

Rows are sharded by EIN's last two digits mod SHARDS, so an org stays in the
same shard across rebuilds — a delta update only re-downloads shards whose
sha256 changed in the manifest. Donors get updates within a day of new data
for the bandwidth cost of the changed slices only.

Privacy note (P2): this enables fully on-device search — what a donor
searches for never reaches a server.

Usage:
  python3 scripts/export_offline_pack.py                # full build
  python3 scripts/export_offline_pack.py --out DIR      # custom output dir
  python3 scripts/export_offline_pack.py --limit 50000  # smoke test build
"""

import argparse
import gzip
import hashlib
import json
import sqlite3
import sys
import time
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "data" / "merit_registry.db"
DEFAULT_OUT = BASE / "precompute_output" / "offline_pack"
SHARDS = 64

QUERY = """
SELECT EIN, organization_name, city, state, ntee1,
       CASE WHEN donate_url IS NOT NULL AND donate_url != ''
                 AND donate_url_status IN ('beta','claimed') THEN 1 ELSE 0 END
FROM registry_enriched
WHERE organization_name IS NOT NULL AND organization_name != ''
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--limit", type=int, default=0, help="cap rows (smoke test)")
    args = ap.parse_args()

    t0 = time.time()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=60)
    conn.execute("PRAGMA query_only=1")

    shards: list[list[list]] = [[] for _ in range(SHARDS)]
    q = QUERY + (f" LIMIT {args.limit}" if args.limit else "")
    rows = 0
    for ein, name, city, state, ntee1, donate in conn.execute(q):
        # Compact row — field order is the schema (documented in manifest)
        try:
            shard_idx = int(str(ein)[-2:]) % SHARDS
        except ValueError:
            shard_idx = 0
        shards[shard_idx].append([ein, name, city or "", state or "", ntee1 or "", donate])
        rows += 1
    conn.close()

    manifest_shards = []
    total_bytes = 0
    for i, shard in enumerate(shards):
        # Stable order within a shard → stable bytes → stable sha256 when
        # nothing changed, which is what makes delta updates work.
        shard.sort(key=lambda r: r[0])
        payload = json.dumps(shard, ensure_ascii=False, separators=(",", ":")).encode()
        blob = gzip.compress(payload, 9)
        name = f"shard_{i:02d}.json.gz"
        (out / name).write_bytes(blob)
        total_bytes += len(blob)
        manifest_shards.append({
            "file": name,
            "rows": len(shard),
            "bytes": len(blob),
            "sha256": hashlib.sha256(blob).hexdigest(),
        })

    manifest = {
        "version": f"{date.today().isoformat()}-{rows}",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "schema": ["ein", "name", "city", "state", "ntee1", "has_donate_link"],
        "rows": rows,
        "total_bytes": total_bytes,
        "shards": manifest_shards,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))

    print(f"offline pack: {rows:,} orgs → {SHARDS} shards, "
          f"{total_bytes / 1048576:.1f} MB total, {time.time() - t0:.0f}s → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
