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
