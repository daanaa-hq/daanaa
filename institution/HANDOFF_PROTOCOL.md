# Claude Code-Codex Handoff Protocol

## Document Control

| Field | Value |
|---|---|
| Purpose | Prevent conflicting work between Claude Code product development and Codex stewardship/quality work. |
| Responsible role | Product Engineering Steward and Stewardship Systems Agent. |
| Authority level | Operating protocol subordinate to `CONSTITUTION.md`, `AUTHORITY.md`, and founder approval policies. |
| Review trigger | Parallel-work conflict, merge confusion, recurring rework, or weekly review. |
| Editable status | Editable by ordinary agents if protections and task traceability are preserved. |
| Dependencies | `AGENTS.md`, `CLAUDE.md`, `institution/AUTHORITY.md`, `institution/tasks/`. |
| Retirement condition | Retire only if replaced by a simpler authenticated coordination system that lives in the repository. |

## Roles

- Codex owns institutional state, stewardship review, operating-loop automation, founder briefs, quality review, and cross-cutting risk documentation.
- Claude Code remains the active product-development system unless a task record assigns product work to Codex.

## Branch And Worktree Naming

- Codex stewardship branches: `stewardship/<topic>` or `stewardship-system-bootstrap`.
- Claude Code product branches: `claude/<topic>`.
- Shared review branches: `review/<topic>`.
- If a separate worktree is used, name it to match the branch.

## Task Records

- Every active cross-agent task lives in `institution/tasks/`.
- One task file per task, named `T-YYYY-MM-DD-###-short-name.md`.
- Required fields: owner, scope, affected paths, authority constraints, status, validation plan, handoff target, merge notes.

## Proposed Product Changes

- Stewardship requirements for product work must be written in the task record.
- Product change proposals must identify affected files, user value, protected-principle checks, and required tests.
- If a change touches ranking, privacy, donations, claims, public trust signals, or payments, Codex must attach a stewardship review before merge.

## Implementation Notes

- Claude Code records implementation notes, tradeoffs, and test results directly in the task record or `DECISIONS.md` when durable.
- Codex records review findings, risks, and merge readiness in the same task record or `DECISION_LOG.md`.

## Review And Merge

- Codex reviews product branches for stewardship, validation quality, and conflict with protected rules.
- Approved changes are merged only after task status is `ready-to-merge` and validations listed in the task record have passed.
- If work is unfinished, the task record must state what remains, what is blocked, and who owns the next action.

## Conflict Escalation

- If two agents need the same file, prefer the task owner already assigned.
- If overlap is unavoidable, add a conflict note in the task record and narrow scope before editing.
- If authority is unclear, follow the higher-order source in `AUTHORITY.md` and record the conflict in `RISK_REGISTER.md`.

## Decision Storage

- Material decisions go to `institution/DECISION_LOG.md`.
- Task-local implementation choices stay in the task record unless they affect wider policy or repeated practice.

## Startup Protocol

Before reading chat or editing files, open `institution/handoffs/STARTUP_PROTOCOL.md` and use it as the first shared checkpoint for both Claude and Codex.

## Reusable Claude Script

Use this as the standard Claude prompt when Codex will review the work:

```text
You are working inside the Daanaa Claude-Code/Codex mandate.

Before you change anything:
1. Read the governing files and the task record first.
2. Restate the goal, owner, scope, affected paths, and authority gates.
3. List unknowns and assumptions. If a fact is missing or load-bearing, stop and ask.
4. Write a short plan with exact files, tests, and rollback/no-op path.
5. Make only the minimum changes needed for the task.
6. Run the relevant tests or smoke checks and report exact commands and results.
7. Update the task record with implementation notes, validation, and any open gaps.
8. Handoff to Codex with changed files, why they changed, what was tested, and what remains uncertain.

Rules:
- Do not touch public claims, pricing, privacy, payments, auth, methodology, or deployment without explicit founder approval.
- If another agent may be touching the same files, record the conflict in the task record before editing.
- Do not optimize for speed over traceability; optimize for no rework.
- Use Codex as the verification partner, not as a substitute for missing evidence.
```

## Handoff Packet Generator

Generate a Codex-ready packet from any task record with:

```bash
python3 scripts/task_handoff_packet.py institution/tasks/<task>.md --out /tmp/CODEX_HANDOFF.md --check
```

The packet flags mismatches between declared pass criteria and the evidence actually present in the task record. Use it before handoff so Codex reviews one artifact instead of reconstructing the state manually.

## Reusable Codex Review Script

Use this as the standard Codex review pass for Claude-delivered work:

```text
You are reviewing a Claude implementation under the Daanaa mandate.

1. Read the task record, the diff, and the relevant governing files.
2. Confirm the change matches the task scope and authority boundaries.
3. Check whether the implementation introduced unsupported assumptions, hidden coupling, or public-claim risk.
4. Verify the tests or smoke checks are sufficient for the risk level.
5. Call out any missing evidence, incomplete rollback path, or unresolved conflict.
6. Approve only when the task record, diff, and validation all line up.

Report back with:
- findings first, ordered by severity
- exact file references
- any residual risks or missing tests
- whether the task is ready to merge or needs another pass
```
