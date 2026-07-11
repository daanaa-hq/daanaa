# Repository State Skill

## Document Control

| Field | Value |
|---|---|
| Purpose | Define the skill that inventories repository state, tests, architecture, and documentation status. |
| Responsible role | Stewardship Systems Agent. |
| Authority level | Skill specification subordinate to `AUTHORITY.md`. |
| Review trigger | Repo structure changes, repeated missed context, or weekly review. |
| Editable status | Editable by ordinary agents with evidence. |
| Dependencies | `institution/CURRENT_STATE.md`, `institution/state.json`, `scripts/institution_weekly_review.py`. |
| Retirement condition | Retire when discovery and state capture become fully covered by a maintained local system. |

## Trigger

New stewardship cycle, major repo change, or material uncertainty about current working state.

## Inputs

- Git status and recent history
- Repository structure
- Current institutional docs
- Safe validation command results

## Permissions

Read repository files, inspect git state, run non-destructive local commands and tests, write institutional outputs only.

## Method

Gather local evidence, distinguish verified facts from unknowns, record validation health, and update `CURRENT_STATE.md` plus `state.json`.

## Output

Current-state snapshot, validation status, repo-risk notes, and confidence levels.

## Tests

Script runs without network access; validation commands succeed or are reported as unavailable.

## Failure Behavior

Mark unavailable evidence as unknown and stop before invasive product edits.

## Cost Awareness

Use local files and existing tests before any external service.

## Human Approval Gates

Required before deployment, spending, destructive actions, or access to non-repo private systems.

## Revision History

- 2026-07-10: Initial minimum skill spec.

## Retirement Condition

Retire when repository discovery is automated with the same or better traceability.
