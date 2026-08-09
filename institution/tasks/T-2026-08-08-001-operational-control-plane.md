# T-2026-08-08-001 — Operational control plane

| Field | Value |
|---|---|
| Owner | Codex (operations and review); Claude Code (backend changes) |
| Scope | Read-only preflight, search performance evidence, backup storage visibility, and agent handoff discipline |
| Affected paths | `scripts/operational_preflight.py`, `scripts/audit_backup_storage.py`, `docs/OPERATIONAL_CONTROL_PLANE.md` |
| Authority constraints | No production mutation, deployment, service restart, backup deletion, or retention change from this task |
| Status | in_progress |
| Validation | Python compile; disposable/local preflight; search benchmark output; review of concurrent backend diff |
| Handoff target | Founder review, then Claude Code backend task records |
| Merge notes | Keep operational controls separate from backend/API implementation files |

## Objective

Create a small, evidence-first operating layer so Codex and Claude Code can work in parallel without making unsupported production claims or duplicating work.

## Gates

- Read-only by default.
- A failing check stops the claim of readiness; it does not trigger an automatic repair.
- Search performance is reported with p50/p95 and query-level results.
- Backup storage is audited without deletion or pruning.
- Production deployment remains a separate, explicitly approved task.

## Open follow-up

- Add CI wiring only after the local commands are reviewed.
- Add a skill registry entry after the first two manual runs prove the workflow is useful.
- Review Claude Code changes through the task record and exact diff before merge.
