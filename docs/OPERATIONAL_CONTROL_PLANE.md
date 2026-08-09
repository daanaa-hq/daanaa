# Operational Control Plane

This is the lightweight operating loop for parallel Codex and Claude Code work.

## Ownership

- Claude Code: backend/product implementation and backend tests.
- Codex: operational controls, stewardship review, evidence quality, backup visibility, and cross-cutting verification.
- Founder: production mutation, destructive infrastructure actions, spending, retention changes, and final release approval.

## One-command local preflight

```bash
python3 scripts/operational_preflight.py --json
```

The command is read-only. It checks:

- database existence and SQLite quick-check;
- required `registry_enriched` and `org_fts` tables;
- registry and FTS row counts;
- free disk space;
- API health;
- search response latency across representative queries.

Run a full integrity check separately when needed:

```bash
python3 scripts/operational_preflight.py --full-integrity --iterations 10
```

## Backup visibility

```bash
python3 scripts/audit_backup_storage.py --root /home/akbar/meritgiving --json
```

This is an inventory only. It never deletes, moves, compresses, or prunes backups.

## Evidence rules

Every readiness report must distinguish:

```text
tested locally
tested on a disposable copy
read-only production verified
production mutation executed
```

Search claims must include query names, iteration count, p50, p95, and failure count. A single average is not a release gate.

## Parallel-work rule

Before editing, each agent records owner, scope, affected paths, authority constraints, validation, and handoff target in `institution/tasks/`. Operational work should not edit backend implementation files owned by Claude Code.

## Suggested cadence

1. Run local preflight before a backend task.
2. Run it again after the task and attach JSON output to the task record.
3. Run backup storage audit weekly or after a large artifact build.
4. Review search p95 and disk free space before any deployment approval.
