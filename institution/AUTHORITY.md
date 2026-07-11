# Authority Hierarchy

## Document Control

| Field | Value |
|---|---|
| Purpose | Define the order of authority for institutional and agent instructions in this repository. |
| Responsible role | Chief Steward; Stewardship Systems Agent maintains references. |
| Authority level | Interpretive control document subordinate only to `PURPOSE.md`, `COVENANT.md`, and `CONSTITUTION.md`. |
| Review trigger | New governance file, instruction conflict, or proposed autonomy change. |
| Editable status | Editable by ordinary agents for clarity, but may not reduce higher-order protections. |
| Dependencies | `AGENTS.md`, `institution/README.md`, `institution/CONSTITUTION.md`, `institution/GOVERNANCE.md`. |
| Retirement condition | Retire only if replaced by a clearer authority map with the same or stronger protections. |

## Order Of Authority

Higher layers control lower layers. Lower layers may clarify, but may not override.

1. `institution/PURPOSE.md`
2. `institution/COVENANT.md`
3. `institution/CONSTITUTION.md`
4. `STEWARDSHIP.md` and `institution/STEWARDSHIP.md`
5. `institution/GOVERNANCE.md`
6. Operating policies and invariants, including `PRIVACY-INVARIANTS.md`, `DECISIONS.md`, and `LESSONS.md`
7. Current strategy and evidence snapshots, including `institution/CURRENT_STATE.md`, `institution/BUDGET_STATE.md`, `institution/RISK_REGISTER.md`, and `institution/FUNDING_PIPELINE.md`
8. Current priorities and task records, including `institution/state.json` and founder briefs
9. Task-specific instructions and workflow documents
10. Agent implementation choices

## Conflict Handling

- Follow the highest applicable authority source.
- Record unresolved conflicts in `institution/RISK_REGISTER.md`.
- Put founder-required conflicts in `institution/FOUNDER_REQUESTS.md`.
- The mission, covenant, and protected constitutional principles may not self-modify.
