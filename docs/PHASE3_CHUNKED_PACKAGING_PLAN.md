# Phase 3 Chunked Packaging and Validation Plan

Status: local remediation only; no live deployment is authorized by this document.

## Finding

The existing `precompute_output/orgs` directory is not a clean production artifact
tree. A read-only scan found both stale flat JSON files and nested `.json.gz`
files. Those sets must not be combined when checking deployment completeness.

The current tree therefore fails the layout gate and must not be packaged.

## Safe sequence

1. Rebuild into an empty `.deploy_scratch/precompute` directory using the committed
   production builder. Do not reuse `precompute_output`.
2. Validate the nested layout, file count, IRS field presence, and status counts.
3. Generate a path-and-size manifest. Hashes are optional for local inventory and
   required for each transfer unit.
4. Package organization prefixes into bounded, resumable shard archives. Use
   32–64 shards by default; 1,000 tiny archives adds operational overhead without
   solving the completeness problem.
5. Write each archive to a temporary name, then atomically rename it and write a
   sidecar SHA-256 file.
6. On the destination, verify every sidecar checksum and expected member count,
   extract into a new staging directory, validate the extracted tree, and only
   then perform an atomic directory swap.
7. Keep non-organization assets (browse data, content, maps, and indexes) in
   separate small transfer units with their own manifests.

## Hard stop conditions

- Any flat files, symlinks, unexpected prefixes, or unexpected extensions.
- Any count mismatch between the clean builder output and the authoritative
  database query.
- Any missing IRS fields or status-count mismatch.
- Any checksum, member-count, or post-extraction validation failure.
- Any live performance degradation during packaging or transfer.

Do not run `fio` against the live application disk. Use read-only observations
such as `iostat`, `vmstat`, `pidstat`, and directory timing first; reserve write
benchmarks for an isolated maintenance window or a disposable volume.

## Local validation commands

```bash
python3 -m py_compile scripts/phase3_artifact_tools.py
python3 scripts/phase3_artifact_tools.py validate-org-layout \
  --root .deploy_scratch/precompute \
  --expected-count 1758078
python3 scripts/phase3_artifact_tools.py inventory \
  --root .deploy_scratch/precompute \
  --output .deploy_scratch/precompute.manifest.json
```

The expected count must be confirmed from the clean builder/database run before
it is treated as authoritative. No `--ship-only` or production promotion should
run until all gates pass and QA signs off.
